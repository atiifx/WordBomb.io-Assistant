import time
import threading
import customtkinter as ctk
from PIL import ImageGrab, ImageOps
import win32gui
import os
import sys

class RegionSelector(ctk.CTkToplevel):
    def __init__(self, callback, title_text="Alanı Seçin"):
        super().__init__()
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None

        self.attributes("-alpha", 0.35)
        self.attributes("-topmost", True)
        self.attributes("-fullscreen", True)
        self.config(cursor="cross")

        self.canvas = ctk.CTkCanvas(self, cursor="cross", bg="#101828")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text=f"Lütfen {title_text} alanını fare ile basılı tutarak çizin",
            fill="white",
            font=("Segoe UI", 16, "bold")
        )

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline="#22C55E", width=2)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        right = max(self.start_x, end_x)
        bottom = max(self.start_y, end_y)

        self.destroy()

        if right - left > 5 and bottom - top > 5:
            self.callback((left, top, right, bottom))


class AutoGameScanner:
    def __init__(self, on_turn_detected_callback):
        self.running = False
        self.on_turn_detected = on_turn_detected_callback

        self.auto_mode_enabled = False
        self.solo_mode = False

        self.last_detected_hece = ""
        self.already_typed_in_turn = False

        self.hece_box = (880, 70, 1040, 150)
        self.turn_box = None

        self.reader = None
        self.is_reader_ready = False

        # EasyOCR'ı arka planda yükle (Arayüz anında açılsın)
        threading.Thread(target=self._init_ocr_engine, daemon=True).start()

    def _init_ocr_engine(self):
        """EasyOCR motorunu arka planda sessizce yükler."""
        try:
            import easyocr
            # Terminale 'Using CPU...' yazmasını engellemek için verbose=False
            self.reader = easyocr.Reader(['en', 'tr'], gpu=False, verbose=False)
            self.is_reader_ready = True
        except Exception:
            pass

    def start(self):
        if self.running:
            return
        self.running = True
        self.already_typed_in_turn = False
        self.last_detected_hece = ""
        threading.Thread(target=self._scan_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def set_hece_box(self, bbox):
        self.hece_box = bbox

    def set_turn_box(self, bbox):
        self.turn_box = bbox
        self.already_typed_in_turn = False

    def _is_my_turn_selected_region(self):
        if not self.turn_box or not self.is_reader_ready:
            return False

        try:
            import numpy as np

            screenshot = ImageGrab.grab(bbox=self.turn_box)
            img_np = np.array(screenshot)

            lower_purple = np.array([60, 70, 190])
            upper_purple = np.array([120, 130, 255])

            lower_white = np.array([220, 220, 220])
            upper_white = np.array([255, 255, 255])

            purple_mask = (img_np >= lower_purple) & (img_np <= upper_purple)
            white_mask = (img_np >= lower_white) & (img_np <= upper_white)

            purple_pixels = np.sum(purple_mask)
            white_pixels = np.sum(white_mask)

            if purple_pixels < 50 or white_pixels < 25:
                return False

            results = self.reader.readtext(img_np, detail=0)
            text_found = " ".join(results).upper()

            valid_keywords = ["YOUR", "TURN", "SIRA", "SENDE", "YOURTURN", "SIRASENDE"]
            return any(keyword in text_found for keyword in valid_keywords)

        except Exception:
            return False

    def _read_hece(self):
        """Çift okuma (UCYC gibi parazit) korumalı, tam otonom hece okuyucu"""
        if not self.is_reader_ready:
            return ""

        try:
            import numpy as np
            from PIL import ImageOps

            screenshot = ImageGrab.grab(bbox=self.hece_box)
            w, h = screenshot.size

            # Büyütme ve Yumuşatılmış Netleştirme
            resized = screenshot.resize((int(w * 2.5), int(h * 2.5)))
            gray = ImageOps.grayscale(resized)
            
            # Gürültüyü engelleyen dengeli eşikleme
            thresholded = gray.point(lambda p: 255 if p > 130 else 0)
            padded = ImageOps.expand(thresholded, border=12, fill=0)

            img_np = np.array(padded.convert("RGB"))
            img_h, img_w, _ = img_np.shape

            results = self.reader.readtext(
                img_np,
                detail=1,
                allowlist="ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZXWQ-'"
            )

            if not results:
                return ""

            valid_blocks = []

            for bbox, text, confidence in results:
                clean_blk = "".join(c for c in text if c.isalpha() or c == "-").strip().upper()
                if confidence > 0.12 and clean_blk:
                    min_x = min(pt[0] for pt in bbox)
                    max_x = max(pt[0] for pt in bbox)
                    min_y = min(pt[1] for pt in bbox)
                    max_y = max(pt[1] for pt in bbox)

                    # Sağ alt köşedeki skoru/sayıları ve çerçeve artıklarını FILTRELE
                    if (min_x > img_w * 0.58) and (min_y > img_h * 0.52):
                        continue

                    valid_blocks.append({
                        'x': min_x,
                        'text': clean_blk,
                        'width': max_x - min_x,
                        'area': (max_x - min_x) * (max_y - min_y)
                    })

            if not valid_blocks:
                return ""

            # Alanı (Area) veya genişliği en büyük olan ANA HECE'yi seç
            main_block = max(valid_blocks, key=lambda b: b['area'])
            clean_text = main_block['text']

            if not clean_text:
                return ""

            # 1. AŞAMA: OCR Tireyi Metin Olarak Doğrudan Yakaladıysa
            if clean_text.startswith("-"):
                return " " + clean_text.replace("-", "").strip()
            elif clean_text.endswith("-"):
                return clean_text.replace("-", "").strip() + " "

            pure_letters = "".join(c for c in clean_text if c.isalpha())

            # 2. AŞAMA: OCR Tireyi Kaçırdıysa (Ağırlık Merkezi ve Şekil Analizi)
            if len(pure_letters) == 1:
                char_center_x = main_block['x'] + (main_block['width'] / 2.0)

                if pure_letters in ["I", "1"]:
                    if char_center_x >= (img_w * 0.48):
                        return " " + pure_letters
                    else:
                        return pure_letters + " "

                if char_center_x > (img_w * 0.50):
                    return " " + pure_letters
                else:
                    return pure_letters + " "

            elif len(pure_letters) == 2:
                box_x_min = main_block['x']
                box_x_max = main_block['x'] + main_block['width']

                gap = 4
                stripe_width = 28

                left_start = max(0, int(box_x_min - gap - stripe_width))
                left_end = max(0, int(box_x_min - gap))
                
                right_start = min(img_w, int(box_x_max + gap))
                right_end = min(img_w, int(box_x_max + gap + stripe_width))

                left_stripe = img_np[:, left_start:left_end]
                right_stripe = img_np[:, right_start:right_end]

                def has_dash_shape(stripe):
                    if stripe.size == 0:
                        return False
                    gray_stripe = np.mean(stripe, axis=2) if stripe.ndim == 3 else stripe
                    mask = gray_stripe > 135
                    if not np.any(mask):
                        return False
                    y_indices, x_indices = np.where(mask)
                    if len(x_indices) < 5:
                        return False
                    dash_w = np.max(x_indices) - np.min(x_indices) + 1
                    dash_h = np.max(y_indices) - np.min(y_indices) + 1
                    stripe_h = stripe.shape[0]
                    avg_y = np.mean(y_indices)
                    is_centered_y = (stripe_h * 0.20) <= avg_y <= (stripe_h * 0.80)
                    return (dash_w / max(1, dash_h)) >= 1.4 and dash_w >= 5 and is_centered_y

                has_left_dash = has_dash_shape(left_stripe)
                has_right_dash = has_dash_shape(right_stripe)

                if has_left_dash and not has_right_dash:
                    return " " + pure_letters
                elif has_right_dash and not has_left_dash:
                    return pure_letters + " "
                else:
                    return pure_letters

            return pure_letters[:4]

        except Exception:
            return ""

    def _is_game_window_active(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd).lower()

            allowed_targets = ["chrome", "discord", "wordbomb", "edge", "opera", "brave"]
            return any(target in window_title for target in allowed_targets)
        except Exception:
            return True

    def _scan_loop(self):
        pending_hece = ""
        pending_count = 0

        while self.running:
            if not self.auto_mode_enabled or not self.is_reader_ready:
                time.sleep(0.2)
                continue

            try:
                if not self._is_game_window_active():
                    time.sleep(0.4)
                    continue

                # 1. SOLO MOD
                if self.solo_mode:
                    detected = self._read_hece()

                    if detected and len(detected) >= 1:
                        if detected != self.last_detected_hece:
                            if detected == pending_hece:
                                pending_count += 1
                            else:
                                pending_hece = detected
                                pending_count = 1

                            if pending_count >= 2:
                                self.last_detected_hece = detected
                                pending_hece = ""
                                pending_count = 0

                                if hasattr(self, 'writer_ref') and self.writer_ref:
                                    self.writer_ref.request_stop()

                                self.on_turn_detected(detected)
                        else:
                            pending_hece = ""
                            pending_count = 0

                    time.sleep(0.06)
                    continue

                # 2. MULTI MOD
                turn_active = self._is_my_turn_selected_region()

                if turn_active:
                    if not self.already_typed_in_turn:
                        detected = self._read_hece()

                        if detected and len(detected) >= 1:
                            if detected == pending_hece:
                                pending_count += 1
                            else:
                                pending_hece = detected
                                pending_count = 1

                            if pending_count >= 2:
                                self.already_typed_in_turn = True
                                self.last_detected_hece = detected
                                pending_hece = ""
                                pending_count = 0
                                self.on_turn_detected(detected)
                else:
                    if self.already_typed_in_turn:
                        self.already_typed_in_turn = False
                    pending_hece = ""
                    pending_count = 0

            except Exception:
                pass

            time.sleep(0.06)