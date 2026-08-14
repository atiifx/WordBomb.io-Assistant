import os
import sys
import warnings

# --- TÜM LOG VE UYARILARI SUSTUR (C++ & Python Seviyesi) ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['TORCH_CPP_LOG_LEVEL'] = 'ERROR'
warnings.filterwarnings("ignore")

import customtkinter as ctk
import threading
import webbrowser
import zipfile
import requests
import subprocess
import ctypes
from core.dictionary import DictionaryManager
from core.writer import HumanoidWriter
from core.stealth import StealthEngine
from core.scanner import AutoGameScanner, RegionSelector
from core.security import SecurityManager, LICENSE_FILE, CLIENT_VERSION
from utils.helpers import focus_platform

# --- WINDOWS GÖREV ÇUBUĞU ÖZEL İKON KİMLİĞİ ---
try:
    myappid = 'atii.wordbomb.vip.assistant.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def get_icon_path():
    """Hem geliştirme ortamında hem de PyInstaller .exe içinde doğru ikon yolunu bulur."""
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, 'wbs.ico')
        if os.path.exists(p):
            return p
    return os.path.abspath("wbs.ico")

def apply_icon_to_window(win):
    """Pencereye ikonu güvenli bir şekilde uygular."""
    icon_file = get_icon_path()
    if os.path.exists(icon_file):
        try:
            win.iconbitmap(icon_file)
        except Exception:
            pass

APP_BG = "#070B12"
TEXT_MAIN = "#E5E7EB"
TEXT_MUTED = "#94A3B8"

PRIMARY = "#3B82F6"
PRIMARY_HOVER = "#2563EB"

SECONDARY = "#182235"
SECONDARY_HOVER = "#22314D"

INPUT_BG = "#0E1625"
INPUT_BORDER = "#2F4D7A"

SWITCH_OFF = "#334155"
SWITCH_ON = "#22C55E"

ORANGE = "#D97706"
ORANGE_HOVER = "#F59E0B"

BLUE = "#2563EB"
BLUE_HOVER = "#3B82F6"

FONT_MAIN = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_INPUT = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 9, "bold")

LANG_OPTIONS = {
    "Türkçe": "tr",
    "English": "en",
    "Português": "pt"
}


class AutoUpdateDialog(ctk.CTkToplevel):
    """Otomatik İndiren ve Uygulayan Güncelleme Ekranı"""
    def __init__(self, parent, new_ver):
        super().__init__(parent)
        self.parent = parent
        self.title("Otomatik Güncelleyici")

        self.after(100, lambda: apply_icon_to_window(self))
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"340x210+{int(screen_width/2 - 170)}+{int(screen_height/2 - 105)}")
        
        self.resizable(False, False)
        self.configure(fg_color="#070B12")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.card = ctk.CTkFrame(self, fg_color="#0B1322", border_color="#D97706", border_width=1, corner_radius=14)
        self.card.pack(padx=14, pady=14, fill="both", expand=True)

        self.lbl_icon = ctk.CTkLabel(self.card, text=f"⚡ YENİ GÜNCELLEME ({new_ver})", font=("Segoe UI", 11, "bold"), text_color="#F59E0B")
        self.lbl_icon.pack(pady=(12, 2))

        self.lbl_status = ctk.CTkLabel(self.card, text="Yeni sürüm tespit edildi. Güncelleme zorunludur.", font=("Segoe UI", 9), text_color="#94A3B8")
        self.lbl_status.pack(pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(self.card, width=260, height=8, progress_color="#F59E0B", fg_color="#1E293B")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 10))

        self.btn_action = ctk.CTkButton(
            self.card,
            text="OTOMATİK GÜNCELLE",
            font=("Segoe UI", 10, "bold"),
            fg_color="#D97706",
            hover_color="#B45309",
            command=self.start_download
        )
        self.btn_action.pack(pady=(0, 6))

        self.after(50, lambda: (self.deiconify(), self.lift(), self.focus_force()))

    def on_close(self):
        self.parent.destroy()
        sys.exit(0)

    def start_download(self):
        self.btn_action.configure(state="disabled", text="İndiriliyor...")
        threading.Thread(target=self.download_and_apply, daemon=True).start()

    def download_and_apply(self):
        url = f"{SecurityManager.SERVER_URL}/api/download_update"
        target_zip = "update_temp.zip"

        try:
            res = requests.get(url, stream=True, timeout=30)
            if res.status_code != 200:
                raise Exception(f"Sunucu hatası: {res.status_code}")

            total_len = res.headers.get('content-length')

            if total_len is None:
                with open(target_zip, 'wb') as f:
                    f.write(res.content)
            else:
                dl = 0
                total_len = int(total_len)
                with open(target_zip, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=4096):
                        dl += len(chunk)
                        f.write(chunk)
                        percent = dl / total_len
                        self.after(0, lambda p=percent: self.progress_bar.set(p))
                        self.after(0, lambda p=int(percent*100): self.lbl_status.configure(text=f"İndiriliyor... %{p}"))

            self.after(0, lambda: self.lbl_status.configure(text="Yükleniyor ve Yeniden Başlatılıyor...", text_color="#34D399"))

            bat_script = """@echo off
timeout /t 2 /nobreak >nul
tar -xf update_temp.zip
del update_temp.zip
start "" "WordBomb.exe"
del "%~f0"
"""
            with open("updater.bat", "w") as f:
                f.write(bat_script)

            subprocess.Popen(["updater.bat"], shell=True)
            self.parent.destroy()
            sys.exit(0)

        except Exception as e:
            self.after(0, lambda: self.lbl_status.configure(text=f"Hata: {e}", text_color="#EF4444"))
            self.after(0, lambda: self.btn_action.configure(state="normal", text="Tekrar Dene"))


