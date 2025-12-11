import asyncio
from typing import List
from core.models import Doctor
from .base import BaseScraper
from playwright.async_api import async_playwright

class DoctenaScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Doctena] Scraping {self.doctor_name}...")
        
        url = self.config.get("booking_url")
        slots = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Check for "booking not possible" alert
                    # <div class="alert alert-warning" role="alert">
                    alert = await page.query_selector(".alert.alert-warning")
                    if alert:
                        text = await alert.inner_text()
                        if "nicht möglich" in text:
                            print(f"[Doctena] Online booking not possible for {self.doctor_name}")
                            await browser.close()
                            return [self._create_doctor(slots)]

                    # If no alert, try to find slots
                    # This part is speculative as we don't have a working example yet
                    # But typically Doctena uses .availabilities-slot
                    avail_slots = await page.query_selector_all(".availabilities-slot")
                    for slot in avail_slots:
                        # Parse slot time...
                        pass
                        
                except Exception as e:
                    print(f"[Doctena] Page load error: {e}")
                
                await browser.close()
                    
        except Exception as e:
            print(f"[Doctena] Error: {e}")
            
        print(f"[Doctena] Found {len(slots)} slots.")
        return [self._create_doctor(slots)]

    def _create_doctor(self, slots):
        return Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Klagenfurt"),
            speciality=self.config.get("speciality", "Zahnarzt"),
            insurance=self.config.get("insurance", ["Alle Kassen"]),
            slots=slots,
            booking_url=self.config.get("booking_url", "")
        )
