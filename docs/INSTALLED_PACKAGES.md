# Installed Packages & Tools

A complete list of packages and tools installed by the CodeHero.

---

## System Packages

### Core
| Package | Description |
|---------|-------------|
| `python3` | Python 3 interpreter |
| `python3-pip` | Python package manager |
| `git` | Version control |
| `curl`, `wget` | HTTP clients |
| `openssl` | SSL/TLS toolkit |
| `sudo` | Privilege escalation |

### Web Server
| Package | Description |
|---------|-------------|
| `nginx` | High-performance web server |
| `php8.3-fpm` | PHP 8.3 FastCGI Process Manager |
| `php8.3-*` | PHP extensions (mysql, curl, intl, etc.) |

### Database
| Package | Description |
|---------|-------------|
| `mysql-server` | MySQL 8.0 database server |

### JavaScript
| Package | Description |
|---------|-------------|
| `nodejs` | Node.js 22.x runtime |
| `npm` | Node package manager |

---

## Multimedia & Processing Tools

### Image Processing
| Package | Command | Description |
|---------|---------|-------------|
| `imagemagick` | `convert`, `identify` | Image conversion, resize, crop, effects |
| `libvips-tools` | `vips` | Fast image processing for large files |
| `optipng` | `optipng` | PNG optimization |
| `jpegoptim` | `jpegoptim` | JPEG optimization |
| `webp` | `cwebp`, `dwebp` | WebP conversion |
| `librsvg2-bin` | `rsvg-convert` | SVG to PNG/PDF |

### OCR (Optical Character Recognition)
| Package | Command | Description |
|---------|---------|-------------|
| `tesseract-ocr` | `tesseract` | Extract text from images |
| `tesseract-ocr-eng` | - | English language data |
| `tesseract-ocr-ell` | - | Greek language data |

### Audio Processing
| Package | Command | Description |
|---------|---------|-------------|
| `ffmpeg` | `ffmpeg` | Audio/video Swiss Army knife |
| `sox` | `sox`, `soxi` | Sound processing, effects |

### Video Processing
| Package | Command | Description |
|---------|---------|-------------|
| `ffmpeg` | `ffmpeg` | Video conversion, editing, streaming |
| `mediainfo` | `mediainfo` | Media file information |

### PDF Processing
| Package | Command | Description |
|---------|---------|-------------|
| `poppler-utils` | `pdftotext`, `pdftoppm` | PDF to text/images |
| `ghostscript` | `gs` | PDF manipulation, compression |
| `qpdf` | `qpdf` | PDF transformations |

---

## Python Packages

### Web Framework
| Package | Description |
|---------|-------------|
| `flask` | Web framework |
| `flask-socketio` | WebSocket support |
| `flask-cors` | Cross-origin requests |
| `eventlet` | Async networking |

### Database
| Package | Description |
|---------|-------------|
| `mysql-connector-python` | MySQL driver |

### Security
| Package | Description |
|---------|-------------|
| `bcrypt` | Password hashing |

### Testing
| Package | Description |
|---------|-------------|
| `playwright` | Browser automation & testing |

### Image & Multimedia
| Package | Description |
|---------|-------------|
| `Pillow` | Image processing library |
| `opencv-python-headless` | Computer vision (no GUI) |
| `pytesseract` | Python wrapper for Tesseract OCR |
| `pdf2image` | Convert PDF pages to images |
| `pydub` | Audio manipulation |

---

## Usage Examples

### Image Processing

```bash
# Convert format
convert input.png output.jpg

# Resize to 50%
convert input.png -resize 50% output.png

# Optimize PNG
optipng -o7 image.png

# Convert to WebP
cwebp -q 85 input.png -o output.webp
```

### OCR (Image to Text)

```bash
# English
tesseract image.png output -l eng

# Greek
tesseract image.png output -l ell

# Multiple languages
tesseract image.png output -l eng+ell
```

```python
import pytesseract
from PIL import Image

text = pytesseract.image_to_string(
    Image.open('image.png'),
    lang='eng+ell'
)
print(text)
```

### Audio/Video

```bash
# Convert video format
ffmpeg -i input.mp4 output.webm

# Extract audio from video
ffmpeg -i video.mp4 -vn audio.mp3

# Create video thumbnail
ffmpeg -i video.mp4 -ss 00:00:05 -frames:v 1 thumb.jpg

# Resize video
ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4

# Convert audio format
ffmpeg -i input.wav output.mp3

# Audio effects with sox
sox input.wav output.wav reverse
sox input.wav output.wav trim 0 30  # First 30 seconds
```

### PDF Processing

```bash
# PDF to text
pdftotext document.pdf output.txt

# PDF to images (one per page)
pdftoppm -png document.pdf output

# Compress PDF
gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -o compressed.pdf input.pdf

# Rotate PDF pages
qpdf --rotate=90:1-5 input.pdf output.pdf
```

```python
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('document.pdf')
for i, img in enumerate(images):
    img.save(f'page_{i}.png')
```

### Python Image Processing

```python
from PIL import Image
import cv2

# Resize with Pillow
img = Image.open('input.png')
img.thumbnail((800, 600))
img.save('output.jpg')

# OpenCV - read and process
img = cv2.imread('input.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imwrite('gray.png', gray)
```

---

## Verification Commands

```bash
# Check all tools are installed
ffmpeg -version | head -1
convert -version | head -1
tesseract --version | head -1
sox --version 2>&1 | head -1
pdftotext -v 2>&1 | head -1
gs --version
mediainfo --version

# Check Python packages
python3 -c "import PIL; print('Pillow:', PIL.__version__)"
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import pytesseract; print('pytesseract: OK')"
python3 -c "from pdf2image import convert_from_path; print('pdf2image: OK')"
python3 -c "from pydub import AudioSegment; print('pydub: OK')"
```

---

*Last Updated: 2026-01-12*
