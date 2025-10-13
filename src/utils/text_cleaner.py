import re

HEADER_FOOTER_RE = re.compile(r"(Trang\s+\d+\/\d+)|(^\s*—\s*$)", re.MULTILINE)

def strip_headers(text: str) -> str:
    return re.sub(HEADER_FOOTER_RE, "", text).strip()
