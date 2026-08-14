import time
import random
from pynput.keyboard import Controller, Key


class KeyboardLayouts:
    NEARBY_CHARS = {
        "tr": {
            "a": "sqz", "b": "vgn", "c": "xv", "ç": "ö.", "d": "serf", "e": "rwrd",
            "f": "dgrt", "g": "fhtb", "h": "gjny", "ı": "uio", "i": "uok", "j": "hkm",
            "k": "jli", "l": "kiş", "m": "nj", "n": "bmh", "o": "ipk", "ö": "çlp",
            "p": "oğ", "r": "etf", "s": "ade", "ş": "li", "t": "rgy", "u": "ıy",
            "ü": "ğ", "v": "cb", "y": "tu", "z": "asx"
        },
        "en": {
            "a": "sqz", "b": "vgn", "c": "xv", "d": "serf", "e": "rwrd", "f": "dgrt",
            "g": "fhtb", "h": "gjny", "i": "uok", "j": "hkm", "k": "jli", "l": "ki",
            "m": "nj", "n": "bmh", "o": "ipk", "p": "o", "q": "wa", "r": "etf",
            "s": "ade", "t": "rgy", "u": "iy", "v": "cb", "w": "qe", "x": "zc",
            "y": "ut", "z": "as"
        },
        "pt": {
            "q": "wa", "w": "qeas", "e": "wrds", "r": "etdf", "t": "ryfg", "y": "tugh",
            "u": "yijh", "i": "uokj", "o": "iplk", "p": "ol", "a": "sqz", "s": "awedxz",
            "d": "serfcx", "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "j": "huikmn",
            "k": "jiolm", "l": "kopç", "ç": "lp", "z": "asx", "x": "zsdc", "c": "xdfv",
            "v": "cfgb", "b": "vghn", "n": "bhjm", "m": "njk", "á": "asq", "à": "asq",
            "â": "asq", "ã": "asq", "é": "ews", "ê": "ews", "í": "iuo", "ó": "oip",
            "ô": "oip", "õ": "oip", "ú": "uyj", "ü": "uyj"
        }
    }

    ALPHABETS = {
        "tr": "abcçdefghıiklmnoöprsştuüvyz",
        "en": "abcdefghijklmnopqrstuvwxyz",
        "pt": "abcdefghijklmnopqrstuvwxyzçáàâãéêíóôõúü"
    }

    @staticmethod
    def get_nearby_char(char, lang="tr"):
        lang_map = KeyboardLayouts.NEARBY_CHARS.get(lang, KeyboardLayouts.NEARBY_CHARS["en"])
        nearby = lang_map.get(char.lower())

        if not nearby:
            nearby = KeyboardLayouts.ALPHABETS.get(lang, KeyboardLayouts.ALPHABETS["en"])

        wrong = random.choice(nearby)

        for _ in range(5):
            if wrong.lower() != char.lower():
                return wrong
            wrong = random.choice(nearby)

        alphabet = KeyboardLayouts.ALPHABETS.get(lang, KeyboardLayouts.ALPHABETS["en"])
        fallback = [c for c in alphabet if c != char.lower()]

        return random.choice(fallback) if fallback else wrong


