import json
import requests
import datetime
from datetime import timedelta

def diagnose():
    with open("config/doctors_registry.json", "r") as f:
        registry = json.load(f)

    # Filter for Dr. Ambrozy
    target_ids = ["ambrozy_latido"]

    print(f"Diagnosing {len(target_ids)} doctors...\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    start_date = datetime.datetime.now()
    end_date = start_date + timedelta(days=120)

    for doctor in registry:
        if doctor["id"] in target_ids:
            print(f"--- Checking {doctor['name']} ({doctor['id']}) ---")
            
            params = {
                "doctorid": doctor.get("doctor_id"),
                "calendarid": doctor.get("calendar_id"),
                "typeid": doctor.get("type_id"),
                "start": start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "end": end_date.strftime("%Y-%m-%dT%H:%M:%S.999Z")
            }

            print(f"Querying from {start_date.date()} to {end_date.date()}...")

            try:
                resp = requests.get("https://patient.latido.at/api/appointments/freeslots", params=params, headers=headers, timeout=10)
                print(f"Status Code: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        print(f"Response: Valid JSON List. Item count: {len(data)}")
                        if len(data) == 0:
                            print("RESULT: NO SLOTS AVAILABLE (Empty List)")
                        else:
                            print(f"RESULT: {len(data)} SLOTS FOUND")
                            # Print the first few slots to verify the date/time
                            for slot in data[:10]:
                                print(f"  - Found slot: {slot.get('start')}")
                    else:
                        print(f"Response: Unexpected JSON format: {str(data)[:100]}...")
                else:
                    print(f"Response Error: {resp.text[:200]}")
            
            except Exception as e:
                print(f"Request Failed: {e}")
            
            print("\n")

if __name__ == "__main__":
    diagnose()
