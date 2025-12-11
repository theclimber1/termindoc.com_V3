import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
import json

async def find_ids_for_url(name, url):
    print(f"\n--- Processing {name} ---")
    print(f"URL: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        found_ids = None
        
        # Intercept freeslots requests
        async def handle_request(request):
            nonlocal found_ids
            if "freeslots" in request.url and not found_ids:
                print(f"[{name}] Intercepted freeslots: {request.url}")
                parsed = urlparse(request.url)
                params = parse_qs(parsed.query)
                
                doc_id = params.get('doctorid', [None])[0]
                cal_id = params.get('calendarid', [None])[0]
                type_id = params.get('typeid', [None])[0]
                
                if doc_id and cal_id and type_id:
                    found_ids = {
                        "doctor_id": doc_id,
                        "calendar_id": cal_id,
                        "type_id": type_id
                    }
                    print(f"[{name}] SUCCESS! Found IDs: {found_ids}")

        page.on("request", handle_request)

        try:
            await page.goto(url, wait_until="networkidle")
            
            # Handle Cookie Banner
            try:
                buttons = await page.query_selector_all("button")
                for btn in buttons:
                    text = await btn.inner_text()
                    if any(x in text for x in ["Akzeptieren", "Alle akzeptieren", "Zustimmen"]):
                        await btn.click()
                        print(f"[{name}] Clicked cookie banner")
                        break
            except:
                pass
            
            await asyncio.sleep(2)
            
            # Check if we already found IDs
            if not found_ids:
                print(f"[{name}] IDs not found yet, trying to click 'Termin buchen'...")
                
                # Try clicking the specific booking button found in HTML
                clicked = False
                for selector in ["button[test-tag='schedule-appointment-button']", "button[test-tag='startBookingBtn']"]:
                    try:
                        if await page.is_visible(selector):
                            print(f"[{name}] Clicking {selector}...")
                            await page.click(selector)
                            clicked = True
                            break
                    except:
                        pass
                
                if clicked:
                    print(f"[{name}] Waiting for service selection...")
                    await asyncio.sleep(3)
                    
                    # Look for service selection buttons
                    service_selector = "button[test-tag='choose-appointment-type']"
                    
                    try:
                        # Wait for at least one service button to appear
                        await page.wait_for_selector(service_selector, timeout=5000)
                        
                        service_buttons = await page.query_selector_all(service_selector)
                        if service_buttons:
                            print(f"[{name}] Found {len(service_buttons)} service buttons, clicking the first one...")
                            await service_buttons[0].click()
                            await asyncio.sleep(3)
                        else:
                            print(f"[{name}] No service buttons found after wait.")
                            
                    except Exception as e:
                        print(f"[{name}] Error waiting for/clicking service button: {e}")
                        # Dump HTML if failed
                        content = await page.content()
                        with open(f"{name.replace(' ', '_')}_service_fail.html", "w") as f:
                            f.write(content)

                else:
                    print(f"[{name}] 'Termin buchen' button not found/visible.")
                    # Dump HTML
                    content = await page.content()
                    with open(f"{name.replace(' ', '_')}_no_button_dump.html", "w") as f:
                        f.write(content)

            # Wait a bit more
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[{name}] Error: {e}")
            
        await browser.close()
        return found_ids

async def main():
    doctors = [
        {"name": "PVE Kumberg", "url": "https://patient.latido.at/arzt/_PVE_Kumberg"},
        {"name": "Dr. Franziska Winder", "url": "https://patient.latido.at/arzt/_Winder"},
        {"name": "Dr. Florian Ensat", "url": "https://patient.latido.at/arzt/_Ensat"},
        {"name": "Dr. Christian Walcher", "url": "https://patient.latido.at/arzt/_Walcher"},
        {"name": "Dr. Max Zacherl", "url": "https://patient.latido.at/arzt/_M.A."},
        {"name": "Dr. Martin Rief", "url": "https://patient.latido.at/arzt/_Rief"},
        {"name": "Dr. Wolfgang Sauseng", "url": "https://patient.latido.at/arzt/_Sauseng"}
    ]

    results = {}
    for doc in doctors:
        ids = await find_ids_for_url(doc["name"], doc["url"])
        if ids:
            results[doc["name"]] = ids
        else:
            results[doc["name"]] = "Not Found"

    print("\n\n=== FINAL RESULTS ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
