#!/bin/bash
# Upgrade to version 2.42.0
# Adds multimedia tools for file processing

log_info() { echo -e "\033[0;36m[2.42.0]\033[0m $1"; }

log_info "Installing multimedia tools..."

# Check and install packages
NEW_PACKAGES=""
command -v ffmpeg >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES ffmpeg"
command -v convert >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES imagemagick"
command -v tesseract >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES tesseract-ocr tesseract-ocr-eng tesseract-ocr-ell"
command -v sox >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES sox"
command -v pdftotext >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES poppler-utils"
command -v gs >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES ghostscript"
command -v mediainfo >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES mediainfo"
command -v cwebp >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES webp"
command -v optipng >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES optipng"
command -v jpegoptim >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES jpegoptim"
command -v rsvg-convert >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES librsvg2-bin"
command -v vips >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES libvips-tools"
command -v qpdf >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES qpdf"

if [ -n "$NEW_PACKAGES" ]; then
    apt-get update -qq
    apt-get install -y $NEW_PACKAGES >/dev/null 2>&1 || true

    # Python packages
    pip3 install --quiet Pillow opencv-python-headless pydub pytesseract pdf2image --break-system-packages 2>/dev/null || \
    pip3 install --quiet Pillow opencv-python-headless pydub pytesseract pdf2image 2>/dev/null || true

    log_info "Multimedia tools installed"
else
    log_info "Multimedia tools already installed"
fi
