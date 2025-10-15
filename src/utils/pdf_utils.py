import os, io, requests, tempfile, subprocess
from pdfminer.high_level import extract_text

def fetch_and_extract_pdf(url: str, out_dir="../../outputs/pdf"):
    os.makedirs(out_dir, exist_ok=True)
    name = url.split("/")[-1].split("?")[0] or "file.pdf"
    local_path = os.path.join(out_dir, name)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(local_path,"wb") as f:
        f.write(r.content)

    # thử text layer
    text = extract_text(local_path) or ""
    if len(text.strip()) < 50:
        # OCR từng trang: pdf2image -> tesseract
        from pdf2image import convert_from_path
        pages = convert_from_path(local_path, dpi=300)
        ocr_txt = []
        import pytesseract
        for pg in pages:
            ocr_txt.append(pytesseract.image_to_string(pg, lang="vie+eng"))
        text = "\n".join(ocr_txt)

    # lưu .txt
    txt_path = local_path.replace(".pdf", ".txt")
    with open(txt_path,"w",encoding="utf-8") as f:
        f.write(text)
    return {"local_path": local_path, "ocr_text_path": txt_path}
