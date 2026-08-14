import os
import requests
import subprocess
import socket

# --- APPDATA GİZLİ DİZİNİ ---
APPDATA_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'WordBomb')
os.makedirs(APPDATA_DIR, exist_ok=True)
LICENSE_FILE = os.path.join(APPDATA_DIR, 'license.key')

CLIENT_VERSION = "1.0.0"


class SecurityManager:
    SERVER_URL = "http://34.139.220.109:8000"  # <-- VDS IP adresini yaz

    @staticmethod
    def get_hwid():
        """Windows 11 uyumlu, wmic gerektirmeyen güvenli HWID üretici"""
        # 1. Yöntem: Windows Kayıt Defteri MachineGuid (En Hızlı ve Stabil)
        try:
            import winreg
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            guid, _ = winreg.QueryValueEx(registry_key, "MachineGuid")
            winreg.CloseKey(registry_key)
            if guid:
                return str(guid).strip()
        except Exception:
            pass

        # 2. Yöntem: PowerShell ile UUID sorgusu (WMIC alternatifi)
        try:
            cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"]
            res = subprocess.check_output(cmd, creationflags=0x08000000, timeout=3).decode().strip()
            if res:
                return res
        except Exception:
            pass

        # 3. Yöntem: Hostname Yedek
        try:
            return socket.gethostname()
        except Exception:
            return "UNKNOWN_HWID"

    @staticmethod
    def check_license(key):
        if not key:
            return False, "Lütfen lisans anahtarınızı girin.", False

        hwid = SecurityManager.get_hwid()
        payload = {
            "license_key": key,
            "hwid": hwid,
            "version": CLIENT_VERSION
        }

        try:
            res = requests.post(f"{SecurityManager.SERVER_URL}/api/auth", json=payload, timeout=5)
            print(f"[DEBUG SUNUCU YANITI] HTTP Kodu: {res.status_code} | Yanıt: {res.text}")
            
            if res.status_code == 200:
                data = res.json()
                
                # SUNUCU GÜNCELLEME İSTEDİ Mİ?
                if data.get("status") == "update_required":
                    new_ver = data.get("latest_version", "Yeni Sürüm")
                    return False, new_ver, True
                
                SecurityManager.save_license(key)
                return True, data.get("expire_date", "Aktif"), False
            elif res.status_code == 426:
                detail = res.json().get("detail", "")
                new_ver = detail.split("|")[1] if "|" in detail else "Yeni Sürüm"
                return False, new_ver, True
            else:
                detail = res.json().get("detail", "Geçersiz Lisans!")
                return False, detail, False

        except requests.exceptions.RequestException as e:
            print(f"[DEBUG HATA] Sunucuya bağlanamadı: {e}")
            return False, "Sunucuya bağlanılamadı! İnternetinizi kontrol edin.", False

    @staticmethod
    def save_license(key):
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                f.write(key.strip())
        except Exception:
            pass