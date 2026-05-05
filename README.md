# Telugu Document Translator

A simple Python tool that extracts and translates Telugu text from **PDFs, DOCX, images, and text files** into English (or any target language). Includes intelligent Telugu detection and automatic OCR fallback for scanned documents.

## Features

- ✅ **Multi‑format support** – PDF, DOCX, TXT, PNG, JPG, JPEG, TIFF, BMP
- ✅ **OCR fallback** – If direct text extraction fails, automatically uses Tesseract OCR
- ✅ **Forced OCR mode** – Process scanned PDFs/images with `--force-ocr`
- ✅ **Telugu script detection** – Uses Unicode range to identify Telugu text
- ✅ **Smart chunking** – Sentences are preserved during translation
- ✅ **Command‑line arguments** – Customize source/target language, chunk size, OCR language
- ✅ **Works with Python 3.14+** – Uses `deep-translator` (no `cgi` module issues)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Hafsa2N/Telugu-Pdf-translator.git
cd Telugu-Pdf-translator
```
**How It Works**
Extraction – The script detects the file type and extracts text:
PDFs: tries pdfplumber (for selectable text), falls back to OCR via pytesseract
DOCX: extracts using python-docx
Images: directly applies OCR
TXT: reads UTF‑8 text directly
Telugu detection – Checks Unicode characters \u0C00 to \u0C7F and ensures at least 5% Telugu characters (or 20+ characters).
Chunking – Splits text by sentences (using Telugu punctuation ।, !, ?, newlines) to keep context.
Translation – Uses deep-translator (Google Translate) with chunking to avoid API limits.
Output – Saves the translated text as UTF‑8 plain text.

**Requirements**
pdfplumber
deep-translator
python-docx
pdf2image
pytesseract
Pillow
