from playwright.sync_api import sync_playwright
import json

def analyze_timesloth():
    url = "https://shop.timesloth.io/de/a/dr-schmidmayr/MHFBKJHRET3gALMawVRO?backButton=true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Navigating to {url}...")
        
        # Capture network requests
        page.on("request", lambda request: print(f">> {request.method} {request.url}"))
        
        def handle_response(response):
            if "api.timesloth.io" in response.url and "slots" in response.url:
                print(f"!! FOUND SLOTS API: {response.url}")
                try:
                    json_data = response.json()
                    print("!! JSON RESPONSE:")
                    print(json.dumps(json_data, indent=2))
                except:
                    print("!! Could not parse JSON")

        page.on("response", handle_response)

        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # Dump HTML
        with open("timesloth_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print("HTML dumped to timesloth_dump.html")
        browser.close()

if __name__ == "__main__":
    analyze_timesloth()
