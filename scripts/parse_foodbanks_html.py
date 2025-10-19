# scripts/parse_foodbanks_and_details.py
"""
Parse public/foodbanks/foodbanks.html and its local detail pages in
public/foodbanks/*.html. Produce normalized JSON files in data/normalized/.
"""

import re
import json
import uuid
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

ROOT = Path.cwd()
SRC_MAIN = ROOT / "public" / "foodbanks" / "foodbanks.html"
DETAILS_DIR = ROOT / "public" / "foodbanks"
OUT_DIR = ROOT / "data" / "normalized"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
CAPACITY_MEALS_RE = re.compile(r"([\d,]+)\s*meals", re.I)

URGENCY_MAP = {
    "very high": "very_high",
    "very_high": "very_high",
    "high": "high",
    "medium": "medium",
    "med": "medium",
    "low": "low",
    "unknown": "unknown"
}

def make_id(prefix, name):
    safe = re.sub(r"[^a-z0-9\-]+", "-", name.lower().strip())
    safe = re.sub(r"-+", "-", safe).strip("-")
    return f"{prefix}:{safe}-{uuid.uuid4().hex[:8]}"

def canonicalize_urgency(raw):
    if not raw:
        return "unknown"
    s = raw.strip().lower()
    s = s.replace("_", " ").replace("-", " ")
    return URGENCY_MAP.get(s, "unknown")

def parse_lat_lng_from_maps_src(src):
    if not src:
        return None, None
    m2 = re.search(r"!2d([-0-9\.]+)!3d([-0-9\.]+)", src)
    if m2:
        lng = float(m2.group(1))
        lat = float(m2.group(2))
        return lat, lng
    m3 = re.search(r"!3d([-0-9\.]+)!2d([-0-9\.]+)", src)
    if m3:
        lat = float(m3.group(1))
        lng = float(m3.group(2))
        return lat, lng
    mq = re.search(r"[?&]q=([-0-9\.]+),([-0-9\.]+)", src)
    if mq:
        return float(mq.group(1)), float(mq.group(2))
    return None, None

def extract_card_fields(card_soup):
    data = {}
    h5 = card_soup.select_one(".card-title")
    data["name"] = h5.get_text(strip=True) if h5 else "Unknown"

    p = card_soup.select_one(".card-text")
    text_lines = []
    if p:
        for br in p.find_all("br"):
            br.replace_with("\n")
        text = p.get_text("\n", strip=True)
        text_lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in text_lines:
        low = line.lower()
        if low.startswith("address:"):
            data["address"] = line.split(":",1)[1].strip()
        elif low.startswith("city:"):
            data["city"] = line.split(":",1)[1].strip()
        elif low.startswith("zip") or low.startswith("zip code:"):
            data["zip"] = line.split(":",1)[1].strip() if ":" in line else line.split()[-1]
        elif low.startswith("capacity:"):
            raw = line.split(":",1)[1].strip()
            data["capacity_raw"] = raw
            m = CAPACITY_MEALS_RE.search(raw.replace("~",""))
            if m:
                try:
                    data["meals_per_week"] = int(m.group(1).replace(",",""))
                except Exception:
                    data["meals_per_week"] = None
        elif low.startswith("hours:"):
            data["hours"] = line.split(":",1)[1].strip()
        elif low.startswith("urgency:"):
            data["urgency"] = line.split(":",1)[1].strip()

    # details link (relative)
    a = card_soup.find("a", href=True, string=re.compile(r"View Details", re.I))
    if a:
        data["details_link"] = a["href"]

    iframe = card_soup.find("iframe")
    if iframe and iframe.get("src"):
        data["map_src"] = iframe.get("src")
        lat, lng = parse_lat_lng_from_maps_src(data["map_src"])
        if lat is not None and lng is not None:
            data["lat"] = lat
            data["lng"] = lng

    return data

def read_detail_page(relative_href):
    if not relative_href:
        return None, None
    href = relative_href.split("#")[0].split("?")[0]
    candidate = DETAILS_DIR / href
    if candidate.exists():
        html = candidate.read_text(encoding="utf-8")
        return html, candidate
    candidate2 = SRC_MAIN.parent / href
    if candidate2.exists():
        html = candidate2.read_text(encoding="utf-8")
        return html, candidate2
    candidate3 = ROOT / href
    if candidate3.exists():
        html = candidate3.read_text(encoding="utf-8")
        return html, candidate3
    return None, None

