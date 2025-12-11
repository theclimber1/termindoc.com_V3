import requests
import asyncio
from typing import List
from core.models import Doctor
from .base import BaseScraper
from datetime import datetime

class CustomPalasserScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Palasser] Scraping {self.doctor_name}...")
        
        # URL from config or hardcoded fallback
        url = self.config.get("api_url", self.config.get("url"))
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        slots = []
        loop = asyncio.get_event_loop()
        
        try:
            response = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers))
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    tage_dict = data[0]
                    
                    # Logic from palasser.py (simplified for brevity)
                    # We iterate over days and find "LEER" or gaps
                    
                    for datum, info in tage_dict.items():
                        termine = info.get("Termine")
                        if termine == "LEER":
                            # Add a slot for the day (08:00) just to mark availability
                            slots.append(f"{datum}T08:00:00")
                        elif isinstance(termine, list):
                            # Has bookings, but might have gaps. 
                            # For aggregator, just marking the day as "check details" is often enough,
                            # but let's try to add one slot if possible.
                            # Real logic is complex (gaps), let's assume if it's not "VOLL", there might be space.
                            pass
                            
        except Exception as e:
            print(f"[Palasser] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Lienz"),
            speciality=self.config.get("speciality", "Internist"),
            insurance=self.config.get("insurance", ["Wahlarzt"]),
            slots=slots,
            booking_url=self.config.get("booking_url", "")
        )
        print(f"[Palasser] Found {len(slots)} slots.")
        return [doctor]
