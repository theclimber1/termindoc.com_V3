import requests
import asyncio
from datetime import datetime, timedelta
import urllib.parse
from typing import List
from core.models import Doctor
from .base import BaseScraper

class MobimedScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Mobimed] Scraping {self.doctor_name}...")
        
        user_id = self.config.get("mobimed_user_id")
        service_id = self.config.get("mobimed_service_id", 21) # Default to 21 (Erstordination) if not specified
        booking_url = self.config.get("booking_url")
        
        if not user_id:
            print(f"[Mobimed] Error: No 'mobimed_user_id' configured for {self.doctor_name}")
            return []

        # Calculate date range (next 60 days)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=60)
        
        # Format dates as ISO 8601 with timezone (UTC)
        fmt = "%Y-%m-%dT%H:%M:%S.000Z"
        start_str = start_date.strftime(fmt)
        end_str = end_date.strftime(fmt)
        
        # Construct URL
        base_url = "https://scheduler.mobimed.at/api/scheduler/slots"
        params = {
            "from": start_str,
            "to": end_str,
            "service": service_id,
            "user": user_id
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://scheduler.mobimed.at/ensat/",
            "Accept": "application/json",
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjYyNjZlOWFhOTdlYzdhNjM5YzAyMzQyNTBmNGU3NmRkOTZlNDI3NmExOTJjZjhjNGU1Zjc0ZGJhOGFhNTQxZjU3ODRiNjUyZjVmMTc5Y2QyIn0.eyJhdWQiOiIxIiwianRpIjoiNjI2NmU5YWE5N2VjN2E2MzljMDIzNDI1MGY0ZTc2ZGQ5NmU0Mjc2YTE5MmNmOGM0ZTVmNzRkYmE4YWE1NDFmNTc4NGI2NTJmNWYxNzljZDIiLCJpYXQiOjE2NTQ3NzAwOTcsIm5iZiI6MTY1NDc3MDA5NywiZXhwIjoxOTcwMzg5Mjk3LCJzdWIiOiIxMzEiLCJzY29wZXMiOlsic2NoZWR1bGUtYXBwb2ludG1lbnRzIl19.SrCRhUlteoRhP-Jo4cDTlF19SqW7cUKqZz9kMlh0sp34cMOz5esr6bae4UjJrvMYoqoYAsxDgbkYO8hMA1hfahmk_gTviIiaWA-tNC3iGB_ulwPPSO5HWE1lDQ0FKkFkG-k4n37EgyBn-vFRkNZU-Iqo4nYww9HLFw5Hu5aeTe9LB0YMGO8Tjedz_JN_8YMgA-FwIOBmNPgDmyortt3B8OmpkbqCKp21rXiqaBrU2TkRkunkLRbTIHFmDmVt2W5_S-0K1rt6ATM5KjUhiIWyW2m1W1iyUtt-gG4wMY4Zc0hcPrdzOlIoyF8VNJ4YBVveA2qJiB4HKJm3k8UEHK-EBOaY97AVuUdP0Ud_b82s1YDP2NuNGXNewxfcIh4JSJPqWJfvZdrl-thVMYcin-1L4HRsVnRjCiQZnJEVZiRsbAQz1YbBgcV0OedFVUnoVkC2WeSZ3hMMsHoKab0cJM7pDH41GR6FTrjjlNWN1DpRW5amRW5DMygEGb7m3s20tRR9GDkCARKkbY6Kif5zTMhQcCy3UPWe20khpZ72Jbu2cZEwD13d_Rm2v0TaofKquuUk3-puxJVtA-BpKMJE635wsdNySsCoSo6WYgyZc7xNahE7Hh-jGdoflQjSZoKvgJa2Zsyv3oL_HCZ2EE-YWYu2nNu9FRckVUgID9Zi4IXj6GM"
        }
        
        slots = []
        loop = asyncio.get_event_loop()
        
        try:
            resp = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers))
            
            if resp.status_code == 200:
                data = resp.json()
                # Data structure: {"slots": [{"start": "...", "end": "...", ...}, ...]}
                # Or maybe it's a list directly? The analysis log didn't show the body of slots response.
                # Usually it's a list or dict with "slots".
                
                slots_data = data.get("slots", []) if isinstance(data, dict) else data
                
                for slot in slots_data:
                    start_time = slot.get("date")
                    if start_time:
                        slots.append(start_time)
                
            else:
                print(f"[Mobimed] API Error: {resp.status_code}")
                
        except Exception as e:
            print(f"[Mobimed] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", ""),
            speciality=self.config.get("speciality", ""),
            insurance=self.config.get("insurance", []),
            slots=slots,
            booking_url=booking_url
        )
        
        print(f"[Mobimed] Found {len(slots)} slots.")
        return [doctor]