class HumanoidWriter:
    def __init__(self):
        self.controller = Controller()
        self.stop_requested = False
        self.last_typed_word = ""

        # Emniyetli Alt Sınır Gecikmeleri (Windows tuş yutma koruması)
        self.min_key_gap = 0.020
        self.min_backspace_gap = 0.030

        self.hizlar = {
            "Rahat": {
                "delay": (0.22, 0.38),
                "reaction": (0.50, 0.90),
                "mistake_chance": 0.12,
                "human_delete_chance": 0.35,
                "start_pause": (0.04, 0.12),
                "mid_pause_chance": 0.18,
                "mid_pause": (0.07, 0.18),
                "long_pause_chance": 0.25,
                "long_pause": (0.08, 0.22),
                "stop_chance": 0.5,
                "stop_pause": (0.65, 1.25)
            },
            "Normal": {
                "delay": (0.12, 0.22),
                "reaction": (0.30, 0.60),
                "mistake_chance": 0.18,
                "human_delete_chance": 0.30,
                "start_pause": (0.025, 0.09),
                "mid_pause_chance": 0.12,
                "mid_pause": (0.05, 0.13),
                "long_pause_chance": 0.18,
                "long_pause": (0.06, 0.16),
                "stop_chance": 0.5,
                "stop_pause": (0.55, 1.10)
            },
            "Panik": {
                "delay": (0.08, 0.14),
                "reaction": (0.20, 0.40),
                "mistake_chance": 0.25,
                "human_delete_chance": 0.24,
                "start_pause": (0.010, 0.045),
                "mid_pause_chance": 0.06,
                "mid_pause": (0.025, 0.075),
                "long_pause_chance": 0.10,
                "long_pause": (0.035, 0.10),
                "stop_chance": 0.5,
                "stop_pause": (0.45, 0.90)
            },
            "ALLAH": {
                "delay": (0.025, 0.045),
                "reaction": (0.15, 0.30),
                "mistake_chance": 0.20,
                "human_delete_chance": 0.40,
                "start_pause": (0.020, 0.060),
                "mid_pause_chance": 0.35,
                "mid_pause": (0.080, 0.180),
                "long_pause_chance": 0.45,
                "long_pause": (0.120, 0.280),
                "stop_chance": 0.30,
                "stop_pause": (0.35, 0.70)
            }
        }

    def request_stop(self):
        self.stop_requested = True
        print("Writer durdurma isteği aldı.")

    def clear_stop(self):
        self.stop_requested = False

    def _type_char(self, char, correction=False):
        if self.stop_requested:
            return False

        try:
            # Boşluk karakteri için Özel Key.space kontrolü (Kelimeleri birleştirmeyi engeller)
            if char == " ":
                self.controller.press(Key.space)
                time.sleep(0.015)
                self.controller.release(Key.space)
            else:
                self.controller.press(char)
                time.sleep(0.015)
                self.controller.release(char)
        except Exception:
            try:
                if char == " ":
                    self.controller.press(Key.space)
                    self.controller.release(Key.space)
                else:
                    self.controller.type(char)
            except Exception:
                return False

        gap = self.min_key_gap if not correction else self.min_key_gap * 1.5
        time.sleep(gap)
        return not self.stop_requested

    def _press_backspace(self):
        if self.stop_requested:
            return False

        try:
            self.controller.press(Key.backspace)
            time.sleep(0.010)
            self.controller.release(Key.backspace)
        except Exception as e:
            print(f"Backspace basılamadı: {e}")
            return False

        time.sleep(self.min_backspace_gap)
        return not self.stop_requested

    def _sleep(self, seconds):
        if seconds <= 0:
            return True

        end_time = time.time() + seconds

        while time.time() < end_time:
            if self.stop_requested:
                return False

            remaining = end_time - time.time()
            time.sleep(min(0.01, max(0, remaining)))

        return True

    def type_with_logic(
        self,
        word,
        speed_mode,
        is_human,
        is_mistake,
        lang,
        multiplier=1.0,
        word_mode="Optimal"
    ):
        if not word:
            return None

        self.clear_stop()
        self.last_typed_word = word
        settings = self._get_settings(speed_mode, multiplier)

        # 1. HATA MODU
        if is_mistake:
            should_send_wrong_word = (
                len(word) >= 4
                and random.random() < settings["mistake_chance"]
            )

            if should_send_wrong_word:
                wrong_word = self._make_wrong_word(word, lang)

                if not self._sleep_before_word(wrong_word, settings, word_mode):
                    return None

                if not self._write_direct(wrong_word, settings, self._build_pause_map(wrong_word, settings, word_mode)):
                    return None

                if not self._press_enter_after_delay(settings):
                    return None

                if not self._sleep(random.uniform(0.35, 0.70) / settings["multiplier"]):
                    return None

                if not self._sleep_before_word(word, settings, word_mode):
                    return None

                if not self._write_direct(word, settings, self._build_pause_map(word, settings, word_mode)):
                    return None

                self._press_enter_after_delay(settings)
                return wrong_word + word

        # 2. NORMAL / INSANSI MOD
        if is_human:
            if not self._sleep(random.uniform(settings["reaction"][0], settings["reaction"][1])):
                return None

        if not self._sleep_before_word(word, settings, word_mode):
            return None

        if is_human:
            if not self._write_humanized(word, settings, lang, self._build_pause_map(word, settings, word_mode)):
                return None
        else:
            if not self._write_direct(word, settings, self._build_pause_map(word, settings, word_mode)):
                return None

        self._press_enter_after_delay(settings)
        return word

    def _press_enter_after_delay(self, settings):
        if not self._sleep(random.uniform(0.035, 0.08) / settings["multiplier"]):
            return False

        if self.stop_requested:
            return False

        try:
            self.controller.press(Key.enter)
            time.sleep(0.015)
            self.controller.release(Key.enter)
        except Exception as e:
            print(f"Enter tuşuna basılamadı: {e}")
            return False

        return True

    def _get_settings(self, speed_mode, multiplier):
        multiplier = max(1.0, min(float(multiplier or 1.0), 2.0))
        base = self.hizlar.get(speed_mode, self.hizlar["Normal"])

        return {
            "delay": (
                max(0.015, base["delay"][0] / multiplier),
                max(0.025, base["delay"][1] / multiplier)
            ),
            "reaction": (
                base["reaction"][0] / multiplier,
                base["reaction"][1] / multiplier
            ),
            "mistake_chance": base["mistake_chance"],
            "human_delete_chance": base["human_delete_chance"],
            "multiplier": multiplier,
            "start_pause": (
                base["start_pause"][0] / multiplier,
                base["start_pause"][1] / multiplier
            ),
            "mid_pause_chance": base["mid_pause_chance"],
            "mid_pause": (
                base["mid_pause"][0] / multiplier,
                base["mid_pause"][1] / multiplier
            ),
            "long_pause_chance": base["long_pause_chance"],
            "long_pause": (
                base["long_pause"][0] / multiplier,
                base["long_pause"][1] / multiplier
            ),
            "stop_chance": base["stop_chance"],
            "stop_pause": (
                base["stop_pause"][0] / multiplier,
                base["stop_pause"][1] / multiplier
            )
        }

    def _word_mode_pause_factor(self, word_mode):
        if word_mode == "Hızlı":
            return 0.75
        if word_mode == "Şov":
            return 1.25
        return 1.0

    def _sleep_before_word(self, word, settings, word_mode):
        start_min, start_max = settings["start_pause"]

        if start_max <= 0:
            return True

        factor = self._word_mode_pause_factor(word_mode)
        pause = random.uniform(start_min, start_max) * factor

        if len(word) >= 11:
            pause += random.uniform(0.005, 0.035) / settings["multiplier"]

        return self._sleep(pause)

    def _write_direct(self, text, settings, pause_map):
        for index, char in enumerate(text):
            if self.stop_requested:
                return False

            if not self._type_char(char):
                return False

            if not self._sleep(settings["delay"][0]):
                return False

            if not self._sleep_pause_if_needed(pause_map, index):
                return False

        return True

    def _write_humanized(self, text, settings, lang, pause_map):
        total = len(text)

        alpha_indexes = [
            i for i, char in enumerate(text)
            if char.isalpha() and 2 <= i <= len(text) - 3
        ]

        should_delete_fix = (
            len(alpha_indexes) > 0
            and random.random() < settings["human_delete_chance"]
        )

        delete_index = random.choice(alpha_indexes) if should_delete_fix else None
        
        for i, char in enumerate(text):
            if self.stop_requested:
                return False

            if delete_index is not None and i == delete_index:
                wrong_char = KeyboardLayouts.get_nearby_char(char, lang)
                
                self._type_char(wrong_char, correction=True)
                time.sleep(0.18)
                
                self._press_backspace()
                time.sleep(0.12)
                
                self._type_char(char, correction=True)
                time.sleep(0.05)
                
                delete_index = None
                continue

            if not self._type_char(char):
                return False

            if not self._sleep_after_key(settings, i, total, char):
                return False

            if not self._sleep_pause_if_needed(pause_map, i):
                return False

        return True

    def _sleep_after_key(self, settings, index, total, char, correction=False):
        delay = random.uniform(settings["delay"][0], settings["delay"][1])

        if index == 0:
            delay *= 1.06
        elif index == 1:
            delay *= 1.03

        if correction:
            delay *= 1.05

        return self._sleep(delay)

    def _build_pause_map(self, text, settings, word_mode):
        pause_map = {}

        if len(text) < 5:
            return pause_map

        factor = self._word_mode_pause_factor(word_mode)

        pause_indexes = [
            i for i, char in enumerate(text)
            if char.isalpha() and 2 <= i <= len(text) - 3
        ]

        if not pause_indexes:
            return pause_map

        mid_chance = min(settings["mid_pause_chance"] * factor, 0.45)
        long_chance = min(settings["long_pause_chance"] * factor, 0.55)

        if random.random() < mid_chance:
            index = random.choice(pause_indexes)
            pause_map[index] = random.uniform(
                settings["mid_pause"][0],
                settings["mid_pause"][1]
            )

        if len(text) >= 11 and random.random() < long_chance:
            available_indexes = [
                index for index in pause_indexes
                if index not in pause_map
            ]

            if not available_indexes:
                available_indexes = pause_indexes

            index = random.choice(available_indexes)
            pause_map[index] = pause_map.get(index, 0) + random.uniform(
                settings["long_pause"][0],
                settings["long_pause"][1]
            )

        if len(text) >= 7:
            stop_chance = min(settings["stop_chance"] * factor, 0.12)

            if random.random() < stop_chance:
                stop_indexes = [
                    index for index in pause_indexes
                    if 3 <= index <= len(text) - 4
                ]

                if stop_indexes:
                    index = random.choice(stop_indexes)
                    pause_map[index] = pause_map.get(index, 0) + random.uniform(
                        settings["stop_pause"][0],
                        settings["stop_pause"][1]
                    )

        return pause_map

    def _sleep_pause_if_needed(self, pause_map, index):
        pause = pause_map.get(index)

        if not pause:
            return True

        return self._sleep(pause)

    def _make_wrong_word(self, word, lang):
        chars = list(word)

        candidate_indexes = [
            i for i, char in enumerate(chars)
            if char.isalpha()
        ]

        if not candidate_indexes:
            return word

        error_count = random.randint(2, 3)
        error_count = min(error_count, len(candidate_indexes))

        indexes = random.sample(candidate_indexes, error_count)

        for index in indexes:
            chars[index] = KeyboardLayouts.get_nearby_char(chars[index], lang)

        wrong_word = "".join(chars)

        if wrong_word == word and candidate_indexes:
            index = random.choice(candidate_indexes)
            chars[index] = KeyboardLayouts.get_nearby_char(chars[index], lang)
            wrong_word = "".join(chars)

        return wrong_word