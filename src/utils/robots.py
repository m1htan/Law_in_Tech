import urllib.robotparser as rp
from functools import lru_cache

@lru_cache(maxsize=256)
def _get_parser(root: str):
    p = rp.RobotFileParser()
    p.set_url(root.rstrip("/") + "/robots.txt")
    try:
        p.read()
    except:
        pass
    return p

def can_fetch(url: str, ua="*") -> bool:
    import re
    m = re.match(r"^(https?://[^/]+)/", url)
    if not m: return True
    root = m.group(1)
    parser = _get_parser(root)
    try:
        return parser.can_fetch(ua, url)
    except:
        return True
