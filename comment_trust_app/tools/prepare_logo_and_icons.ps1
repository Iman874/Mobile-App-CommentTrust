# Compress logo and generate launcher icons for Comment Trust
# Usage:
# 1) Copy your high-quality logo image to assets/images/logo.png
# 2) Run this script in PowerShell in the project root: `.	ools\prepare_logo_and_icons.ps1`
# Requirements (choose one):
# - ImageMagick (magick)
# - pngquant
# - flutter_launcher_icons (listed as a dev_dependency in pubspec.yaml)

param(
    [string]$source = "assets/logo/logo_commenttrust.png",
    [string]$out = "assets/logo/logo_commenttrust_optimized.png",
    [int]$pngquantQualityMin = 60,
    [int]$pngquantQualityMax = 80
)

if (!(Test-Path $source)) {
    Write-Error "Source logo not found at $source. Place your logo file there first."; exit 2
}

# Try pngquant first
if (Get-Command pngquant -ErrorAction SilentlyContinue) {
    Write-Host "Compressing with pngquant..."
    pngquant --quality=${pngquantQualityMin}-${pngquantQualityMax} --output $out --force "$source"
} elseif (Get-Command magick -ErrorAction SilentlyContinue) {
    Write-Host "Compressing with ImageMagick (magick)..."
    magick convert "$source" -strip -quality 85 "$out"
} else {
    Write-Warning "No pngquant or ImageMagick (magick) found; copying original to $out without compression.\nInstall pngquant or ImageMagick for better compression.";
    Copy-Item $source $out -Force
}

# Replace the source with optimized version
Move-Item -Force $out $source

Write-Host "Optimized logo prepared at $source"

Write-Host "Now run:
  flutter pub get
  flutter pub run flutter_launcher_icons:main
This will generate platform launcher icons from $source using the configuration in pubspec.yaml."
