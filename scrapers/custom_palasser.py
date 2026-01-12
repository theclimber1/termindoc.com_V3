import requests
import asyncio
from typing import List
from core.models import Doctor
from .base import BaseScraper
from datetime import datetime, timedelta

class CustomPalasserScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Palasser] Scraping {self.doctor_name}...")
        
        # URL from config or hardcoded fallback
        base_url = self.config.get("api_url", self.config.get("url"))
        
        # Force current date to ensure valid results
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(base_url)
            params = parse_qs(parsed.query)
            params['Datum'] = [datetime.now().strftime("%Y-%m-%d")]
            # Rebuild query string
            new_query = urlencode(params, doseq=True)
            url = urlunparse(parsed._replace(query=new_query))
        except Exception as e:
            print(f"[Palasser] Error updating date param: {e}, using config URL")
            url = base_url
        
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
                        
                        # Fix 1: Skip days marked as "VOLL" (Full)
                        if termine == "VOLL":
                            continue
                            
                        # Fix 2: Skip today as requested (same-day bookings not possible)
                        date_obj = datetime.strptime(datum, "%Y-%m-%d").date()
                        if date_obj <= datetime.now().date():
                            continue

                        # Parse blocks
                        blocks = []
                        if isinstance(termine, list):
                            for term in termine:
                                try:
                                    std = term.get("BeginnSTD")
                                    min_ = term.get("BeginnMIN")
                                    dauer = int(term.get("Dauer", 0))
                                    if std and min_:
                                        start_dt = datetime.strptime(f"{datum}T{std}:{min_}:00", "%Y-%m-%dT%H:%M:%S")
                                        end_dt = start_dt + timedelta(minutes=dauer)
                                        blocks.append((start_dt, end_dt))
                                except Exception as parsing_err:
                                    print(f"[Palasser] Error parsing block {term}: {parsing_err}")
                        
                        blocks.sort()
                        
                        # Define day limits - Start at 08:00 as seen online
                        day_start = datetime.strptime(f"{datum}T08:00:00", "%Y-%m-%dT%H:%M:%S")
                        day_end = datetime.strptime(f"{datum}T19:00:00", "%Y-%m-%dT%H:%M:%S")
                        slot_duration = 20 # minutes
                        
                        # Find gaps
                        current = day_start
                        while current + timedelta(minutes=slot_duration) <= day_end:
                            # Grid Alignment: Ensure current is on a 10-minute mark (0, 10, 20...)
                            if current.minute % 10 != 0:
                                # Snap to next 10-minute mark
                                minutes_to_add = 10 - (current.minute % 10)
                                current += timedelta(minutes=minutes_to_add)
                                current = current.replace(second=0, microsecond=0)
                                if current + timedelta(minutes=slot_duration) > day_end:
                                    break

                            # 1. Check if current is strictly inside a block -> jump to end
                            in_block = False
                            for b_start, b_end in blocks:
                                if b_start <= current < b_end:
                                    current = b_end
                                    in_block = True
                                    break
                            if in_block:
                                continue
                                
                            # 2. Check if slot fits (current + duration <= next_block_start)
                            slot_end = current + timedelta(minutes=slot_duration)
                            clash = False
                            for b_start, b_end in blocks:
                                if current < b_end and slot_end > b_start:
                                    clash = True
                                    current = b_end
                                    break
                            
                            if not clash:
                                if current > datetime.now():
                                    slots.append(current.strftime("%Y-%m-%dT%H:%M:%S"))
                                current += timedelta(minutes=slot_duration)

                            
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
