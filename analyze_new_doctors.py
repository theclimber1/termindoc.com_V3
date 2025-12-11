import asyncio
from playwright.async_api import async_playwright

async def find_ids(url, name):
    print(f"\n--- Inspecting {name} ({url}) ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def handle_request(request):
            if request.resource_type in ["xhr", "fetch"]:
                print(f"[{name}] Request: {request.url}")
            
        page.on("request", handle_request)
        
        try:
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5)
            
            buttons = await page.query_selector_all("button")
            for btn in buttons:
                text = await btn.inner_text()
                if "Termin" in text or "buchen" in text.lower():
                    print(f"[{name}] Clicking button: {text}")
                    await btn.click()
                    await asyncio.sleep(5)
                    break 
                    
        except Exception as e:
            print(f"[{name}] Error: {e}")
            
        await browser.close()

async def analyze_site(url, name):
    print(f"\n--- Analyzing {name} ({url}) ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            content = await page.content()
            print(f"[{name}] Page Title: {await page.title()}")
            
            # Check for iframes (common for embedded booking tools)
            iframes = await page.query_selector_all("iframe")
            print(f"[{name}] Found {len(iframes)} iframes.")
            for frame in iframes:
                src = await frame.get_attribute("src")
                print(f"[{name}] Iframe Src: {src}")
                
            # Check for specific booking keywords
            if "latido" in content.lower():
                print(f"[{name}] Detected 'latido' in content.")
            if "doctena" in content.lower():
                print(f"[{name}] Detected 'doctena' in content.")
            if "mednanny" in content.lower():
                print(f"[{name}] Detected 'mednanny' in content.")
                
        except Exception as e:
            print(f"[{name}] Error: {e}")
        await browser.close()

async def main():
    # Dr. Kletz (Latido Debug)
    await find_ids("https://patient.latido.at/arzt/_OA_Dr._Marco_Kletz", "Dr. Kletz")
    
    # New Sites
    await analyze_site("https://www.hautarzt-aichinger.at/", "Dr. Aichinger")
    await analyze_site("https://perfect-smile.at/online-terminvereinbarung/", "Perfect Smile")

if __name__ == "__main__":
    asyncio.run(main())
