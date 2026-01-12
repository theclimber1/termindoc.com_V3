import asyncio
import json
import urllib.parse
from typing import List
from datetime import datetime
from core.models import Doctor
from .base import BaseScraper
from playwright.async_api import async_playwright

class CustomPerfectSmileScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Perfect Smile] Scraping {self.doctor_name} (Deep Scan V2 - UI Interaction)...")
        
        # Structure: Location -> Services
        LOCATIONS = [
            {"name": "Wolfsberg", "id": "112273", "services": [
                {"name": "Beratung", "id": "112275"}
            ]},
            {"name": "Klagenfurt", "id": "112274", "services": [
                {"name": "Beratung", "id": "111869"},
                {"name": "Reparatur", "id": "111849"},
                {"name": "Schmerzen", "id": "111850"},
            ]}
        ]
        
        generated_doctors = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            for loc in LOCATIONS:
                for service in loc["services"]:
                    
                    loc_name = loc["name"]
                    serv_name = service["name"]
                    loc_id = loc["id"]
                    serv_id = service["id"]
                    
                    safe_loc = loc_name.lower().replace(" ", "_")
                    safe_serv = serv_name.lower().replace(" ", "_").replace(".", "")
                    unique_id = f"perfect_smile_{safe_loc}_{safe_serv}"
                    display_name = f"Perfect Smile {loc_name} ({serv_name})"
                    
                    print(f"  -> Processing: {display_name}...")
                    page = await context.new_page()
                    all_slots = []
                    
                    try:
                        # 1. Navigate & Setup
                        await page.goto("https://termine.softdent.at/perfect-smile")
                        
                        # Click Location
                        try:
                            await page.wait_for_selector(f'[id="{loc_id}"]', timeout=5000)
                            await page.click(f'[id="{loc_id}"]')
                        except:
                            print(f"    [Warn] Location {loc_name} not found.")
                            await page.close()
                            continue
                            
                        # Click Service
                        try:
                            await page.wait_for_selector(f'[id="{serv_id}"]', timeout=5000)
                            await page.click(f'[id="{serv_id}"]')
                        except:
                            print(f"    [Warn] Service {serv_name} not found.")
                            await page.close()
                            continue
                            
                        # Click Weiter
                        try:
                            await page.click("text=Weiter zur Terminauswahl")
                        except:
                            await page.click("button:has-text('Weiter')")
                            
                        # 2. Iterate Months (Safety limit: 3 months)
                        for _ in range(4):
                            try:
                                # Wait for calendar to be visible
                                await page.wait_for_selector(".ui-datepicker-calendar", timeout=5000)
                            except:
                                break
                            
                            # Find available days (class 'dayA')
                            # Note: We need to re-query elements after every click usually, 
                            # because DOM might refresh. 
                            # Strategy: Get list of indices or IDs, then query one by one.
                            
                            # However, Softdent slots load below the calendar without refreshing the calendar itself?
                            # Let's verify.
                            # We can just iterate elements.
                            
                            day_elements = await page.query_selector_all("td.dayA")
                            print(f"    Found {len(day_elements)} active days in current view.")
                            
                            for i in range(len(day_elements)):
                                # Re-query simply to be safe against DOM updates (stale element ref)
                                days = await page.query_selector_all("td.dayA")
                                if i >= len(days): break
                                day_el = days[i]
                                
                                # Setup Interceptor for THIS click
                                response_future = asyncio.Future()
                                
                                async def handle_slot_response(response):
                                    if "api/timeslots" in response.url and response.status == 200:
                                        # Verify it's NOT the rangesearch=1 call
                                        if "rangesearch=1" not in response.url:
                                            try:
                                                data = await response.json()
                                                if not response_future.done():
                                                    response_future.set_result(data)
                                            except: pass
                                
                                # Add listener
                                page.on("response", handle_slot_response)
                                
                                try:
                                    # Click the day
                                    await day_el.click()
                                    
                                    # Wait for response
                                    slots_data = await asyncio.wait_for(response_future, timeout=3)
                                    
                                    # Parse
                                    if isinstance(slots_data, list):
                                        for s in slots_data:
                                            t = s.get("start")
                                            # We want precise times, usually they are 2026-02-16T08:30:00
                                            if t and "00:00:00" not in t:
                                                all_slots.append(t)
                                except asyncio.TimeoutError:
                                    # Just ignore, maybe clicked wrong thing or no slots loaded
                                    pass
                                except Exception as e:
                                    print(f"      Error clicking day: {e}")
                                finally:
                                    # Remove listener to avoid leaks/confusion
                                    page.remove_listener("response", handle_slot_response)
                                    
                            # Check for Next Month button
                            next_btn = await page.query_selector(".ui-datepicker-next")
                            if next_btn:
                                # click next
                                await next_btn.click()
                                await page.wait_for_timeout(1000) # Wait for animation
                            else:
                                break
                                
                    except Exception as e:
                        print(f"    [Error] {display_name}: {e}")
                    finally:
                        await page.close()
                    
                    if all_slots:
                        # De-duplicate
                        all_slots = sorted(list(set(all_slots)))
                        print(f"    -> Collected {len(all_slots)} unique slots.")
                    
                    doc = Doctor(
                        id=unique_id,
                        name=display_name,
                        address=f"Perfekt Smile {loc_name}",
                        speciality="Kieferorthopädie",
                        insurance=self.config.get("insurance", ["Alle Kassen"]),
                        slots=all_slots,
                        booking_url="https://perfect-smile.at/online-terminvereinbarung/"
                    )
                    generated_doctors.append(doc)

            await browser.close()
            
        return generated_doctors
