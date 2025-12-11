import asyncio
from playwright.async_api import async_playwright

async def inspect_doctena():
    url = "https://www.doctena.at/de/fachgebiet/zahnheilkunde-zahnarzt/dr-isabella-szalay-fasching-409749/ordination-dr-isabella-szalay-fasching-330910"
    print(f"Inspecting {url}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture requests
        async def handle_request(request):
            if "availabilities" in request.url or "slots" in request.url:
                print(f"Found availability request: {request.url}")
                
        page.on("request", handle_request)
        
        try:
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5)
            
            # Save HTML to file
            content = await page.content()
            with open("doctena_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Saved HTML to doctena_debug.html")
            
            # Try to click next week or something to trigger load
            buttons = await page.query_selector_all("button")
            print(f"Found {len(buttons)} buttons")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_doctena())
