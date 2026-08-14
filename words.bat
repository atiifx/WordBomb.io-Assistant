@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "WB_SELF=%~f0"
set "WB_ROOT=%~dp0"

echo ==========================================
echo Turkce kelime listesi duzeltiliyor...
echo Klasor: %cd%
echo ==========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $content=[System.IO.File]::ReadAllText($env:WB_SELF,[System.Text.Encoding]::UTF8); $parts=$content -split '(?m)^# POWERSHELL_SCRIPT_START\s*$',2; if($parts.Count -lt 2){throw 'PowerShell bolumu bulunamadi.'}; Invoke-Expression $parts[1]"

set "RESULT=%ERRORLEVEL%"

echo.
echo ==========================================
if "%RESULT%"=="0" (
    echo Islem bitti.
) else (
    echo Islem hatayla bitti. Kod: %RESULT%
)
echo ==========================================
pause
exit /b %RESULT%

# POWERSHELL_SCRIPT_START

$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$root = (Resolve-Path $env:WB_ROOT).Path
$data = Join-Path $root "data"
$path = Join-Path $data "words_tr.txt"

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$trCulture = [System.Globalization.CultureInfo]::GetCultureInfo("tr-TR")

function Normalize-Word {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return ""
    }

    $word = $Text.Trim()

    # Gizli karakterleri temizle
    $word = $word -replace "[\u200B-\u200D\uFEFF\u00AD]", ""

    # Unicode normalize
    $word = $word.Normalize([System.Text.NormalizationForm]::FormC)

    # Türkçe lower
    $word = $word.ToLower($trCulture)

    # Şapkalı (Düzeltme işaretli) harfleri normale çevir
    $word = $word -replace "[âÂ]", "a"
    $word = $word -replace "[îÎ]", "i"
    $word = $word -replace "[ûÛ]", "u"

    # Fazla boşlukları teke indir
    $word = $word -replace "\s+", " "

    return $word.Trim()
}

$fix = [ordered]@{}

# =========================
# Bariz yazım / eksik harf
# =========================
$fix["ballandırmk"] = "ballandırmak"
$fix["ektirmeek"] = "ektirmek"
$fix["hıcıv"] = "hiciv"
$fix["eips"] = "cips"

# =========================
# Bozuk i / ı düzeltmeleri
# =========================
$fix["temerrüt faızı"] = "temerrüt faizi"

$fix["dıplomatık"] = "diplomatik"
$fix["dıplomasız"] = "diplomasız"

$fix["bır göz"] = "bir göz"
$fix["göz memesı"] = "göz memesi"
$fix["değışmez"] = "değişmez"
$fix["ıktısat"] = "iktisat"
$fix["satanızm"] = "satanizm"

$fix["organık"] = "organik"
$fix["gazıno"] = "gazino"
$fix["cazıbe"] = "cazibe"

$fix["fuzulı"] = "fuzuli"
$fix["kuzu etı"] = "kuzu eti"
$fix["balıketı"] = "balıketi"

$fix["bılge"] = "bilge"
$fix["belgecı"] = "belgeci"
$fix["sılgeç"] = "silgeç"

$fix["devrı"] = "devri"
$fix["adlıye"] = "adliye"
$fix["evlıya"] = "evliya"
$fix["malıye"] = "maliye"
$fix["naklıye"] = "nakliye"
$fix["baklıyat"] = "bakliyat"
$fix["tahlıye"] = "tahliye"
$fix["faalıyet"] = "faaliyet"

$fix["ezgılı"] = "ezgili"
$fix["ılgılı"] = "ilgili"
$fix["gergılı"] = "gergili"
$fix["belgılı"] = "belgili"
$fix["bılgılı"] = "bilgili"

$fix["ekolojı"] = "ekoloji"
$fix["bıyolojı"] = "biyoloji"
$fix["nörolojı"] = "nöroloji"
$fix["lojıstık"] = "lojistik"
$fix["onkolojı"] = "onkoloji"
$fix["arkeolojı"] = "arkeoloji"
$fix["sosyolojı"] = "sosyoloji"
$fix["teknolojı"] = "teknoloji"

$fix["emır"] = "emir"
$fix["emzırmek"] = "emzirmek"

$fix["cumayerı"] = "cumayeri"
$fix["cumartesı"] = "cumartesi"
$fix["cumhurıyet"] = "cumhuriyet"
$fix["cumhur reısı"] = "cumhur reisi"

