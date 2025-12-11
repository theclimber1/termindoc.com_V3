import json
import asyncio
from datetime import datetime, timedelta
from typing import List
from core.models import Doctor
from .base import BaseScraper
from playwright.async_api import async_playwright

class MedineumScraper(BaseScraper):
    async def scrape(self) -> List[Doctor]:
        print(f"[Medineum] Scraping {self.doctor_name}...")
        
        institution_id = self.config.get("institution_id")
        appt_type_id = self.config.get("appointment_type_id")
        api_url = "https://de.cgmlife.com/Appointment/AppointmentService/getNextPossibleProposals"
        
        slots = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                token_future = asyncio.Future()
                
                async def handle_request(request):
                    # Only capture token from the specific API call we care about, or after full load
                    if 'cgm-identity' in request.headers and not token_future.done():
                        # Verify it's not empty
                        val = request.headers['cgm-identity']
                        if len(val) > 10:
                            token_future.set_result(val)

                page.on("request", handle_request)
                
                try:
                    await page.goto("https://de.cgmlife.com/eservices/#/?institution=ef406de6-589d-494b-8200-9ed7de4dc914", wait_until="networkidle", timeout=30000)
                    # Wait a bit more to ensure we have the latest token
                    await asyncio.sleep(3)
                    token = await asyncio.wait_for(token_future, timeout=10)
                except Exception as e:
                    print(f"[Medineum] Failed to get token: {e}")
                    await browser.close()
                    return []

                # Fetch Loop
                heute = datetime.now()
                ende = heute + timedelta(days=365)
                current_start_date = heute.strftime("%Y-%m-%d")
                datum_ende_str = ende.strftime("%Y-%m-%d")
                
                max_loops = 5 # Reduced for demo speed
                loop_count = 0
                
                # Fetch Loop using page.evaluate to ensure cookies are used
                heute = datetime.now()
                ende = heute + timedelta(days=365)
                current_start_date = heute.strftime("%Y-%m-%d")
                datum_ende_str = ende.strftime("%Y-%m-%d")
                
                max_loops = 5
                loop_count = 0
                
                while loop_count < max_loops:
                    loop_count += 1
                    
                    # We pass the payload and url to the browser
                    # We use fetch() inside the browser
                    js_code = """
                        async (args) => {
                            const response = await fetch(args.url, {
                                method: 'POST',
                                headers: {
                                    'cgm-identity': args.token,
                                    'accept': 'application/json',
                                    'content-type': 'application/json'
                                },
                                body: JSON.dumps(args.payload)
                            });
                            return await response.json();
                        }
                    """
                    
                    payload = [
                        institution_id,
                        [appt_type_id],
                        current_start_date,
                        datum_ende_str,
                        None, None, None
                    ]
                    
                    try:
                        # Execute fetch in browser
                        # Return raw details to debug
                        resp_data = await page.evaluate("""
                            async ({url, token, payload}) => {
                                const response = await fetch(url, {
                                    method: 'POST',
                                    headers: {
                                        'cgm-identity': token,
                                        'accept': 'application/json',
                                        'content-type': 'application/json'
                                    },
                                    body: JSON.stringify(payload)
                                });
                                const text = await response.text();
                                return {
                                    status: response.status,
                                    url: response.url,
                                    text: text
                                };
                            }
                        """, {"url": api_url, "token": token, "payload": payload})
                        
                        if resp_data['status'] != 200:
                            print(f"[Medineum] API Error: {resp_data['status']}")
                            break
                            
                        try:
                            proposals = json.loads(resp_data['text'])
                        except:
                            break
                            
                        for prop in proposals:
                            date_str = prop.get('date')
                            time_str = prop.get('time')
                            try:
                                # Time format is HH:MM:SS
                                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                                slots.append(dt.isoformat())
                            except ValueError:
                                # Fallback for HH:MM
                                try:
                                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                                    slots.append(dt.isoformat())
                                except:
                                    pass
                            except Exception as e:
                                print(f"[Medineum Debug] Date parse error: {e}")
                                
                        if not proposals:
                            break

                        # Next date logic
                        last_prop = proposals[-1]
                        last_date = datetime.strptime(last_prop.get('date'), "%Y-%m-%d")
                        next_start = last_date + timedelta(days=1)
                        if next_start > ende:
                            break
                        current_start_date = next_start.strftime("%Y-%m-%d")
                        
                        await asyncio.sleep(0.2)
                        
                    except Exception as e:
                        print(f"[Medineum] Fetch error: {e}")
                        break
                
                await browser.close()
                    
        except Exception as e:
            print(f"[Medineum] Error: {e}")
            
        doctor = Doctor(
            id=self.doctor_id,
            name=self.doctor_name,
            address=self.config.get("address", "Klagenfurt"),
            speciality=self.config.get("speciality", "Allgemeinmedizin"),
            insurance=self.config.get("insurance", ["Alle Kassen"]),
            slots=slots,
            booking_url=self.config.get("booking_url", "")
        )
        print(f"[Medineum] Found {len(slots)} slots.")
        return [doctor]
