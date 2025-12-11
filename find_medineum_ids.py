import asyncio
from playwright.async_api import async_playwright
import json

async def find_ids():
    url = "https://de.cgmlife.com/eservices/#/appointment/?institution=ef406de6-589d-494b-8200-9ed7de4dc914"
    print(f"Visiting {url}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture responses to find the appointment types JSON
        async def handle_response(response):
            if "getInitConfig" in response.url:
                try:
                    data = await response.json()
                    with open("medineum_config.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("Saved medineum_config.json")
                except:
                    pass
                    
        page.on("response", handle_response)
        
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5) # Wait for SPA
        
        await page.screenshot(path="medineum_before_click.png")
        print("Saved medineum_before_click.png")
        
        # Try to find the dropdown or list
        # The user mentioned "Bitte wählen Sie eine Terminart"
        # We look for elements that might be the dropdown
        
        # Log all network requests
        async def handle_response(response):
            try:
                if response.request.resource_type in ["xhr", "fetch"]:
                    print(f"Response: {response.url}")
                    try:
                        data = await response.json()
                        s = json.dumps(data)
                        # Check for keywords
                        if "getBookingConfig" in response.url:
                            print(f"--- FOUND DOCTORS IN {response.url} ---")
                            with open("medineum_doctors.json", "w") as f:
                                json.dump(data, f, indent=2)
                            print("Saved medineum_doctors.json")
                        elif "Dr." in s or "27b98eb0" in s or "appointment" in s.lower():
                            print(f"--- MATCH IN {response.url} ---")
                            print(s[:500] + "...")
                    except:
                        pass
            except:
                pass
                
        page.on("response", handle_response)
        
        # Reload page to capture initial requests
        print("Reloading page...")
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(5)

        # Click dropdown
        try:
            print("Clicking dropdown...")
            dropdown = page.locator("text=Please select an appointment type")
            await dropdown.first.click()
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error clicking dropdown: {e}")
            
            # Now look for options
            # They are likely in a list or select
            # We dump all text content of potential list items
            
            # Strategy 1: Look for 'li' elements or elements with ng-repeat
            items = page.locator(".ui-select-choices-row-inner") # Common in Angular UI Select
            count = await items.count()
            
            if count == 0:
                # Fallback: Look for any clickable elements with doctor names
                items = page.locator("div[ng-click]")
                count = await items.count()
                
            print(f"Found {count} potential items.")
            
            for i in range(count):
                text = await items.nth(i).text_content()
                print(f"Item {i}: {text.strip()}")
                
                # Try to get the ID from the scope or attributes
                # This is tricky in pure scraping without inspecting network
                # But maybe we can see it in the HTML
                html = await items.nth(i).inner_html()
                print(f"HTML: {html[:100]}...")

        except Exception as e:
            print(f"Error interacting: {e}")
            
        # Also dump the full page content again just in case
        content = await page.content()
        with open("medineum_page_interactive.html", "w") as f:
            f.write(content)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_ids())