$fix["şıfa"] = "şifa"
$fix["şıke"] = "şike"
$fix["şışe"] = "şişe"
$fix["şıfre"] = "şifre"
$fix["şışko"] = "şişko"
$fix["şışme"] = "şişme"
$fix["şıddet"] = "şiddet"
$fix["şırın"] = "şirin"
$fix["şımşek"] = "şimşek"
$fix["şıfrelı"] = "şifreli"

$fix["kendı"] = "kendi"
$fix["kenevır"] = "kenevir"
$fix["kendınce"] = "kendince"

$fix["mıde"] = "mide"
$fix["mıyav"] = "miyav"
$fix["mılıtan"] = "militan"
$fix["mınıbüs"] = "minibüs"
$fix["mıkropsuz"] = "mikropsuz"
$fix["mıllettaş"] = "millettaş"
$fix["mılyarder"] = "milyarder"
$fix["mılyarlık"] = "milyarlık"
$fix["mılyonluk"] = "milyonluk"
$fix["mımarbaşı"] = "mimarbaşı"

$fix["endışe"] = "endişe"

$fix["ıkaz"] = "ikaz"
$fix["ıkna"] = "ikna"
$fix["ıkon"] = "ikon"
$fix["ıklım"] = "iklim"
$fix["ıkbal"] = "ikbal"
$fix["ıkıleme"] = "ikileme"
$fix["ıkıncıl"] = "ikincil"

$fix["ızleme"] = "izleme"
$fix["ızlenme"] = "izlenme"
$fix["ızletme"] = "izletme"

$fix["öncelık"] = "öncelik"
$fix["ön seçım"] = "ön seçim"
$fix["ön lısans"] = "ön lisans"

$fix["çılek"] = "çilek"
$fix["çıllı"] = "çilli"
$fix["çıl-çıl"] = "çıl çıl"

$fix["ırtıbatlı"] = "irtibatlı"
$fix["ırtıbatsız"] = "irtibatsız"
$fix["ırtıbatsızlık"] = "irtibatsızlık"
$fix["ırtıfak-hakkı"] = "irtifak hakkı"
$fix["ıdıl"] = "idil"

$fix["pıton"] = "piton"
$fix["aspırın"] = "aspirin"
$fix["jüpıter"] = "jüpiter"
$fix["kelepır"] = "kelepir"

# =========================
# Çevre / çevrim tarzı barizler
# =========================
$fix["cevre"] = "çevre"
$fix["cevrim"] = "çevrim"

if (!(Test-Path -LiteralPath $path)) {
    throw "words_tr.txt bulunamadi: $path"
}

$backup = "$path.backup"
$report = "$path.fixed_report.txt"
$removedReport = "$path.removed_duplicates.txt"

Copy-Item -LiteralPath $path -Destination $backup -Force

$oldLines = [System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::UTF8)

$seen = [System.Collections.Generic.HashSet[string]]::new()
$clean = [System.Collections.Generic.List[string]]::new()
$removed = [System.Collections.Generic.List[string]]::new()
$fixedReport = [System.Collections.Generic.List[string]]::new()

foreach ($line in $oldLines) {
    $word = Normalize-Word $line

    if ([string]::IsNullOrWhiteSpace($word)) {
        continue
    }

    $originalWord = $word

    if ($fix.Contains($word)) {
        $word = $fix[$word]
        $word = Normalize-Word $word

        if ($originalWord -ne $word) {
            [void]$fixedReport.Add("$originalWord -> $word")
        }
    }

    if ([string]::IsNullOrWhiteSpace($word)) {
        continue
    }

    if ($seen.Add($word)) {
        [void]$clean.Add($word)
    } else {
        [void]$removed.Add($word)
    }
}

[System.IO.File]::WriteAllLines($path, [string[]]$clean, $utf8NoBom)
[System.IO.File]::WriteAllLines($report, [string[]]$fixedReport, $utf8NoBom)
[System.IO.File]::WriteAllLines($removedReport, [string[]]$removed, $utf8NoBom)

Write-Host "[TEMIZLENDI] $path"
Write-Host ("Eski satir: {0}" -f $oldLines.Count)
Write-Host ("Yeni satir: {0}" -f $clean.Count)
Write-Host ("Duzeltilen kelime: {0}" -f $fixedReport.Count)
Write-Host ("Silinen tekrar: {0}" -f $removed.Count)
Write-Host "Yedek: $backup"
Write-Host "Duzeltme raporu: $report"
Write-Host "Silinen tekrar raporu: $removedReport"