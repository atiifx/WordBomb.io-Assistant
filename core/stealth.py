import keyboard
import threading
import ctypes


class StealthEngine:
    def __init__(
        self,
        callback_function,
        visibility_callback,
        mode_callback,
        emergency_stop_callback=None,
        blacklist_callback=None
    ):
        self.active = False
        self.capturing = False
        self.buffer = ""

        self.callback = callback_function
        self.visibility_callback = visibility_callback
        self.mode_callback = mode_callback
        self.emergency_stop_callback = emergency_stop_callback
        self.blacklist_callback = blacklist_callback

        self.app_title = "WordBomb - created by atii"

        self.mode_hotkeys = {
            "f1": "Hızlı",
            "f2": "Optimal",
            "f3": "Şov"
        }

        self.game_title_keywords = [
            "wordbomb",
            "word bomb",
            "wordbomb.io",
            "bombparty",
            "bomb party",
            "jklm.fun",
            "jklm",
            "discord",
            "discord canary",
            "discord ptb",
            "google chrome",
            "chrome"
        ]

    def get_active_window_title(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value or ""
        except Exception:
            return ""

    def get_focus_state(self):
        title = self.get_active_window_title().strip()

        if not title:
            return False, False

        if title == self.app_title:
            return True, False

        lowered_title = title.lower()

        target_focused = any(
            keyword.lower() in lowered_title
            for keyword in self.game_title_keywords
        )

        return False, target_focused

    def is_app_focused(self):
        app_focused, _ = self.get_focus_state()
        return app_focused

    def is_game_focused(self):
        _, game_focused = self.get_focus_state()
        return game_focused

    def should_handle_mode_hotkeys(self):
        app_focused, game_focused = self.get_focus_state()

        if app_focused:
            return True

        if self.active and game_focused:
            return True

        return False

    def handle_events(self):
        keyboard.hook(self._process_key, suppress=True)
        keyboard.wait()

    def _toggle_active(self):
        self.active = not self.active
        self.capturing = False
        self.buffer = ""

        self.visibility_callback()

        status = "AKTIF" if self.active else "PASIF"
        print(f"Gizli Mod: {status}")

    def _emergency_stop(self):
        self.capturing = False
        self.buffer = ""

        if self.emergency_stop_callback:
            self.emergency_stop_callback()

        print("Acil durdurma tetiklendi.")

    def _process_key(self, event):
        if event.event_type != keyboard.KEY_DOWN:
            return True

        key_name = (event.name or "").lower()

        # ACİL DURDURMA (F8)
        if key_name == "f8":
            self._emergency_stop()
            return False

        # GİZLİ MOD AÇ / KAPAT (F7)
        if key_name == "f7":
            self._toggle_active()
            return False

        # KARA LİSTEYE AL (F4)
        if key_name == "f4":
            if self.blacklist_callback:
                threading.Thread(
                    target=self.blacklist_callback,
                    daemon=True
                ).start()
            return False

        app_focused, game_focused = self.get_focus_state()

        # KELİME MODU KISAYOLLARI (F1 / F2 / F3)
        if key_name in self.mode_hotkeys:
            if app_focused or (self.active and game_focused):
                self.mode_callback(self.mode_hotkeys[key_name])
                return False
            return True

        # GİZLİ MOD AKTİFKEN .hece YAKALAMA
        capture_context = self.active and (self.capturing or app_focused or game_focused)

        if capture_context:
            if not self.capturing and key_name == ".":
                self.capturing = True
                self.buffer = ""
                return False

            if self.capturing:
                if key_name == "enter":
                    captured_text = self.buffer
                    self.capturing = False
                    self.buffer = ""

                    if captured_text.strip():
                        threading.Thread(
                            target=self.callback,
                            args=(captured_text,),
                            daemon=True
                        ).start()

                    return False

                if key_name == "space":
                    self.buffer += " "
                    return False

                if key_name == "backspace":
                    self.buffer = self.buffer[:-1]
                    return False

                if key_name in ("esc", "escape"):
                    self.capturing = False
                    self.buffer = ""
                    return False

                if len(key_name) == 1:
                    self.buffer += key_name
                    return False

                return False

        return True

    def start(self):
        self.handle_events()