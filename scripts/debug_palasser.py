import requests
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def main():
    base_url = "https://www.wisitor.at/php/Termine/freieTage.php?Datum=2026-01-01&Bis=90&Grund=489&Ordination=153&OrdinationListe=245&Token=ITOR10014800002000080015300245"
    
    # Update date to today
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query)
    today = datetime.now().strftime("%Y-01-01") # Still keep Jan 1 to see full scope or today?
    # User says 13.1. is problematic. Let's start from today or a fixed date close to 13.1.2026?
    # Wait, current date is 2026-01-12. So 13.1 is tomorrow.
    params['Datum'] = [datetime.now().strftime("%Y-%m-%d")]
    
    new_query = urlencode(params, doseq=True)
    url = urlunparse(parsed._replace(query=new_query))
    
    print(f"Fetching: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("Response (first item keys/sample):")
        if isinstance(data, list) and len(data) > 0:
            tage = data[0]
            for target_date in sorted(tage.keys()):
                if "2026-01" not in target_date:
                    continue
                info = tage[target_date]
                termine = info.get("Termine")
                if isinstance(termine, list):
                    print(f"{target_date}: LIST with {len(termine)} entries")
                    if target_date in ["2026-01-13", "2026-01-14", "2026-01-15", "2026-01-19"]:
                         print(json.dumps(termine, indent=2))
                else:
                    print(f"{target_date}: {termine}")
        else:
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
