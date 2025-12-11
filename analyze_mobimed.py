import asyncio
from playwright.async_api import async_playwright

async def analyze_mobimed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("🔍 Navigating to Mobimed scheduler...")
        
        async def handle_response(response):
            if "json" in response.headers.get("content-type", ""):
                try:
                    print(f"\n📦 JSON RESPONSE: {response.url}")
                    print(f"   Request Headers: {response.request.headers}")
                    if "users" in response.url or "services" in response.url or "slots" in response.url:
                        body = await response.json()
                        print(f"   Body: {str(body)[:500]}")
                except:
                    pass

        page.on("response", handle_response)

        await page.goto("https://scheduler.mobimed.at/ensat/", timeout=30000)
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        
        # Select "Erstordination" (Value 21)
        print("🖱️ Selecting 'Erstordination' (Value 21)...")
        try:
            # Find the select element. It likely has a specific class or ID, but we can try generic 'select'
            # or look for the select that contains this option.
            await page.select_option("select", "21")
            
            # Wait for reaction
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"❌ Selection failed: {e}")

        # Extract meta config
        import urllib.parse
        import json
        
        try:
            meta_element = await page.query_selector("meta[name='ultimed-scheduler/config/environment']")
            if meta_element:
                content_encoded = await meta_element.get_attribute("content")
                content_decoded = urllib.parse.unquote(content_encoded)
                print(f"\n🧩 Decoded Meta Config (FULL): {content_decoded}")
                
                # Parse JSON to check for token
                config_json = json.loads(content_decoded)
                # print keys
                print(f"   Config Keys: {config_json.keys()}")
                if "APP" in config_json:
                     print(f"   APP Config: {config_json['APP']}")
        except Exception as e:
            print(f"❌ Meta extraction failed: {e}")

        content = await page.content()
        print(f"\n📄 Page Content Preview: {content[:500]}...")
        
        # Check for iframes
        frames = page.frames
        print(f"\n🖼️ Found {len(frames)} frames.")
        for frame in frames:
            print(f"   Frame URL: {frame.url}")

        page.on("response", handle_response)

        await page.goto("https://scheduler.mobimed.at/ensat/", timeout=30000)
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        
        # Maybe we need to click something to trigger the fetch?
        # Let's take a screenshot to see what it looks like
        await page.screenshot(path="mobimed_debug.png")
        print("📸 Screenshot saved to mobimed_debug.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_mobimed())
