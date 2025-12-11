import asyncio
from typing import List
from core.models import Doctor
from .base import BaseScraper

class CustomPerfectSmileScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Perfect Smile] Scraping {self.doctor_name}...")
        
        # Perfect Smile requires login, so we cannot scrape slots publicly.
        # We return the doctor with 0 slots, so they appear in the list (if the UI supports it)
        # or at least the user knows they are in the system.
        
        slots = []
        
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Klagenfurt"),
            speciality=self.config.get("speciality", "Zahnarzt"),
            insurance=self.config.get("insurance", ["Alle Kassen"]),
            slots=slots,
            booking_url=self.config.get("booking_url", "")
        )
        print(f"[Perfect Smile] Added as directory entry (login required).")
        return [doctor]
