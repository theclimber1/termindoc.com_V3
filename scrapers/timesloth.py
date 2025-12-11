import requests
import asyncio
from datetime import datetime
from typing import List
from core.models import Doctor
from .base import BaseScraper

class TimeslothScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Timesloth] Scraping {self.doctor_name}...")
        
        booking_url = self.config.get("booking_url")
        # Extract slugs from URL if not provided explicitly
        # URL format: https://shop.timesloth.io/de/a/{customer_slug}/{event_slug}?backButton=true
        try:
            parts = booking_url.split("/a/")[1].split("/")
            customer_slug = parts[0]
            event_slug = parts[1].split("?")[0]
        except Exception as e:
            print(f"[Timesloth] Error parsing URL {booking_url}: {e}")
            return []

        api_url = f"https://api.timesloth.io/integrations/appointments/customers/{customer_slug}/events/{event_slug}/slots"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        slots = []
        loop = asyncio.get_event_loop()
        
        try:
            resp = await loop.run_in_executor(None, lambda: requests.get(api_url, headers=headers))
            
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    timestamp_ms = item.get("start")
                    if timestamp_ms:
                        # Convert ms to seconds
                        dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
                        # Format to ISO 8601
                        slots.append(dt.isoformat())
            else:
                print(f"[Timesloth] API Error: {resp.status_code}")
                
        except Exception as e:
            print(f"[Timesloth] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", ""),
            speciality=self.config.get("speciality", ""),
            insurance=self.config.get("insurance", []),
            slots=slots,
            booking_url=booking_url
        )
        print(f"[Timesloth] Found {len(slots)} slots.")
        return [doctor]
