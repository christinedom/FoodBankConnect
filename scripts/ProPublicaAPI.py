import requests
import json
import time

BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"

def fetch_search(q="food bank", state=None, page=0):
    """
    Calls /search.json on the ProPublica Nonprofit Explorer API.
    Returns parsed JSON (dict) for that page.
    """
    url = f"{BASE_URL}/search.json"
    params = {"q": q, "page": page}
    if state:
        params["state[id]"] = state
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_organization(ein: str):
    """
    Calls /organizations/:ein.json for detailed nonprofit info.
    """
    url = f"{BASE_URL}/organizations/{ein}.json"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return resp.json()

def scrape(q="food bank", state=None, max_pages=2):
    """
    Returns a list of JSON objects formatted for the FoodBank schema.
    Missing fields are filled with 'N/A'.
    """
    results = []
    org_id = 1

    for page in range(max_pages):
        print(f"Fetching page {page+1}...")
        search_json = fetch_search(q=q, state=state, page=page)
        orgs = search_json.get("organizations", [])
        if not orgs:
            break

        for org in orgs:
            ein = org.get("ein")
            name = org.get("name", "N/A")
            city = org.get("city", "N/A")
            state_code = org.get("state", "N/A")
            website = org.get("website", "N/A")
            # Get detailed org info
            detail = fetch_organization(ein)
            if detail and "organization" in detail:
                org_detail = detail["organization"]
                about = org_detail.get("mission", "N/A")
                address = org_detail.get("street", "N/A")
                zipcode = org_detail.get("zipcode", "N/A")
            else:
                about = "N/A"
                address = "N/A"
                zipcode = "N/A"

            # Construct JSON in your format
            foodbank_json = {
                "about": about,
                "address": address,
                "capacity": "N/A",  # not provided by ProPublica
                "city": city,
                "eligibility": "N/A",
                "id": str(org_id),
                "image": "N/A",
                "languages": ["English"],
                "name": name,
                "phone": "N/A",
                "services": [
                    "N/A"
                ],
                "type": "foodbank",
                "urgency": "N/A",
                "website": website if website else "N/A",
                "zipcode": zipcode
            }

            results.append(foodbank_json)
            org_id += 1

            # Pause to be polite to the API
            time.sleep(0.2)

        # Stop if last page
        if page >= search_json.get("num_pages", 0) - 1:
            break

    return results

if __name__ == "__main__":
    data = scrape(q="food bank", state="TX", max_pages=2)
    print(json.dumps(data, indent=2))
