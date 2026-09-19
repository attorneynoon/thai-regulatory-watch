import hashlib
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_url(url):
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Only public HTTPS URLs without credentials or custom ports are allowed")
    if any(ord(c) < 32 for c in url) or "\\" in url:
        raise ValueError("Unsafe URL characters")
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit(("https", p.hostname.lower(), p.path or "/", urlencode(query), ""))


MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
SHORT_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def parse_date(raw):
    """Return an explicit date/date-time; never invent a timezone or a date."""
    if not raw:
        return None
    s = str(raw).strip().translate(str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789"))
    original_s = s
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.isoformat() if dt.tzinfo else dt.date().isoformat()
    except ValueError:
        pass
    for i, names in enumerate(zip(MONTHS, SHORT_MONTHS), 1):
        for name in names:
            s = s.replace(name, str(i))
    for i,name in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],1):
        s=re.sub(r'\b'+name+r'\b',str(i),s,flags=re.I)
    match = re.fullmatch(r"\s*(\d{1,2})[ /.-]+(\d{1,2})[ /.-]+(?:พ.ศ.\s*)?(\d{4})\s*", s)
    if match:
        day, month, year = map(int, match.groups())
        try:
            return datetime(year - 543 if year > 2400 else year, month, day).date().isoformat()
        except ValueError:
            return None
    try:
        dt = parsedate_to_datetime(original_s)
        return dt.isoformat() if dt.tzinfo else dt.date().isoformat()
    except (ValueError, TypeError):
        return None


def clean_text(text):
    return " ".join(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text)).split())
