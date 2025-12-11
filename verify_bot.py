import json
import time
import os
from playwright.sync_api import sync_playwright
from main import run_scraper_for_single_doctor, load_all_registries

def verify_doctors():
    # 1. Load the Registry
    doctors = load_all_registries()
    if not doctors:
        print("No doctors found in registry.")
        return

    # Filter doctors without URL
    doctors = [d for d in doctors if "booking_url" in d and d["booking_url"]]

    print(f"🔎 Starting visual verification for {len(doctors)} doctors...")

    with sync_playwright() as p:
        # Open browser visibly (headless=False)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        
        for i, doctor in enumerate(doctors):
            print(f"-------------------------------------------------")
            print(f"🏥 [{i+1}/{len(doctors)}] Checking: {doctor['name']}")

            # A) SCRAPING IN BACKGROUND
            print("   ... scraping data ...")
            try:
                scraped_slots = run_scraper_for_single_doctor(doctor) 
                count = len(scraped_slots)
            except Exception as e:
                print(f"❌ Error scraping: {e}")
                count = "ERROR"

            print(f"🤖 System says: {count} slots.")

            # B) OPEN BROWSER
            page = context.new_page()
            try:
                print(f"   ... opening {doctor['booking_url']} ...")
                page.goto(doctor['booking_url'], timeout=15000)
                page.wait_for_load_state("domcontentloaded")
                
                # Wait briefly for dynamic content
                time.sleep(2) 

                # C) INJECTION
                box_color = "green" if count != 0 and count != "ERROR" else "red"
                
                js_injection = f"""
                const div = document.createElement('div');
                div.style = 'position: fixed; top: 20px; right: 20px; background-color: {box_color}; color: white; padding: 15px; border-radius: 8px; font-family: sans-serif; font-weight: bold; font-size: 18px; z-index: 999999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); border: 3px solid white;';
                div.innerHTML = '🤖 Dashboard-Check<br><hr style="margin:5px 0">Found: {count} Slots<br><small>{doctor["name"]}</small>';
                document.body.appendChild(div);
                """
                page.evaluate(js_injection)

                print(f"👀 Please check the browser! Press ENTER for next doctor (or Ctrl+C to stop)...")
                input() 

            except Exception as e:
                print(f"⚠️ Could not open page: {e}")
            
            finally:
                page.close()

        browser.close()

if __name__ == "__main__":
    verify_doctors()
