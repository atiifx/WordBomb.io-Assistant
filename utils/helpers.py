import pygetwindow as gw
import time

def focus_platform(platform_name):
    titles = {
        "Google Chrome": "Google Chrome",
        "Discord": "Discord",
        "Discord Canary": "Discord Canary",
        "Discord PTB": "Discord PTB"
    }
    
    target = titles.get(platform_name)
    try:
        window = gw.getWindowsWithTitle(target)[0]
        if window:
            window.activate()
            time.sleep(0.1)
            return True
    except Exception as e:
        print(f"Pencere bulunamadı: {e}")
    return False