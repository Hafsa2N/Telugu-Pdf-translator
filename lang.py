import argparse
import re
from pathlib import Path


def import_package(name, pip_name=None):
    try:
        return __import__(name)
    except ModuleNotFoundError as error:
        package = pip_name or name
        raise RuntimeError(
            f"Missing Python package '{package}'. Install it with: pip install {package}"
        ) from error


def is_telugu_text(text, min_telugu_chars=20, min_ratio=0.05):
    telugu_chars = sum(1 for ch in text if "\u0C00" <= ch <= "\u0C7F")
    if telugu_chars < min_telugu_chars:
        return False
    return telugu_chars / max(1, len(text)) >= min_ratio or telugu_chars >= min_telugu_chars


def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return text.strip()


def extract_text_txt(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def extract_text_docx(path):
    docx = import_package("docx", pip_name="python-docx")
    document = docx.Document(path)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_pdfplumber(path):
    pdfplumber = import_package("pdfplumber")
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_images(path, ocr_lang="tel"):
    pdf2image = import_package("pdf2image")
    pytesseract = import_package("pytesseract")
    from PIL import Image

    path = Path(path)
    images = []
    if path.suffix.lower() == ".pdf":
        try:
            images = pdf2image.convert_from_path(path, dpi=300)
        except Exception as error:
            raise RuntimeError(
                "Could not convert PDF to images. Install Poppler and ensure it is on your PATH."
            ) from error
    else:
        images = [Image.open(path)]

    lines = []
    for idx, image in enumerate(images, start=1):
        print(f"  OCR page {idx}/{len(images)}...")
        try:
            page_text = pytesseract.image_to_string(image, lang=ocr_lang)
        except AttributeError:
            raise RuntimeError(
                "pytesseract is installed but did not expose image_to_string."
            )
        except pytesseract.pytesseract.TesseractNotFoundError as error:
            raise RuntimeError(
                "Tesseract binary not found. Install Tesseract OCR and ensure it is on your PATH."
            ) from error
        lines.append(page_text)
    return "\n".join(lines)


def chunk_text(text, max_chars=1000):
    sentences = re.split(r"(?<=[।!?\n])\s+", text)
    chunks = []
    current = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current_len + len(sentence) + 1 <= max_chars:
            current.append(sentence)
            current_len += len(sentence) + 1
            continue

        if current:
            chunks.append(" ".join(current))

        if len(sentence) <= max_chars:
            current = [sentence]
            current_len = len(sentence) + 1
        else:
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i : i + max_chars])
            current = []
            current_len = 0

    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


def translate_text(text, target="en", source=None, chunk_size=1000):
    deep_translator = import_package("deep_translator", pip_name="deep-translator")
    GoogleTranslator = deep_translator.GoogleTranslator
    source_lang = source if source else ("te" if is_telugu_text(text) else "auto")
    translator = GoogleTranslator(source=source_lang, target=target)

    chunks = chunk_text(text, chunk_size)
    translated_chunks = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        try:
            result = translator.translate(chunk)
            translated_chunks.append(result)
            print(f"Translated chunk {idx}/{total}")
        except Exception as error:
            print(f"Translation error on chunk {idx}: {error}")
            translated_chunks.append(chunk)
    return "\n\n".join(translated_chunks)


def load_text(input_path, force_ocr=False, ocr_lang="tel"):
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input path not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".txt":
        text = extract_text_txt(path)
    elif suffix == ".docx":
        text = extract_text_docx(path)
    elif suffix == ".pdf":
        if force_ocr:
            print("Forcing OCR on PDF...")
            text = extract_text_images(path, ocr_lang=ocr_lang)
        else:
            print("Trying PDF text extraction first...")
            try:
                text = extract_text_pdfplumber(path)
            except RuntimeError as error:
                print(f"  PDF text extraction failed: {error}")
                text = ""
            if not text or not is_telugu_text(text):
                print("  Falling back to OCR for PDF.")
                text = extract_text_images(path, ocr_lang=ocr_lang)
    elif suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        text = extract_text_images(path, ocr_lang=ocr_lang)
    else:
        raise RuntimeError(
            "Unsupported input format. Supported: .txt, .docx, .pdf, .png, .jpg, .jpeg, .tif, .tiff, .bmp"
        )

    return normalize_text(text)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Translate Telugu documents to English with OCR fallback and better extraction."
    )
    parser.add_argument("input", help="Input document path")
    parser.add_argument("output", help="Output text file path")
    parser.add_argument("--target", default="en", help="Target language code (default: en)")
    parser.add_argument(
        "--source",
        default=None,
        help="Source language code (default: auto detect Telugu if possible)",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR on PDF/image input instead of direct text extraction",
    )
    parser.add_argument(
        "--ocr-lang",
        default="tel",
        help="OCR language code for Tesseract (default: tel)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Maximum characters per translation chunk",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        source_text = load_text(args.input, force_ocr=args.force_ocr, ocr_lang=args.ocr_lang)
    except Exception as error:
        print(f"Extraction failed: {error}")
        return

    if not source_text.strip():
        print("No text could be extracted from the input document.")
        return

    if args.source is None and not is_telugu_text(source_text):
        print(
            "Warning: extracted text does not look like Telugu script. "
            "Using auto-detection for translation."
        )

    print("Translating text...")
    try:
        translated_text = translate_text(
            source_text,
            target=args.target,
            source=args.source,
            chunk_size=args.chunk_size,
        )
    except Exception as error:
        print(f"Translation failed: {error}")
        return

    Path(args.output).write_text(translated_text, encoding="utf-8")
    print(f"Done! Translation saved to {args.output}")


if __name__ == "__main__":
    main()
