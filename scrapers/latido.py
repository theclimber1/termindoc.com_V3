import requests
import asyncio
from datetime import datetime, timedelta
from typing import List
from core.models import Doctor
from .base import BaseScraper

class LatidoScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Latido] Scraping {self.doctor_name}...")
        
        doctor_id = self.config.get("doctor_id")
        calendar_id = self.config.get("calendar_id")
        type_id = self.config.get("type_id")
        
        api_url = "https://patient.latido.at/api/appointments/freeslots"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        slots = []
        loop = asyncio.get_event_loop()
        
        try:
            start_date = datetime.now()
            # Search 6 months ahead to catch distant appointments
            end_date_limit = start_date + timedelta(days=180)
            current_start = start_date
            
            while current_start < end_date_limit:
                # Use 90-day chunks to minimize requests (API supports large ranges)
                current_end = current_start + timedelta(days=90)
                
                params = {
                    "doctorid": doctor_id,
                    "calendarid": calendar_id,
                    "typeid": type_id,
                    "start": current_start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "end": current_end.strftime("%Y-%m-%dT%H:%M:%S.999Z")
                }
                
                resp = await loop.run_in_executor(None, lambda: requests.get(api_url, params=params, headers=headers))
                
                if resp.status_code == 200:
                    data = resp.json()
                    for slot in data:
                        start_utc = slot.get("start") # 2025-12-04T07:00:00.000Z
                        if start_utc:
                            # Convert to ISO (keep UTC or naive)
                            slots.append(start_utc)
                
                current_start = current_end
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"[Latido] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Klagenfurt"),
            speciality=self.config.get("speciality", "Allgemeinmedizin"),
            insurance=self.config.get("insurance", ["Alle Kassen"]),
            slots=slots,
            booking_url=self.config.get("booking_url", "")
        )
        print(f"[Latido] Found {len(slots)} slots.")
        return [doctor]
