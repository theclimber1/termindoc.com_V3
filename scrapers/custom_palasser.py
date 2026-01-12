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
                        try:
                            # --- Simplified Day-Only Mode (Project Status: Known Issue) ---
                            # Logic: Only identify available DAYS. Ignore specific times/grids/hours.
                            # Return one placeholder slot (08:00) per available day.
                            
                            if info == "VOLL":
                                continue
                                
                            # Skip today/past
                            if datetime.strptime(datum, "%Y-%m-%d").date() <= datetime.now().date():
                                continue
                            
                            # Check availability
                            is_available = False
                            if isinstance(info, dict):
                                termine = info.get("Termine")
                                if isinstance(termine, list) and len(termine) > 0:
                                    is_available = True
                            
                            if is_available:
                                # Add single placeholder slot
                                slots.append(f"{datum}T08:00:00")
                                
                        except Exception as day_err:
                            print(f"[Palasser] Error processing day {datum}: {day_err}")

                            
        except Exception as e:
            print(f"[Palasser] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Lienz"),
            speciality=self.config.get("speciality", "Internist"),
            insurance=self.config.get("insurance", ["Wahlarzt"]),
            slots=slots,
            booking_url=self.config.get("booking_url", ""),
            show_time=self.config.get("show_time", True)
        )
        return [doctor]