def parse_detail_fields(html):
    """Return dict with phone, email, images[], programs[], description"""
    out = {"phone": None, "email": None, "images": [], "programs": [], "description": None, "website": None}
    if not html:
        return out
    soup = BeautifulSoup(html, "lxml")
    tel = soup.find("a", href=lambda x: x and x.startswith("tel:"))
    if tel:
        out["phone"] = tel.get_text(strip=True)
    else:
        txt = soup.get_text(" ", strip=True)
        m = PHONE_RE.search(txt)
        if m:
            out["phone"] = m.group(0)

    mail = soup.find("a", href=lambda x: x and x.startswith("mailto:"))
    if mail:
        out["email"] = mail.get("href").split(":",1)[1].split("?")[0]
    else:
        m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", txt)
        if m:
            out["email"] = m.group(0)

    imgs = soup.select("img")
    for img in imgs:
        src = img.get("src")
        if src:
            out["images"].append(src)

    site = soup.find("a", href=lambda x: x and x.startswith("http"))
    if site:
        out["website"] = site.get("href")

    for header in soup.find_all(re.compile("^h[1-6]$")):
        htxt = header.get_text(" ", strip=True).lower()
        if "program" in htxt or "service" in htxt or "volunteer" in htxt:
            next_el = header.find_next_sibling()
            if next_el:
                if next_el.name in ("ul","ol"):
                    items = [li.get_text(" ", strip=True) for li in next_el.find_all("li")]
                    out["programs"].extend(items)
                elif next_el.name == "p":
                    out["programs"].append(next_el.get_text(" ", strip=True))
    lists = soup.select("ul.programs, ul#programs, div.programs ul")
    for l in lists:
        out["programs"].extend([li.get_text(" ", strip=True) for li in l.find_all("li")])

    p = soup.find("p")
    if p:
        out["description"] = p.get_text(" ", strip=True)

    return out

def normalize_sponsor(raw_attrs: dict, detail_meta: dict, detail_path):
    name = (raw_attrs.get("name") or "Unnamed Sponsor").strip()
    sid = stable_id(name)

    # contribution amount: try to coerce numeric, else keep original or None
    contrib_raw = (raw_attrs.get("contribution_amt") or "").strip()
    contrib_amt = None
    if contrib_raw and contrib_raw.upper() not in ("N/A", "NONE", "-", ""):
        # remove commas, currency symbols etc.
        numeric = re.sub(r"[^\d\-]+", "", contrib_raw)
        try:
            contrib_amt = int(numeric) if numeric else None
        except Exception:
            contrib_amt = contrib_raw

    contribution_unit = raw_attrs.get("contribution_unit")
    contribution = raw_attrs.get("contribution")
    affiliation = raw_attrs.get("affiliation")
    past_involvement = raw_attrs.get("past_inv") or raw_attrs.get("past_involvement")

    sponsor_page = raw_attrs.get("sponsor_page") or None

    # collect images from the sponsor-card plus detail page, dedupe while preserving order
    media_images = []
    maybe_imgs = []
    if raw_attrs.get("sponsor_img"):
        maybe_imgs.append(raw_attrs.get("sponsor_img"))
    maybe_imgs.extend(detail_meta.get("images", []) or [])
    seen_imgs = set()
    for u in maybe_imgs:
        if not u:
            continue
        u_str = u.strip()
        if u_str not in seen_imgs:
            seen_imgs.add(u_str)
            media_images.append(u_str)

    # clean description: collapse whitespace/newlines
    desc = detail_meta.get("description") or None
    if isinstance(desc, str):
        # collapse runs of whitespace to single space, and strip
        desc_clean = re.sub(r"\s+", " ", desc).strip()
    else:
        desc_clean = None

    # choose website: prefer absolute detail_meta website, else keep sponsor_page (relative)
    website = detail_meta.get("website") or sponsor_page

    canonical = {
        "id": sid,
        "model_type": "sponsor",
        "name": name,
        "contribution": contribution,
        "contribution_amt": contrib_amt,
        "contribution_unit": contribution_unit,
        "affiliation": affiliation,
        "past_involvement": past_involvement,
        "sponsor_page": sponsor_page,
        "contact": {
            "phone": detail_meta.get("phone"),
            "email": detail_meta.get("email"),
            "website": website
        },
        "media": {
            "images": media_images
        },
        "description": desc_clean,
        "raw_source": {
            "url": str(SRC_MAIN),
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "source_id": str(detail_path) if detail_path else None
        }
    }
    return canonical

def main():
    if not SRC_MAIN.exists():
        print(f"ERROR: {SRC_MAIN} not found. Run script from repo root.")
        return

    html = SRC_MAIN.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    cards = soup.select(".row.g-4 .card")
    if not cards:
        print("No cards found.")
        return

    written = []
    for card in cards:
        raw = extract_card_fields(card)
        details_href = raw.get("details_link")
        detail_html, detail_path = read_detail_page(details_href) if details_href else (None, None)
        detail_meta = parse_detail_fields(detail_html) if detail_html else {"phone":None,"email":None,"images":[], "programs":[], "description": None, "website": None}
        normalized = normalize_foodbank(raw, detail_meta, detail_path)
        out_path = OUT_DIR / f"{normalized['id'].replace(':','_')}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2)
        print("WROTE:", out_path)
        written.append(out_path)

    print(f"\nWrote {len(written)} normalized JSON files to {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
