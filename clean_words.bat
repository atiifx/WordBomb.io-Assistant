@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "WB_SELF=%~f0"
set "WB_CLEAN_ROOT=%~dp0"

echo ==========================================
echo Kelime listeleri temizleniyor...
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

$root = (Resolve-Path $env:WB_CLEAN_ROOT).Path
$data = Join-Path $root "data"

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

$trCulture = [System.Globalization.CultureInfo]::GetCultureInfo("tr-TR")
$ptCulture = [System.Globalization.CultureInfo]::GetCultureInfo("pt-PT")

function Normalize-Word {
    param(
        [string]$Text,
        [System.Globalization.CultureInfo]$Culture
    )

    $word = $Text.Trim()

    # Gizli karakterleri temizle
    $word = $word -replace "[\u200B-\u200D\uFEFF\u00AD]", ""

    # Unicode karakterleri normalize et
    $word = $word.Normalize([System.Text.NormalizationForm]::FormC)

    if ($null -ne $Culture) {
        $word = $word.ToLower($Culture)
    } else {
        $word = $word.ToLowerInvariant()
    }

    return $word
}

function Clean-WordFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [System.Globalization.CultureInfo]$Culture
    )

    if (!(Test-Path -LiteralPath $Path)) {
        Write-Host "[YOK] $Path"
        return
    }

    $backup = "$Path.backup"
    $removedReport = "$Path.removed_duplicates.txt"

    Copy-Item -LiteralPath $Path -Destination $backup -Force

    $oldLines = [System.IO.File]::ReadAllLines($Path, [System.Text.Encoding]::UTF8)

    $seen = [System.Collections.Generic.HashSet[string]]::new()
    $clean = [System.Collections.Generic.List[string]]::new()
    $removed = [System.Collections.Generic.List[string]]::new()

    foreach ($line in $oldLines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $word = Normalize-Word $line $Culture

        if ([string]::IsNullOrWhiteSpace($word)) {
            continue
        }

        if ($seen.Add($word)) {
            [void]$clean.Add($word)
        } else {
            [void]$removed.Add($word)
        }
    }

    [System.IO.File]::WriteAllLines($Path, [string[]]$clean, $utf8NoBom)
    [System.IO.File]::WriteAllLines($removedReport, [string[]]$removed, $utf8NoBom)

    Write-Host "[TEMIZLENDI] $Path"
    Write-Host ("Eski satir: {0} | Yeni satir: {1} | Silinen tekrar: {2}" -f $oldLines.Count, $clean.Count, $removed.Count)
    Write-Host "Yedek: $backup"
    Write-Host "Silinen tekrar raporu: $removedReport"
    Write-Host ""
}

try {
    Clean-WordFile (Join-Path $data "words_en.txt") $null
    Clean-WordFile (Join-Path $data "words_tr.txt") $trCulture
    Clean-WordFile (Join-Path $data "words_pt.txt") $ptCulture

    Write-Host "Tum dosyalar temizlendi."
}
catch {
    Write-Host ""
    Write-Host "[HATA]"
    Write-Host $_.Exception.Message
    exit 1
}