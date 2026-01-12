import requests
import asyncio
from typing import List
from core.models import Doctor
from .base import BaseScraper
from datetime import datetime, timedelta

class CustomAichingerScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Aichinger] Scraping {self.doctor_name}...")
        
        # Base URL for Wisitor API
        base_url = "https://www.wisitor.at/php/Termine"
        
        # Parameters specific to Dr. Aichinger
        # o=123&l=200&t=ITOR10001400001000070012300200
        params_base = {
            "o": "123",
            "l": "200",
            "t": "ITOR10001400001000070012300200"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        slots = []
        loop = asyncio.get_event_loop()
        
        try:
            # 1. Fetch available days (freieTage.php)
            # We need to guess the range or just ask for the next few months.
            # Palasser used `Datum` (start date) and `Bis` (days count).
            start_date = datetime.now().strftime("%Y-%m-%d")
            
            days_params = params_base.copy()
            days_params.update({
                "Datum": start_date,
                "Bis": "120",
                "Grund": "399",
                "Ordination": "123", # 'o' parameter
                "OrdinationListe": "200", # 'l' parameter
                "Token": "ITOR10001400001000070012300200", # 't' parameter
                "s": "standard"
            })
            
            # Note: The 'Grund' (Reason) usually comes from selecting an appointment type.
            # In the browser trace, I clicked "Erstuntersuchung" for Kletz, but for Aichinger 
            # the main page just showed a calendar.
            # Let's try to hit `freieTage.php` with just the base params and date.
            
            days_url = f"{base_url}/freieTage.php"
            
            print(f"[Aichinger] Fetching days from {days_url} with params {days_params}")
            
            response = await loop.run_in_executor(None, lambda: requests.get(days_url, params=days_params, headers=headers))
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Data structure expected: [{"YYYY-MM-DD": {...}, ...}] or similar
                    # Response might be [null, null] if no days found
                    
                    if isinstance(data, list) and len(data) > 0:
                        tage_dict = data[0]
                        
                        if tage_dict:
                            for datum_str, info in tage_dict.items():
                                # info might be "LEER", "VOLL", or a dict/list
                                # If it's not "VOLL" and not "LEER" (or "LEER" means available?), we check deeper.
                                # In Palasser: "LEER" meant available (empty slots).
                                
                                if info != "VOLL":
                                    # Check if times are already here
                                    if isinstance(info, dict) and "Termine" in info:
                                        termine = info["Termine"]
                                        if termine == "VOLL":
                                            continue
                                        elif isinstance(termine, list):
                                            for t_entry in termine:
                                                if isinstance(t_entry, dict):
                                                    std = t_entry.get("BeginnSTD")
                                                    min_ = t_entry.get("BeginnMIN")
                                                    if std and min_:
                                                        slots.append(f"{datum_str}T{std}:{min_}:00")
                                        elif termine == "LEER":
                                            # LEER might mean fully available, but without specific slots it's hard to map.
                                            # We skip it for now as we have plenty of explicit slots.
                                            pass
                                    else:
                                        # Fallback or other format
                                        pass
                        else:
                            print("[Aichinger] No available days found (data[0] is null).")
                                    
                except Exception as json_err:
                     print(f"[Aichinger] JSON Error: {json_err} - Response: {response.text[:100]}")

            else:
                print(f"[Aichinger] Failed to fetch days: {response.status_code}")
                
        except Exception as e:
            print(f"[Aichinger] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Klagenfurt"),
            speciality=self.config.get("speciality", "Hautarzt"),
            insurance=self.config.get("insurance", ["Alle Kassen"]),
            slots=slots,
            booking_url=self.config.get("booking_url", ""),
            show_time=self.config.get("show_time", True)
        )
        print(f"[Aichinger] Found {len(slots)} slots.")
        return [doctor]
