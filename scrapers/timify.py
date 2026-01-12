import asyncio
import re
from typing import List
from playwright.async_api import async_playwright
from core.models import Doctor
from scrapers.base import BaseScraper
from datetime import datetime

class TimifyScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.booking_url = config.get("booking_url")
        self.service_filter = config.get("service_filter")
        
        # Initialize doctor object
        name = config.get("name")
        if self.service_filter and "(" not in name:
            name = f"{name} ({self.service_filter})"

        self.doctor = Doctor(
            id=config.get("id"),
            name=name,
            speciality=config.get("speciality", "Allgemeinmedizin"),
            address=config.get("address", ""),
            insurance=config.get("insurance", []),
            booking_url=self.booking_url,
            slots=[]
        )

    async def scrape(self) -> List[Doctor]:
        print(f"[Timify] Scraping {self.doctor.name} (UI)...")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="de-DE"
            )
            page = await context.new_page()
            
            try:
                # 1. Go to Booking URL
                await page.goto(self.booking_url, timeout=60000)
                
                # Wait for Service Selection (Guest widget usually shows services first)
                try:
                    await page.wait_for_selector(".ta-services__service", timeout=20000)
                except:
                    print(f"[Timify] No services found/loaded for {self.doctor.name}")
                    await browser.close()
                    return [self.doctor]

                # 2. Select Service
                service_clicked = False
                if self.service_filter:
                    # Iterate items to match text
                    items = page.locator(".ta-services__service")
                    count = await items.count()
                    for i in range(count):
                        item = items.nth(i)
                        text = await item.inner_text()
                        if self.service_filter.lower() in text.lower():
                            # Ensure visible and clickable
                            await item.scroll_into_view_if_needed()
                            await item.click()
                            service_clicked = True
                            print(f"[Timify] Selected service '{self.service_filter}'")
                            break
                    
                    if not service_clicked:
                        print(f"[Timify] Service '{self.service_filter}' not found, clicking first available.")
                
                if not service_clicked:
                    # Click first service
                    await page.locator(".ta-services__service").first.click()
                    print("[Timify] Selected first service.")

                # 3. Wait for Calendar
                # Look for calendar elements
                try:
                    await page.wait_for_selector(".ta-slots__slot", timeout=15000)
                except:
                   # Check if staff selection is needed?
                   if await page.locator(".ta-resource-item").count() > 0:
                        print("[Timify] Selecting first resource/staff...")
                        await page.locator(".ta-resource-item").first.click()
                        await page.wait_for_selector(".ta-slots__slot", timeout=10000)
                   else:
                        pass # Maybe no slots available at all?

                # 4. Extract Slots
                unique_slots = set()
                
                # We will check 4 weeks
                for week_idx in range(4):
                    # Check for "Show More" buttons and click them to reveal all slots
                    show_more_btns = page.locator(".ta-slots__show-more")
                    count_more = await show_more_btns.count()
                    for i in range(count_more):
                        try:
                            if await show_more_btns.nth(i).is_visible():
                                await show_more_btns.nth(i).click()
                                await page.wait_for_timeout(500)
                        except:
                            pass # Might disappear or be covered

                    # Get all slots
                    slots = page.locator(".ta-slots__slot")
                    slot_count = await slots.count()
                    print(f"[Timify] Processing week {week_idx+1}: Found {slot_count} raw slots.")
                    
                    for i in range(slot_count):
                        try:
                            slot_el = slots.nth(i)
                            
                            # Get time text
                            raw_time_text = await slot_el.inner_text() # e.g. "09:40\nSome hidden text"
                            
                            # Extract HH:MM
                            time_match = re.search(r"(\d{1,2}:\d{2})", raw_time_text)
                            if not time_match:
                                continue
                            time_str = time_match.group(1)
                            
                            # Get date from aria-labelledby
                            aria_label = await slot_el.get_attribute("aria-labelledby")
                            
                            if aria_label:
                                match = re.search(r"ta-slot-(\d{4}-\d{2}-\d{2})", aria_label)
                                if match:
                                    date_str = match.group(1)
                                    
                                    # Normalize 9:40 to 09:40
                                    if len(time_str) == 4: time_str = "0" + time_str
                                    
                                    # Combine
                                    full_iso = f"{date_str}T{time_str}:00"
                                    try:
                                        # Validate ISO
                                        datetime.fromisoformat(full_iso)
                                        unique_slots.add(full_iso)
                                    except:
                                        pass
                        except Exception as e:
                            # Stale element or other minor error
                            pass
                    
                    # Next week
                    next_btn = page.locator(".ta-datepicker__next")
                    if await next_btn.is_visible() and await next_btn.is_enabled():
                        await next_btn.click()
                        await page.wait_for_timeout(2000) # Wait for slots to load
                        
                        # Wait for slots to stabilize?
                        try:
                            await page.wait_for_selector(".ta-slots__slot", timeout=5000)
                        except:
                            # Maybe no slots next week
                            pass
                    else:
                        break # No more weeks
                
                if unique_slots:
                    self.doctor.slots = sorted(list(unique_slots))
                    print(f"[Timify] Found {len(self.doctor.slots)} total slots.")
                else:
                    print("[Timify] No slots found.")

            except Exception as e:
                print(f"[Timify] UI Error: {e}")
                
            await browser.close()
        
        return [self.doctor]
