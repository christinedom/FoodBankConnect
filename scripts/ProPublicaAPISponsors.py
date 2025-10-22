import requests
import json
import time
import re

BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
MAX_RESULTS = 100
KEYWORDS = [
    "foundation",
    "philanthropy",
    "grant",
    "donor",
    "charity",
    "food donation",
    "corporate giving"
]

FOOD_RELATED_KEYWORDS = [
    "food bank",
    "pantry",
    "hunger",
    "meals",
    "feeding",
    "nutrition",
    "soup kitchen",
    "food insecurity"
]

GOOGLE_API_KEY = "AIzaSyCaX5owOlwzJq59MYdCl6lV5BKt3W3K-KE"
GOOGLE_CX = "47dcfe213c7274b68"

def classify_affiliation(name: str, org_detail: dict = None) -> str:
    corp_terms = ["INC", "LLC", "CORP", "COMPANY", "CO.", "LTD", "CORPORATION"]
    if any(term in name.upper() for term in corp_terms):
        return "Private Corporation"
    if org_detail:
        ntype = org_detail.get("organization_type") or org_detail.get("ntee_code") or ""
        if ntype:
            return f"Nonprofit Foundation ({ntype})"
    return "Nonprofit Foundation"

def fetch_grants(ein: str) -> str:
    url = f"{BASE_URL}/organizations/{ein}.json"
    resp = requests.get(url)
    if resp.status_code != 200:
        return "N/A"
    data = resp.json()
    filings = data.get("filings_with_data", [])
    for filing in filings:
        grants = filing.get("grants", [])
        if not grants:
            continue
        for grant in grants:
            recipient = grant.get("recipient_name", "")
            if any(keyword in recipient.lower() for keyword in FOOD_RELATED_KEYWORDS):
                return recipient
        return grants[0].get("recipient_name", "N/A")
    return "N/A"

def fetch_logo(name: str) -> str:
    """Fetch first image URL from Google Custom Search for sponsor logo."""
    if not name:
        return "N/A"

    query = f"{name} logo"
    url = (
        f"https://www.googleapis.com/customsearch/v1?q={query}"
        f"&cx={GOOGLE_CX}&key={GOOGLE_API_KEY}&searchType=image&num=1"
    )
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["link"]
    except Exception as e:
        print(f"Error fetching logo for '{name}': {e}")
    return "N/A"

def fetch_tax_exempt_date(ein: str) -> str:
    """Return 'Tax-exempt since YYYY' from ProPublica EIN page."""
    if not ein:
        return "This is a nonprofit, tax exempt."
    url = f"https://projects.propublica.org/nonprofits/organizations/{ein}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return "This is a nonprofit, tax exempt."
        text = resp.text
        match = re.search(r"Tax-exempt since ([A-Za-z0-9 ,]+)", text)
        if match:
            tax_str = match.group(1)
            if re.search(r"\b\d{4}\b", tax_str):
                return f"Tax-exempt since {tax_str}"
        return "This is a nonprofit, tax exempt."
    except:
        return "This is a nonprofit, tax exempt."

def scrape(max_results=MAX_RESULTS):
    all_results = []
    for keyword in KEYWORDS:
        page = 0
        while len(all_results) < max_results:
            params = {"q": keyword, "page": page}
            response = requests.get(f"{BASE_URL}/search.json", params=params)
            if response.status_code != 200:
                break

            data = response.json()
            orgs = data.get("organizations", [])
            if not orgs:
                break

            for org in orgs:
                if len(all_results) >= max_results:
                    break

                name = org.get("name", "N/A")
                ein = org.get("ein", "N/A")
                city = org.get("city", "N/A")
                state_code = org.get("state", "N/A")

                detail = None
                if ein:
                    detail_resp = requests.get(f"{BASE_URL}/organizations/{ein}.json")
                    if detail_resp.status_code == 200:
                        detail_json = detail_resp.json()
                        detail = detail_json.get("organization")

                # ✅ Change here: use Tax-exempt since ... for about
                about = fetch_tax_exempt_date(ein)

                affiliation = classify_affiliation(name, detail)
                past_involvement = fetch_grants(ein) if ein else "N/A"
                sponsor_link = f"https://projects.propublica.org/nonprofits/organizations/{ein}" if ein else "N/A"

                # ✅ Fetch logo from Google (no caching)
                logo_url = fetch_logo(name)

                donor_json = {
                    "name": name,
                    "image": logo_url,
                    "alt": f"{name} Logo",
                    "contribution": "Donations / Grants",
                    "contributionAmt": "N/A",
                    "affiliation": affiliation,
                    "pastInvolvement": past_involvement,
                    "about": about,
                    "sponsor_link": sponsor_link,
                    "type": "sponsor",
                    "city": city,
                    "state": state_code,
                    "EIN": str(ein)
                }

                all_results.append(donor_json)
                time.sleep(0.3)

            page += 1
            if page >= data.get("num_pages", 0):
                break
            time.sleep(0.5)

        if len(all_results) >= max_results:
            break

    return all_results

if __name__ == "__main__":
    donors = scrape()
