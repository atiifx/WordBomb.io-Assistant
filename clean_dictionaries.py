import os

# Dosya yolları
BLACKLIST_FILE = "blacklist.txt"
DICT_FILES = ["data/words_tr.txt", "data/words_en.txt", "data/words_pt.txt"]


def clean_dictionaries():
    if not os.path.exists(BLACKLIST_FILE):
        print(f"[!] '{BLACKLIST_FILE}' bulunamadı. Temizlenecek kelime yok.")
        return

    # 1. Kara listedeki kelimeleri oku ve normalize et
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        blacklisted_words = {line.strip().lower() for line in f if line.strip()}

    if not blacklisted_words:
        print("[!] Kara liste dosyası boş.")
        return

    print(f"[*] Toplam {len(blacklisted_words)} engelli kelime işleniyor...\n")

    # 2. Her dil dosyasını tara ve engelli kelimeleri çıkar
    total_removed = 0

    for dict_file in DICT_FILES:
        if not os.path.exists(dict_file):
            print(f"[-] '{dict_file}' yerelde bulunamadı, atlanıyor.")
            continue

        with open(dict_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        original_count = len(lines)
        # Sadece kara listede OLMAYAN kelimeleri koru
        clean_lines = [
            line for line in lines 
            if line.strip().lower() not in blacklisted_words
        ]
        
        removed_count = original_count - len(clean_lines)
        total_removed += removed_count

        # Temizlenmiş listeyi dosyaya geri yaz
        with open(dict_file, "w", encoding="utf-8") as f:
            f.writelines(clean_lines)

        print(f"[✓] {dict_file}: {removed_count} hatalı kelime çıkarıldı. (Kalan: {len(clean_lines)})")

    print(f"\n[SUCCESS] İşlem tamamlandı! Toplam {total_removed} kelime veritabanlarından silindi.")

    # 3. İsteğe bağlı: Temizlik bittikten sonra blacklist.txt dosyasını sıfırla
    clear_choice = input("\n'blacklist.txt' dosyasının içi sıfırlansın mı? (e/h): ").strip().lower()
    if clear_choice == "e":
        open(BLACKLIST_FILE, "w", encoding="utf-8").close()
        print("[✓] 'blacklist.txt' başarıyla sıfırlandı.")


if __name__ == "__main__":
    clean_dictionaries()