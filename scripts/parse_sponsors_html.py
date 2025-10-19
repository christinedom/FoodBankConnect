# scripts/parse_sponsors_html.py
"""
Parse public/sponsors/sponsors.html (local file), extract <sponsor-card> custom elements,
follow local sponsor detail pages if present, and write normalized JSON files to
data/normalized/.

Run from repo root:
    python3 scripts/parse_sponsors_html.py
"""
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

ROOT = Path.cwd()
SRC_MAIN = ROOT / "public" / "sponsors" / "sponsors.html"
DETAILS_DIR = ROOT / "public" / "sponsors"
OUT_DIR = ROOT / "data" / "normalized"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "sponsor"

def stable_id(name: str) -> str:
    s = slugify(name)
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    return f"sponsor:{s}-{h}"

def read_detail_page(relative_href):
    """Return (html, Path) or (None, None) if not found."""
    if not relative_href:
        return None, None
    href = str(relative_href).split("#")[0].split("?")[0]
    candidate = DETAILS_DIR / href
    if candidate.exists():
        return candidate.read_text(encoding="utf-8"), candidate
    candidate2 = SRC_MAIN.parent / href
    if candidate2.exists():
        return candidate2.read_text(encoding="utf-8"), candidate2
    candidate3 = ROOT / href
    if candidate3.exists():
        return candidate3.read_text(encoding="utf-8"), candidate3
    return None, None

def parse_detail_fields(html):
    """Extract phone, email, images, description, website from a sponsor detail page."""
    out = {"phone": None, "email": None, "images": [], "description": None, "website": None}
    if not html:
        return out
    soup = BeautifulSoup(html, "lxml")
    # phone
    tel = soup.find("a", href=lambda x: x and x.startswith("tel:"))
    if tel:
        out["phone"] = tel.get_text(strip=True)
    else:
        m = PHONE_RE.search(soup.get_text(" ", strip=True))
        if m:
            out["phone"] = m.group(0)
    # email
    mail = soup.find("a", href=lambda x: x and x.startswith("mailto:"))
    if mail:
        out["email"] = mail.get("href").split(":",1)[1].split("?")[0]
    else:
        m2 = EMAIL_RE.search(soup.get_text(" ", strip=True))
        if m2:
            out["email"] = m2.group(0)
    # images
    for img in soup.select("img"):
        src = img.get("src")
        if src:
            out["images"].append(src)
    # website (first http(s) absolute link)
    site = soup.find("a", href=lambda x: x and x.startswith("http"))
    if site:
        out["website"] = site.get("href")
    # description: take first meaningful paragraph
    p = soup.find("p")
    if p:
        out["description"] = p.get_text(" ", strip=True)
    return out

def normalize_sponsor(raw_attrs: dict, detail_meta: dict, detail_path):
    name = raw_attrs.get("name") or "Unnamed Sponsor"
    sid = stable_id(name)
    contribution = raw_attrs.get("contribution")
    contribution_amt = raw_attrs.get("contribution_amt")
    contribution_unit = raw_attrs.get("contribution_unit")
    affiliation = raw_attrs.get("affiliation")
    past_involvement = raw_attrs.get("past_inv") or raw_attrs.get("past_involvement")
    sponsor_page = raw_attrs.get("sponsor_page")
    media_images = []
    if raw_attrs.get("sponsor_img"):
        media_images.append(raw_attrs.get("sponsor_img"))
    media_images.extend(detail_meta.get("images", []))

    canonical = {
        "id": sid,
        "model_type": "sponsor",
        "name": name,
        "contribution": contribution,
        "contribution_amt": contribution_amt,
        "contribution_unit": contribution_unit,
        "affiliation": affiliation,
        "past_involvement": past_involvement,
        "sponsor_page": sponsor_page,
        "contact": {
            "phone": detail_meta.get("phone"),
            "email": detail_meta.get("email"),
            "website": detail_meta.get("website") or sponsor_page
        },
        "media": {
            "images": media_images
        },
        "description": detail_meta.get("description"),
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

    # Find all sponsor-card custom elements
    sponsor_elems = soup.find_all("sponsor-card")
    if not sponsor_elems:
        # fallback: some builds might inlined <div class="sponsor-card">, try that
        sponsor_elems = soup.select(".sponsor-card")
    if not sponsor_elems:
        print("No sponsor-card elements found in sponsors.html")
        return

    seen_names = set()
    written = []

    for elem in sponsor_elems:
        # attributes are available via .attrs or elem.get()
        raw = {k: elem.get(k) for k in elem.attrs.keys()}

        # dedupe by name (case-insensitive)
        name = (raw.get("name") or "").strip()
        if not name:
            # fallback: skip unnamed sponsor
            continue
        name_key = name.lower()
        if name_key in seen_names:
            # skip duplicate
            continue
        seen_names.add(name_key)

        # attempt to read detail page (relative)
        detail_html, detail_path = read_detail_page(raw.get("sponsor_page"))
        detail_meta = parse_detail_fields(detail_html) if detail_html else {"phone":None,"email":None,"images":[], "description": None, "website": None}

        normalized = normalize_sponsor(raw, detail_meta, detail_path)

        # write file (use id-based filename)
        safe_fname = normalized["id"].replace(":", "_")
        out_path = OUT_DIR / f"{safe_fname}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2)
        written.append(out_path)
        print("WROTE:", out_path)

    print(f"\nWrote {len(written)} sponsor JSON files to {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
