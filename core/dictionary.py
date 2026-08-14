import os
import random
import re
import requests
import unicodedata


class DictionaryManager:
    ALPHABETS = {
        "tr": "abcçdefghıiklmnoöprsştuüvyz",
        "en": "abcdefghijklmnopqrstuvwxyz",
        "pt": "abcdefghijklmnopqrstuvwxyz"
    }

    DICTIONARY_URLS = {
        "tr": "https://raw.githubusercontent.com/atiifx/wordbomb-data/refs/heads/main/words_tr.txt",
        "en": "https://raw.githubusercontent.com/atiifx/wordbomb-data/refs/heads/main/words_en.txt",
        "pt": "https://raw.githubusercontent.com/atiifx/wordbomb-data/refs/heads/main/words_pt.txt"
    }

    def __init__(self):
        self.words = {
            "tr": [],
            "en": [],
            "pt": []
        }

        self.words_tr = self.words["tr"]
        self.words_en = self.words["en"]
        self.words_pt = self.words["pt"]

        self.used_words = set()

        self.blacklist_file = "blacklist.txt"
        self.blacklisted_words = set()
        self.load_blacklist()

        self.load_dictionaries()

    def load_blacklist(self):
        if os.path.exists(self.blacklist_file):
            try:
                with open(self.blacklist_file, "r", encoding="utf-8") as f:
                    self.blacklisted_words = {line.strip().lower() for line in f if line.strip()}
                print(f"Kara liste yüklendi: {len(self.blacklisted_words)} kelime")
            except Exception as e:
                print(f"Kara liste yükleme hatası: {e}")

    def add_to_blacklist(self, word):
        if not word:
            return None
        word_clean = word.lower().strip()
        if word_clean not in self.blacklisted_words:
            self.blacklisted_words.add(word_clean)
            try:
                with open(self.blacklist_file, "a", encoding="utf-8") as f:
                    f.write(f"{word_clean}\n")
            except Exception as e:
                print(f"Kara listeye yazma hatası: {e}")

            for lang in self.words:
                self.words[lang] = [w for w in self.words[lang] if w.lower() != word_clean]
            self.words_tr = self.words.get("tr", [])
            self.words_en = self.words.get("en", [])
            self.words_pt = self.words.get("pt", [])
            return word_clean
        return None

    def get_alphabet(self, lang="tr"):
        return self.ALPHABETS.get(lang, self.ALPHABETS["en"])

    def clean_english_text(self, text, trim=True):
        if not text:
            return ""

        cleaned = re.sub(r"[^a-zA-Z0-9\s\-\']", "", text)
        cleaned = cleaned.lower()
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip() if trim else cleaned

    def clean_portuguese_text(self, text, trim=True):
        if not text:
            return ""

        cleaned = re.sub(
            r"[^a-zA-ZáàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ0-9\s\-\']",
            "",
            text
        )

        cleaned = cleaned.lower()
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip() if trim else cleaned

    def tr_lower(self, text, trim=True):
        if not text:
            return ""

        text = text.replace("İ", "i").replace("I", "ı")
        dmap = str.maketrans("ĞÜŞÖÇ", "ğüşöç")
        text = text.translate(dmap).lower()
        text = re.sub(r"\s+", " ", text)

        return text.strip() if trim else text

    def strip_accents(self, text):
        if not text:
            return ""

        normalized = unicodedata.normalize("NFD", text)

        return "".join(
            char for char in normalized
            if unicodedata.category(char) != "Mn"
        )

    def normalize_text(self, text, lang="tr", trim=True):
        if not text:
            return ""

        if lang == "tr":
            return self.tr_lower(text, trim=trim)

        if lang == "pt":
            return self.clean_portuguese_text(text, trim=trim)

        return self.clean_english_text(text, trim=trim)

    def normalize_search_text(self, text, lang="tr", trim=False):
        normalized = self.normalize_text(text, lang, trim=trim)

        if lang == "pt":
            return self.strip_accents(normalized)

        return normalized

    def normalize_missing_letters(self, missing_letters, lang="tr"):
        if not missing_letters:
            return ""

        alphabet = set(self.get_alphabet(lang))
        normalized = self.normalize_search_text(missing_letters, lang)

        result = []
        seen = set()

        for char in normalized:
            if char in alphabet and char not in seen:
                result.append(char)
                seen.add(char)

        return "".join(result)

    def get_word_letters(self, word, lang="tr"):
        alphabet = set(self.get_alphabet(lang))
        normalized = self.normalize_search_text(word, lang)

        return {
            char for char in normalized
            if char in alphabet
        }

    def word_length(self, word, lang="tr"):
        alphabet = set(self.get_alphabet(lang))
        normalized = self.normalize_search_text(word, lang)

        return sum(
            1 for char in normalized
            if char in alphabet
        )

    def update_missing_letters_after_word(self, missing_letters, word, lang="tr"):
        if not missing_letters or not word:
            return missing_letters

        unique_chars_in_word = set(word.lower())

        missing_list = list(missing_letters.lower())

        for char in unique_chars_in_word:
            if char in missing_list:
                missing_list.remove(char)

        updated_missing = "".join(missing_list).lower()
        return updated_missing

    def unique_keep_order(self, words):
        seen = set()
        result = []

        for word in words:
            if not word:
                continue

            if word not in seen:
                result.append(word)
                seen.add(word)

        return result

    def load_dictionaries(self):
        print("Sözlükler GitHub'dan indiriliyor, lütfen bekleyin...")

        for lang, url in self.DICTIONARY_URLS.items():
            try:
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    print(f"{lang.upper()} sözlük indirilemedi. HTTP: {response.status_code}")
                    continue

                content = response.content.decode("utf-8")

                words = []

                for line in content.splitlines():
                    word = self.normalize_text(line, lang, trim=True)

                    if word and word.lower() not in self.blacklisted_words:
                        words.append(word)

                self.words[lang] = self.unique_keep_order(words)

                print(f"{lang.upper()} sözlük yüklendi: {len(self.words[lang])}")

            except Exception as e:
                print(f"{lang.upper()} sözlük bağlantı hatası: {e}")

        self.words_tr = self.words.get("tr", [])
        self.words_en = self.words.get("en", [])
        self.words_pt = self.words.get("pt", [])

        print(
            f"Sözlükler hazır: "
            f"TR({len(self.words_tr)}), "
            f"EN({len(self.words_en)}), "
            f"PT({len(self.words_pt)})"
        )

    def get_filtered_word(self, hece, lang="tr", game_mode="Orjinal", word_mode="Optimal", missing_letters=""):
        source = self.words.get(lang, self.words["en"])

        if not source:
            return None

        hece_search = self.normalize_search_text(hece, lang, trim=False)

        if not hece_search or not hece_search.strip():
            return None

        base_candidates = self.get_base_candidates(
            source=source,
            hece_search=hece_search,
            game_mode=game_mode,
            lang=lang
        )

        if not base_candidates:
            return None

        normalized_missing = self.normalize_missing_letters(missing_letters, lang)
        missing_set = set(normalized_missing)

        selected_word = self.select_word_by_mode(
            candidates=base_candidates,
            word_mode=word_mode,
            missing_set=missing_set,
            lang=lang
        )

        if selected_word:
            self.used_words.add(selected_word)
            return selected_word

        return None

    def get_base_candidates(self, source, hece_search, game_mode, lang):
        if not hece_search:
            return []

        def word_key(word):
            return self.normalize_search_text(word, lang, trim=True)

        clean_strip = hece_search.strip()

        # 1. TAMLAMA / ÇOKLU KELİME ARAMASI (Örn: "E S" -> 1. parça E ile BİTECEK, 2. parça S ile BAŞLAYACAK)
        if " " in clean_strip:
            parts = clean_strip.split()
            if len(parts) >= 2:
                space_candidates = []
                part1, part2 = parts[0], parts[1]

                for word in source:
                    if word in self.used_words:
                        continue
                    
                    norm_word = word_key(word)
                    if "-" in norm_word or " " in norm_word:
                        sub_words = re.split(r"[\s\-]+", norm_word)
                        if len(sub_words) >= 2:
                            if sub_words[0].endswith(part1) and sub_words[1].startswith(part2):
                                space_candidates.append(word)

                if space_candidates:
                    return space_candidates

        # 2. X- FORMATI (Örn: "A-" veya "A ") -> İlk parça target_char ile BİTECEK
        if hece_search.endswith(" ") and not hece_search.startswith(" "):
            target_char = clean_strip
            dash_candidates = []

            for word in source:
                if word in self.used_words:
                    continue
                norm_word = word_key(word)
                if "-" in norm_word or " " in norm_word:
                    sub_words = re.split(r"[\s\-]+", norm_word)
                    if sub_words and sub_words[0].endswith(target_char):
                        dash_candidates.append(word)

            if dash_candidates:
                return dash_candidates

            # Emniyet: Asla düz kelimeye düşme, sadece tireli alternatif sun
            return [
                word for word in source
                if ("-" in word or " " in word) and target_char in word_key(word)
                and word not in self.used_words
            ]

        # 3. -X FORMATI (Örn: "-F" veya " F") -> 2. veya sonraki parçalar target_char ile BAŞLAYACAK
        if hece_search.startswith(" ") and not hece_search.endswith(" "):
            target_char = clean_strip
            dash_candidates = []

            for word in source:
                if word in self.used_words:
                    continue
                norm_word = word_key(word)
                if "-" in norm_word or " " in norm_word:
                    sub_words = re.split(r"[\s\-]+", norm_word)
                    if len(sub_words) >= 2:
                        if not sub_words[0].startswith(target_char) and any(sub.startswith(target_char) for sub in sub_words[1:] if sub):
                            dash_candidates.append(word)

            if dash_candidates:
                return dash_candidates

            # Emniyet: Asla düz kelimeye düşme
            return [
                word for word in source
                if ("-" in word or " " in word) and target_char in word_key(word)
                and word not in self.used_words
            ]

        # 4. DÜZ İÇİNDE GEÇEN ARAMA (SADECE TİRESİZ DÜZ HECELER İÇİN)
        clean_hece = clean_strip

        if game_mode == "Zincir Kelime":
            startswith_candidates = [
                word for word in source
                if word_key(word).startswith(clean_hece)
                and word not in self.used_words
            ]
            if startswith_candidates:
                return startswith_candidates

        exact_matches = [
            word for word in source
            if clean_hece in word_key(word)
            and word not in self.used_words
        ]

        if exact_matches:
            return exact_matches

        return []

    def select_word_by_mode(self, candidates, word_mode, missing_set, lang):
        if not candidates:
            return None

        fallback_order = self.get_mode_fallback_order(word_mode)

        for active_mode in fallback_order:
            mode_candidates = self.get_mode_candidates(candidates, active_mode, lang)

            if not mode_candidates:
                continue

            if missing_set:
                selected = self.select_by_missing_letters(
                    mode_candidates=mode_candidates,
                    word_mode=active_mode,
                    missing_set=missing_set,
                    lang=lang
                )

                if selected:
                    return selected

            return self.select_without_missing(mode_candidates, active_mode, lang)

        return None

    def get_mode_fallback_order(self, word_mode):
        if word_mode == "Hızlı":
            return ["Hızlı", "Optimal", "Şov"]

        if word_mode == "Şov":
            return ["Şov", "Optimal", "Hızlı"]

        return ["Optimal", "Hızlı", "Şov"]

    def get_mode_label(self, word_mode):
        if word_mode == "Şov":
            return "Şov"

        if word_mode == "Hızlı":
            return "Hızlı"

        return "Optimal"

    def get_mode_candidates(self, candidates, word_mode, lang):
        if word_mode == "Şov":
            return [
                word for word in candidates
                if self.word_length(word, lang) >= 14
            ]

        if word_mode == "Optimal":
            return [
                word for word in candidates
                if 6 <= self.word_length(word, lang) <= 13
            ]

        return [
            word for word in candidates
            if self.word_length(word, lang) <= 6
        ]

    def select_by_missing_letters(self, mode_candidates, word_mode, missing_set, lang):
        scored = [
            (word, self.missing_hit_count(word, missing_set, lang))
            for word in mode_candidates
        ]

        if not scored:
            return None

        best_hit = max(hit for _, hit in scored)

        if best_hit <= 0:
            return None

        best_candidates = [
            word for word, hit in scored
            if hit == best_hit
        ]

        return self.pick_best_candidate_for_mode(best_candidates, word_mode, lang)

    def missing_hit_count(self, word, missing_set, lang):
        word_letters = self.get_word_letters(word, lang)
        return len(word_letters & missing_set)

    def pick_best_candidate_for_mode(self, candidates, word_mode, lang):
        if not candidates:
            return None

        if word_mode == "Şov":
            max_len = max(self.word_length(word, lang) for word in candidates)

            top_pool = [
                word for word in candidates
                if self.word_length(word, lang) >= max_len - 2
            ]

            return random.choice(top_pool)

        if word_mode == "Optimal":
            ideal_length = 9

            best_distance = min(
                abs(self.word_length(word, lang) - ideal_length)
                for word in candidates
            )

            top_pool = [
                word for word in candidates
                if abs(self.word_length(word, lang) - ideal_length) <= best_distance + 1
            ]

            return random.choice(top_pool)

        min_len = min(self.word_length(word, lang) for word in candidates)

        top_pool = [
            word for word in candidates
            if self.word_length(word, lang) <= min_len + 1
        ]

        return random.choice(top_pool)

    def select_without_missing(self, candidates, word_mode, lang):
        if not candidates:
            return None

        if word_mode == "Şov":
            max_len = max(self.word_length(word, lang) for word in candidates)

            top_pool = [
                word for word in candidates
                if self.word_length(word, lang) == max_len
            ]

            return random.choice(top_pool)

        if word_mode == "Optimal":
            return random.choice(candidates)

        min_len = min(self.word_length(word, lang) for word in candidates)

        top_pool = [
            word for word in candidates
            if self.word_length(word, lang) == min_len
        ]

        return random.choice(top_pool)

    def reset_used_words(self):
        self.used_words.clear()
        print("Kelime hafızası sıfırlandı.")