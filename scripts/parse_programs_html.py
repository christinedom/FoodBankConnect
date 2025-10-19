# scripts/parse_programs_html.py  
import re
import json
import uuid
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

ROOT = Path.cwd()
SRC_MAIN = ROOT / "public" / "programs" / "programs.html"
DETAILS_DIR = ROOT / "public" / "programs"
OUT_DIR = ROOT / "data" / "normalized"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

TYPE_MAP = {
    "distribution": "distribution",
    "Distribution": "distribution",
    "Volunteer": "volunteer",
    "Class": "class",
    "Training": "class",
    "Service": "service",
    "training": "class",
    "service": "service",
    "volunteer": "volunteer"
}

def make_id(prefix, name):
    safe = re.sub(r"[^a-z0-9\-]+", "-", name.lower().strip())
    safe = re.sub(r"-+", "-", safe).strip("-")
    return f"{prefix}:{safe}-{uuid.uuid4().hex[:8]}"

def read_detail_page(relative_href):
    if not relative_href:
        return None, None
    href = relative_href.split("#")[0].split("?")[0]
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
    out = {"phone": None, "email": None, "images": [], "description": None, "schedule": None, "website": None}
    if not html:
        return out
    soup = BeautifulSoup(html, "lxml")
    tel = soup.find("a", href=lambda x: x and x.startswith("tel:"))
    if tel:
        out["phone"] = tel.get_text(strip=True)
    else:
        text = soup.get_text(" ", strip=True)
        m = PHONE_RE.search(text)
        if m:
            out["phone"] = m.group(0)
    mail = soup.find("a", href=lambda x: x and x.startswith("mailto:"))
    if mail:
        out["email"] = mail.get("href").split(":",1)[1].split("?")[0]
    else:
        m = EMAIL_RE.search(soup.get_text(" ", strip=True))
        if m:
            out["email"] = m.group(0)
    for img in soup.select("img"):
        src = img.get("src")
        if src:
            out["images"].append(src)
    site = soup.find("a", href=lambda x: x and x.startswith("http"))
    if site:
        out["website"] = site.get("href")
    p = soup.find("p")
    if p:
        out["description"] = p.get_text(" ", strip=True)
    text = soup.get_text("\n", strip=True)
    sched_match = re.search(r"(Schedule|When|Dates|Time|Times):\s*(.+)", text, re.I)
    if sched_match:
        out["schedule"] = sched_match.group(2).strip()
    else:
        m2 = re.search(r"(Weekly|Monthly|Yearly|Every\s+\w+|Ongoing Sessions|By appointment|One[-\s]time)", text, re.I)
        if m2:
            out["schedule"] = m2.group(0)
    return out

def extract_card_fields(card):
    data = {}
    title = card.select_one(".card-title")
    data["name"] = title.get_text(strip=True) if title else "Unnamed Program"
    ancestor = card.find_parent(attrs={"data-type": True})
    if ancestor and ancestor.get("data-type"):
        data["data_type"] = ancestor["data-type"]
    else:
        data["data_type"] = card.get("data-type") or card.get("data_type")
    fields = {}
    for p in card.select("p"):
        txt = p.get_text(" ", strip=True)
        if ":" in txt:
            k, v = [s.strip() for s in txt.split(":", 1)]
            fields[k.lower()] = v
    data["fields"] = fields
    img = card.select_one("img")
    if img and img.get("src"):
        data["image"] = img.get("src")
    a = card.find("a", href=True, string=re.compile(r"(See Details|View Details)", re.I))
    if a:
        data["details_link"] = a["href"]
    return data

def normalize_program(raw, detail_meta, detail_path):
    name = raw.get("name", "Unnamed Program")
    pid = make_id("program", name)
    typ_raw = raw.get("data_type") or raw.get("fields", {}).get("type") or raw.get("fields", {}).get("program type")
    program_type = TYPE_MAP.get(typ_raw, typ_raw.lower() if typ_raw else "unknown")
    eligibility = raw.get("fields", {}).get("eligibility") or None
    frequency = raw.get("fields", {}).get("frequency") or None
    cost = raw.get("fields", {}).get("cost") or None
    host = raw.get("fields", {}).get("host") or None
    media = {"images": []}
    if raw.get("image"):
        media["images"].append(raw.get("image"))
    media["images"].extend(detail_meta.get("images", []))
    canonical = {
        "id": pid,
        "model_type": "program",
        "name": name,
        "program_type": program_type,
        "eligibility": eligibility,
        "frequency": frequency,
        "cost": cost,
        "host": host,
        "schedule": detail_meta.get("schedule"),
        "location": None,
        "contact": {
            "phone": detail_meta.get("phone"),
            "email": detail_meta.get("email"),
            "website": detail_meta.get("website") or raw.get("details_link")
        },
        "media": media,
        "description": detail_meta.get("description"),
        "details_link": raw.get("details_link"),
        "raw_source": {
            "url": str(SRC_MAIN),
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "source_id": str(detail_path) if detail_path else None
        }
    }
    return canonical

def main():
    if not SRC_MAIN.exists():
        print(f"ERROR: {SRC_MAIN} not found. Run from repo root.")
        return

    html = SRC_MAIN.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    # Select only the top-level program containers to avoid double-selecting inner .card
    containers = soup.select("#programCards .program-card")
    if not containers:
        # fallback if markup doesn't use .program-card
        containers = soup.select("#programCards .card")

    seen = set()   # dedupe by details_link or name
    written = []

    for container in containers:
        # find the inner .card element if present
        card = container.select_one(".card") or container
        raw = extract_card_fields(card)
        dedupe_key = (raw.get("details_link") or "").strip() or raw.get("name").strip().lower()
        if not dedupe_key:
            dedupe_key = str(uuid.uuid4())  # fall back to unique key if nothing else

        if dedupe_key in seen:
            # skip duplicate
            continue
        seen.add(dedupe_key)

        details_href = raw.get("details_link")
        detail_html, detail_path = read_detail_page(details_href) if details_href else (None, None)
        detail_meta = parse_detail_fields(detail_html) if detail_html else {"phone":None,"email":None,"images":[], "description": None, "schedule": None, "website": None}
        normalized = normalize_program(raw, detail_meta, detail_path)
        out_path = OUT_DIR / f"{normalized['id'].replace(':','_')}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2)
        print("WROTE:", out_path)
        written.append(out_path)

    print(f"\nWrote {len(written)} program JSON files to {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