class LicenseDialog(ctk.CTkToplevel):
    """Sade ve Şık VIP Lisans Doğrulama Ekranı"""
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.title("WordBomb - created by atii")
        
        self.after(100, lambda: apply_icon_to_window(self))
        
        self.center_window(340, 235)
        self.resizable(False, False)
        self.configure(fg_color="#070B12")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.card = ctk.CTkFrame(
            self,
            fg_color="#0B1322",
            border_color="#1E293B",
            border_width=1,
            corner_radius=14
        )
        self.card.pack(padx=14, pady=(12, 6), fill="both", expand=True)

        self.badge = ctk.CTkLabel(
            self.card,
            text="● VIP EDITION ●",
            font=("Segoe UI", 9, "bold"),
            text_color="#38BDF8",
            fg_color="#082F49",
            corner_radius=6,
            height=18,
            padx=8
        )
        self.badge.pack(pady=(10, 2))

        self.lbl_title = ctk.CTkLabel(
            self.card, 
            text="WordBomb", 
            font=("Segoe UI", 15, "bold"), 
            text_color="#F8FAFC"
        )
        self.lbl_title.pack(pady=(0, 2))

        self.lbl_sub = ctk.CTkLabel(
            self.card, 
            text=f"Lütfen lisans anahtarınızı girin (v{CLIENT_VERSION})", 
            font=("Segoe UI", 9), 
            text_color="#64748B"
        )
        self.lbl_sub.pack(pady=(0, 8))

        self.entry_key = ctk.CTkEntry(
            self.card, 
            placeholder_text="WB-XXXX-XXXX-XXXX", 
            width=270, 
            height=32,
            font=("Consolas", 11, "bold"),
            fg_color="#070D18",
            border_color="#2563EB",
            border_width=1.5,
            text_color="#F8FAFC",
            placeholder_text_color="#475569",
            corner_radius=8,
            justify="center"
        )
        self.entry_key.pack(padx=18, pady=(0, 8))
        self.entry_key.bind("<Return>", lambda e: self.verify_key())

        self.btn_verify = ctk.CTkButton(
            self.card, 
            text="GİRİŞ YAP", 
            command=self.verify_key,
            width=270, 
            height=30,
            font=("Segoe UI", 11, "bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=8
        )
        self.btn_verify.pack(padx=18, pady=(0, 4))

        self.lbl_status = ctk.CTkLabel(
            self.card, 
            text="", 
            font=("Segoe UI", 9), 
            text_color="#EF4444"
        )
        self.lbl_status.pack(pady=(0, 2))

        self.footer = ctk.CTkFrame(self, fg_color="transparent", height=16)
        self.footer.pack(side="bottom", fill="x", padx=14, pady=(0, 5))

        self.lbl_discord = ctk.CTkLabel(
            self.footer,
            text="discord: fdsaqwex",
            font=("Segoe UI", 10, "bold"),
            text_color="#F59E0B"
        )
        self.lbl_discord.pack(side="right")

    def on_close(self):
        self.parent.destroy()
        sys.exit(0)

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def verify_key(self):
        key = self.entry_key.get().strip()
        if not key:
            self.lbl_status.configure(text="Lütfen lisans girin.", text_color="#EF4444")
            return

        self.btn_verify.configure(text="Doğrulanıyor...", state="disabled")
        self.lbl_status.configure(text="Sunucuya bağlanılıyor...", text_color="#94A3B8")
        
        def run_check():
            success, msg, is_update = SecurityManager.check_license(key)
            if is_update:
                # GÜNCELLEME VARSA DİREKT GÜNCELLEME DİYALOĞUNU AÇ
                self.after(0, lambda: self.show_update(msg))
            elif success:
                self.after(0, lambda: self.finish_success(msg))
            else:
                self.after(0, lambda: self.on_fail(msg))

        threading.Thread(target=run_check, daemon=True).start()

    def show_update(self, new_ver):
        self.destroy()
        AutoUpdateDialog(self.parent, new_ver)

    def on_fail(self, error_msg):
        self.btn_verify.configure(text="GİRİŞ YAP", state="normal")
        self.lbl_status.configure(text=error_msg, text_color="#EF4444")

    def finish_success(self, expire_date):
        self.lbl_status.configure(text="Giriş Başarılı!", text_color="#22C55E")
        self.after(300, self.destroy)
        self.on_success(expire_date)


class WordBombApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("WordBomb - created by atii")
        apply_icon_to_window(self)
        self.after(100, lambda: apply_icon_to_window(self))

        self.center_window(370, 245)
        self.resizable(False, False)
        self.configure(fg_color=APP_BG)
        self.withdraw()

        self.dict_mgr = DictionaryManager()
        self.writer = HumanoidWriter()
        self.scanner = AutoGameScanner(self.handle_auto_word_request)
        self.scanner.writer_ref = self.writer

        self.alphabet_level = 1
        
        self.stealth = StealthEngine(
            self.handle_stealth_word_request,
            self.toggle_stealth_visibility,
            self.change_word_mode,
            self.writer.request_stop,
            self.handle_blacklist_request
        )

        self.setup_ui()
        self.after(50, self.initial_license_check)

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def initial_license_check(self):
        saved_key = ""
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
            except Exception:
                saved_key = ""
        
        def check():
            # Eğer kayıtlı anahtar varsa onu kontrol et, yoksa genel sürüm kontrolü yap
            test_key = saved_key if saved_key else "VERSION_CHECK"
            success, msg, is_update = SecurityManager.check_license(test_key)
            
            if is_update:
                # GÜNCELLEME VARSA DİREKT GÜNCELLEME EKRANINI AÇ
                self.after(0, lambda: AutoUpdateDialog(self, msg))
            elif success and saved_key:
                self.after(0, lambda: self.on_license_validated(msg))
            else:
                self.after(0, self.open_license_dialog)

        threading.Thread(target=check, daemon=True).start()

    def open_license_dialog(self):
        LicenseDialog(self, self.on_license_validated)

    def on_license_validated(self, expire_date):
        self.center_window(370, 245)
        self.attributes("-topmost", True)
        self.deiconify()
        apply_icon_to_window(self)
        
        # Kurucu Statüsü Kontrolü
        if str(expire_date).upper() == "DEVELOPER" or "2099" in str(expire_date):
            self.lbl_license_info.configure(
                text="👑 KURUCU • Ömür Boyu",
                text_color="#F59E0B"
            )
        else:
            self.lbl_license_info.configure(
                text=f"● Lisans: {expire_date}",
                text_color="#34D399"
            )

        threading.Thread(target=self.stealth.start, daemon=True).start()
        self.scanner.start()

    def select_hece_region(self):
        self.withdraw()
        self.after(200, lambda: RegionSelector(self.on_hece_selected, title_text="HECE KUTUSU"))

    def on_hece_selected(self, bbox):
        self.scanner.set_hece_box(bbox)
        self.deiconify()
        self.btn_select_hece.configure(text="Hece ✓", fg_color=SWITCH_ON)

    def select_arrow_region(self):
        self.withdraw()
        self.after(200, lambda: RegionSelector(self.on_arrow_selected, title_text="Kendi profilinizin üstündeki 'SIRA SENDE'"))

    def on_arrow_selected(self, bbox):
        self.scanner.set_turn_box(bbox)
        self.deiconify()
        self.btn_select_arrow.configure(text="Ok ✓", fg_color=SWITCH_ON)

    def handle_blacklist_request(self):
        last_word = self.writer.last_typed_word
        if last_word:
            added = self.dict_mgr.add_to_blacklist(last_word)

    def handle_auto_word_request(self, hece):
        self.after(0, lambda: self.handle_word_request(hece, from_stealth=True))

    def setup_ui(self):
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=(6, 0), padx=10, fill="x")

        self.col1 = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.col1.pack(side="left", padx=2)

        self.platform_menu = ctk.CTkOptionMenu(
            self.col1,
            values=["Google Chrome", "Discord", "Discord Canary", "Discord PTB"],
            width=110,
            height=22,
            font=FONT_MAIN,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER,
            dropdown_fg_color=SECONDARY,
            dropdown_hover_color=SECONDARY_HOVER,
            dropdown_text_color=TEXT_MAIN,
            text_color=TEXT_MAIN,
            corner_radius=8,
            bg_color="transparent"
        )
        self.platform_menu.set("Discord")
        self.platform_menu.pack(pady=1)

        self.game_mode = ctk.CTkOptionMenu(
            self.col1,
            values=["Orjinal", "Zincir Kelime"],
            width=110,
            height=22,
            font=FONT_MAIN,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER,
            dropdown_fg_color=SECONDARY,
            dropdown_hover_color=SECONDARY_HOVER,
            dropdown_text_color=TEXT_MAIN,
            text_color=TEXT_MAIN,
            corner_radius=8,
            bg_color="transparent"
        )
        self.game_mode.pack(pady=1)

        self.col2 = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.col2.pack(side="left", padx=2)

        self.speed_mode = ctk.CTkOptionMenu(
            self.col2,
            values=["Rahat", "Normal", "Panik", "ALLAH"],
            width=90,
            height=22,
            font=FONT_MAIN,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER,
            dropdown_fg_color=SECONDARY,
            dropdown_hover_color=SECONDARY_HOVER,
            dropdown_text_color=TEXT_MAIN,
            text_color=TEXT_MAIN,
            corner_radius=8,
            bg_color="transparent"
        )
        self.speed_mode.set("Panik")
        self.speed_mode.pack(pady=1)

        self.lang_menu = ctk.CTkOptionMenu(
            self.col2,
            values=list(LANG_OPTIONS.keys()),
            width=90,
            height=22,
            font=FONT_MAIN,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_HOVER,
            dropdown_fg_color=SECONDARY,
            dropdown_hover_color=SECONDARY_HOVER,
            dropdown_text_color=TEXT_MAIN,
            text_color=TEXT_MAIN,
            corner_radius=8,
            bg_color="transparent"
        )
        self.lang_menu.set("Türkçe")
        self.lang_menu.pack(pady=1)

        self.col3 = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.col3.pack(side="left", padx=2)

        self.word_mode = ctk.CTkSegmentedButton(
            self.col3,
            values=["Hızlı", "Optimal", "Şov"],
            width=140,
            height=22,
            font=FONT_MAIN,
            fg_color=SECONDARY,
            selected_color=PRIMARY,
            selected_hover_color=PRIMARY_HOVER,
            unselected_color=SECONDARY,
            unselected_hover_color=SECONDARY_HOVER,
            text_color=TEXT_MAIN,
            corner_radius=8,
            bg_color="transparent"
        )
        self.word_mode.set("Optimal")
        self.word_mode.pack(pady=1)

        self.sw_frame = ctk.CTkFrame(self.col3, fg_color="transparent")
        self.sw_frame.pack(pady=0)

        self.sw_human = ctk.CTkSwitch(
            self.sw_frame,
            text="İnsansı",
            font=FONT_SMALL,
            width=65,
            text_color=TEXT_MUTED,
            progress_color=SWITCH_ON,
            fg_color=SWITCH_OFF,
            button_color=TEXT_MAIN,
            button_hover_color="#CBD5E1",
            bg_color="transparent"
        )
        self.sw_human.select()
        self.sw_human.pack(side="left")

        self.sw_mistake = ctk.CTkSwitch(
            self.sw_frame,
            text="Hata",
            font=FONT_SMALL,
            width=65,
            text_color=TEXT_MUTED,
            progress_color=SWITCH_ON,
            fg_color=SWITCH_OFF,
            button_color=TEXT_MAIN,
            button_hover_color="#CBD5E1",
            bg_color="transparent"
        )
        self.sw_mistake.pack(side="left")

        self.auto_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.auto_frame.pack(pady=(3, 1), fill="x")

        self.auto_inner = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        self.auto_inner.pack(anchor="center")

        self.sw_auto_ocr = ctk.CTkSwitch(
            self.auto_inner,
            text="Otomatik OCR",
            font=FONT_SMALL,
            width=100,
            text_color=TEXT_MAIN,
            progress_color=SWITCH_ON,
            fg_color=SWITCH_OFF,
            command=self.toggle_auto_ocr
        )
        self.sw_auto_ocr.pack(side="left", padx=(0, 6))

        self.chk_solo = ctk.CTkCheckBox(
            self.auto_inner,
            text="Solo",
            font=FONT_SMALL,
            width=45,
            text_color=TEXT_MUTED,
            fg_color=PRIMARY,
            command=self.toggle_solo_mode
        )
        self.chk_solo.pack(side="left", padx=(0, 6))

        self.btn_select_hece = ctk.CTkButton(
            self.auto_inner,
            text="Hece Seç",
            width=60,
            height=22,
            font=FONT_SMALL,
            fg_color=SECONDARY,
            hover_color=SECONDARY_HOVER,
            command=self.select_hece_region
        )
        self.btn_select_hece.pack(side="left", padx=2)

        self.btn_select_arrow = ctk.CTkButton(
            self.auto_inner,
            text="Sıra Alanı Seç",
            width=55,
            height=22,
            font=FONT_SMALL,
            fg_color=SECONDARY,
            hover_color=SECONDARY_HOVER,
            command=self.select_arrow_region
        )
        self.btn_select_arrow.pack(side="left", padx=2)

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(pady=3, padx=15, fill="x")

        self.missing_box = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Eksik harfler (örn: abcdefg)",
            width=335,
            height=25,
            font=FONT_MAIN,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            border_width=1,
            text_color=TEXT_MAIN,
            placeholder_text_color=TEXT_MUTED,
            corner_radius=9,
            bg_color="transparent"
        )
        self.missing_box.pack(pady=(0, 3))

        self.input_box = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Hece girin ve Enter basın...",
            width=335,
            height=28,
            font=FONT_INPUT,
            fg_color=INPUT_BG,
            border_color=PRIMARY,
            border_width=1,
            text_color=TEXT_MAIN,
            placeholder_text_color=TEXT_MUTED,
            corner_radius=10,
            bg_color="transparent"
        )
        self.input_box.pack(side="left")
        self.input_box.bind("<Return>", lambda e: self.handle_word_request(self.input_box.get()))

        self.speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.speed_frame.pack(pady=1, padx=15, fill="x")

        self.speed_label = ctk.CTkLabel(
            self.speed_frame,
            text="Oyun Hızı: 1.0x",
            font=FONT_MAIN,
            text_color=TEXT_MUTED,
            bg_color="transparent"
        )
        self.speed_label.pack(side="left", padx=5)

        self.speed_slider = ctk.CTkSlider(
            self.speed_frame,
            from_=1.0,
            to=2.0,
            number_of_steps=20,
            command=self.update_speed_label,
            fg_color=SECONDARY,
            progress_color=PRIMARY,
            button_color=TEXT_MAIN,
            button_hover_color="#CBD5E1",
            bg_color="transparent"
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(side="left", fill="x", expand=True, padx=5)

        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=(2, 2), padx=15, fill="x")

        self.chk_top = ctk.CTkCheckBox(
            self.bottom_frame,
            text="Hep Üstte",
            font=FONT_SMALL,
            width=80,
            command=self.toggle_top,
            text_color=TEXT_MUTED,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            border_color=INPUT_BORDER,
            checkmark_color=TEXT_MAIN,
            bg_color="transparent"
        )
        self.chk_top.select()
        self.chk_top.pack(side="left", padx=(0, 5))

        self.btn_reset = ctk.CTkButton(
            self.bottom_frame,
            text="Sıfırla",
            width=70,
            height=22,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
            text_color="#FFFFFF",
            font=FONT_BOLD,
            corner_radius=8,
            border_width=0,
            bg_color="transparent",
            command=self.dict_mgr.reset_used_words
        )
        self.btn_reset.pack(side="left", padx=5)

        self.btn_fill_alphabet = ctk.CTkButton(
            self.bottom_frame,
            text="Alfabeyi Doldur",
            width=100,
            height=22,
            fg_color=BLUE,
            hover_color=BLUE_HOVER,
            text_color="#FFFFFF",
            font=FONT_BOLD,
            corner_radius=8,
            border_width=0,
            bg_color="transparent",
            command=self.fill_alphabet
        )
        self.btn_fill_alphabet.pack(side="left", padx=5)

        # --- ALT DURUM VE BİLGİ ÇUBUĞU ---
        self.status_bar = ctk.CTkFrame(self, fg_color="transparent", height=18)
        self.status_bar.pack(side="bottom", fill="x", padx=14, pady=(0, 4))

        # En Sol Altta Lisans / Kurucu Rozeti
        self.lbl_license_info = ctk.CTkLabel(
            self.status_bar,
            text="● Lisans Kontrol Ediliyor...",
            font=("Segoe UI", 9, "bold"),
            text_color="#34D399"
        )
        self.lbl_license_info.pack(side="left")

        # En Sağ Altta Gold Discord İmzası
        self.lbl_discord = ctk.CTkLabel(
            self.status_bar,
            text="discord: fdsaqwex",
            font=("Segoe UI", 10, "bold"),
            text_color="#F59E0B"
        )
        self.lbl_discord.pack(side="right")

    def toggle_auto_ocr(self):
        self.scanner.auto_mode_enabled = (self.sw_auto_ocr.get() == 1)

    def toggle_solo_mode(self):
        self.scanner.solo_mode = (self.chk_solo.get() == 1)

    def get_selected_lang(self):
        return LANG_OPTIONS.get(self.lang_menu.get(), "tr")

    def handle_stealth_word_request(self, hece):
        self.after(0, lambda: self.handle_word_request(hece, from_stealth=True))

    def update_speed_label(self, value):
        self.speed_label.configure(text=f"Oyun Hızı: {value:.1f}x")

    def change_word_mode(self, new_mode):
        self.after(0, lambda: self.word_mode.set(new_mode))

    def fill_alphabet(self):
        self.alphabet_level = 1
        lang = self.get_selected_lang()
        alphabet = self.dict_mgr.get_alphabet(lang).lower()
        self.missing_box.delete(0, "end")
        self.missing_box.insert(0, alphabet)

    def toggle_top(self):
        self.attributes("-topmost", self.chk_top.get())

    def toggle_stealth_visibility(self):
        self.after(0, self._safe_toggle)

    def _safe_toggle(self):
        self.input_box.delete(0, "end")
        if self.state() == "normal":
            self.withdraw()
        else:
            self.deiconify()
            self.lift()
            self.focus_force()
            self.after(100, lambda: self.input_box.delete(0, "end"))
            self.after(110, lambda: self.input_box.focus())

    def handle_word_request(self, hece, from_stealth=False):
        if hece is None:
            return

        hece = str(hece)

        if not hece.strip():
            return

        lang = self.get_selected_lang()
        missing = self.missing_box.get()

        word = self.dict_mgr.get_filtered_word(
            hece,
            lang=lang,
            game_mode=self.game_mode.get(),
            word_mode=self.word_mode.get(),
            missing_letters=missing
        )

        if word:
            if focus_platform(self.platform_menu.get()):
                typed_word = self.writer.type_with_logic(
                    word,
                    speed_mode=self.speed_mode.get(),
                    is_human=self.sw_human.get(),
                    is_mistake=self.sw_mistake.get(),
                    lang=lang,
                    multiplier=self.speed_slider.get(),
                    word_mode=self.word_mode.get()
                )

                current_missing = self.missing_box.get()
                if current_missing:
                    used_for_missing = typed_word if typed_word else word
                    new_missing = self.dict_mgr.update_missing_letters_after_word(
                        missing_letters=current_missing,
                        word=used_for_missing,
                        lang=lang
                    )
                    
                    if not new_missing:
                        self.alphabet_level = 2
                        base_alphabet = self.dict_mgr.get_alphabet(lang).lower()
                        new_missing = "".join([c * self.alphabet_level for c in base_alphabet]).lower()

                    self.missing_box.delete(0, "end")
                    self.missing_box.insert(0, new_missing.lower())

        self.input_box.delete(0, "end")

        if not from_stealth:
            self.after(100, self.lift)
            self.after(110, self.focus_force)
            self.after(120, lambda: self.input_box.focus())


if __name__ == "__main__":
    app = WordBombApp()
    app.mainloop()