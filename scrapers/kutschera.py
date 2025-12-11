import asyncio
import json
from datetime import datetime, timedelta
from typing import List
from core.models import Doctor
from .base import BaseScraper
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class KutscheraScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Kutschera] Scraping {self.doctor_name}...")
        
        base_url = "https://termin.kutschera.co.at/bootstrap/php"
        url_urlaub = f"{base_url}/get_urlaub.php"
        url_termine = f"{base_url}/get_termine.php"
        url_details = f"{base_url}/wochentag.php"
        
        kunden_id = self.config.get("kunden_id", 385)
        blockzeit = self.config.get("blockzeit", 30)
        
        slots = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Visit main page first to get cookies/session
                await page.goto("https://termin.kutschera.co.at/eckhardtm/", wait_until="domcontentloaded")
                
                # Helper to make requests with correct headers
                async def post_request(url, data):
                    # Use page.evaluate to ensure we use the same fetch context as the page
                    # This is more robust than context.request.post for some PHP sessions
                    return await page.evaluate("""
                        async ({url, data}) => {
                            const formData = new FormData();
                            for (const k in data) {
                                formData.append(k, data[k]);
                            }
                            const response = await fetch(url, {
                                method: 'POST',
                                body: formData
                            });
                            return await response.text();
                        }
                    """, {"url": url, "data": data})

                heute = datetime.now()
                ende = heute + timedelta(days=180)
                datum_start = heute.strftime("%Y-%m-%d")
                datum_ende = ende.strftime("%Y-%m-%d")
                
                # 1. Urlaub
                urlaub_text = await post_request(url_urlaub, {
                    'kunden_id': kunden_id, 'datum_start': datum_start, 'datum_ende': datum_ende
                })
                try:
                    urlaub_set = set(json.loads(urlaub_text))
                except:
                    print(f"[Kutschera] Failed to parse Urlaub. Text: {urlaub_text[:100]}")
                    urlaub_set = set()
                
                # 2. Termine
                termine_text = await post_request(url_termine, {
                    'kunden_id': kunden_id, 'datum_start': datum_start, 'datum_ende': datum_ende, 'blockzeit': blockzeit
                })
                
                try:
                    termine_data = json.loads(termine_text)
                    print(f"[Kutschera] Got {len(termine_data)} entries.")
                except:
                    print(f"[Kutschera] Failed to parse Termine. Text: {termine_text[:100]}")
                    termine_data = []
                
                found_count = 0
                
                for eintrag in termine_data:
                    if found_count >= 10: break
                    
                    if isinstance(eintrag, list): datum_str = eintrag[0]
                    elif isinstance(eintrag, dict): datum_str = eintrag.get('datum', '')
                    else: datum_str = str(eintrag)
                    
                    if datum_str in urlaub_set: continue
                    
                    try:
                        d_obj = datetime.strptime(datum_str, "%Y-%m-%d")
                        js_wochentag = (d_obj.weekday() + 1) % 7
                        
                        detail_text = await post_request(url_details, {
                            'kunden_id': kunden_id, 'wochentag': js_wochentag, 'blockzeit': blockzeit, 'datum': datum_str
                        })
                        
                        soup = BeautifulSoup(detail_text, 'html.parser')
                        
                        buchbare_buttons = soup.find_all("button", onclick=True)
                        echte_slots = [b for b in buchbare_buttons if "buchen" in b['onclick']]
                        
                        # Also check for div.aviable (typo in website)
                        freie_divs = soup.find_all("div", class_="aviable")
                        
                        found_slots_in_day = []
                        
                        # Process buttons
                        for btn in echte_slots:
                            found_slots_in_day.append(btn.text.strip())
                            
                        # Process divs
                        for div in freie_divs:
                            # Text might be "10:00 bis 10:30"
                            txt = div.text.strip()
                            # Extract start time
                            parts = txt.split(" bis ")
                            if parts:
                                found_slots_in_day.append(parts[0].strip())
                        
                        if found_slots_in_day:
                            for time_str in found_slots_in_day:
                                # Clean up time string (sometimes it has extra chars)
                                time_str = time_str.split(" ")[0]
                                try:
                                    t_obj = datetime.strptime(f"{datum_str} {time_str}", "%Y-%m-%d %H:%M")
                                    slots.append(t_obj.isoformat())
                                except:
                                    # Try just appending date if time parse fails
                                    pass
                            
                            found_count += 1
                        
                        await asyncio.sleep(0.1)
                        
                    except Exception:
                        continue
                
                await browser.close()
                    
        except Exception as e:
            print(f"[Kutschera] Error: {e}")

        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Graz"),
            speciality=self.config.get("speciality", "Augenarzt"),
            insurance=self.config.get("insurance", ["ÖGK", "BVAEB"]),
            slots=sorted(list(slots)),
            booking_url=self.config.get("booking_url", "")
        )
        print(f"[Kutschera] Found {len(slots)} slots.")
        return [doctor]
