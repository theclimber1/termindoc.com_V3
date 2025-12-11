import json
import re
import asyncio
import pytz
from datetime import datetime
from playwright.async_api import async_playwright
from main import SCRAPER_MAP, load_all_registries

async def extract_first_time_from_page(page):
    """
    Sucht nach dem ersten Text auf der Seite, der wie eine Uhrzeit aussieht (HH:MM).
    """
    try:
        # Warte kurz, bis Inhalte geladen sind
        await page.wait_for_load_state("networkidle", timeout=5000)
        await asyncio.sleep(2) # Sicherheits-Sleep für Animationen

        # Hole den gesamten sichtbaren Text der Seite
        content_text = await page.inner_text("body")

        # Suche nach Uhrzeit-Muster: 1 oder 2 Ziffern, Doppelpunkt, 2 Ziffern (z.B. 9:00 oder 14:30)
        match = re.search(r'\b([0-2]?[0-9]:[0-5][0-9])\b', content_text)
        
        if match:
            return match.group(1) # Gibt z.B. "09:30" zurück
        return None
    except Exception as e:
        return None

def normalize_time(time_str):
    """Macht aus '9:30' ein '09:30' für den Vergleich"""
    if not time_str: return None
    parts = time_str.split(":")
    return f"{int(parts[0]):02d}:{parts[1]}"

async def verify_precise():
    doctors = load_all_registries()
    
    doctors = [d for d in doctors if "booking_url" in d and d["booking_url"]]

    print(f"🕵️‍♀️ Starte PRÄZISIONS-CHECK für {len(doctors)} Ärzte...")
    print(f"{'Name':<30} | {'Backend (API)':<15} | {'Frontend (Web)':<15} | {'Resultat'}")
    print("-" * 85)

    local_tz = pytz.timezone("Europe/Vienna")

    async with async_playwright() as p:
        # headless=True für Speed, False zum Zuschauen
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        for doctor in doctors:
            name = doctor['name'][:28]
            
            # 1. API DATEN LADEN
            backend_times = set()
            try:
                scraper_type = doctor.get("scraper_type")
                if scraper_type in SCRAPER_MAP:
                    scraper_cls = SCRAPER_MAP[scraper_type]
                    scraper = scraper_cls(doctor)
                    
                    # Run async scrape directly
                    results = await scraper.scrape()
                    
                    # Extrahiere alle Uhrzeiten
                    for doc_obj in results:
                        for slot_str in doc_obj.slots:
                            if isinstance(slot_str, str):
                                try:
                                    # Parse ISO
                                    if slot_str.endswith("Z"):
                                        dt_utc = datetime.fromisoformat(slot_str.replace("Z", "+00:00"))
                                    else:
                                        dt_utc = datetime.fromisoformat(slot_str)
                                    
                                    # Convert to Local Time
                                    if dt_utc.tzinfo:
                                        dt_local = dt_utc.astimezone(local_tz)
                                    else:
                                        dt_local = dt_utc 
                                    
                                    backend_times.add(dt_local.strftime("%H:%M"))
                                except ValueError:
                                    pass
            except Exception as e:
                # print(f"API Error: {e}")
                backend_times = set()

            # 2. BROWSER CHECK
            frontend_time = "---"
            try:
                await page.goto(doctor['booking_url'], timeout=15000)
                
                found_time = await extract_first_time_from_page(page)
                if found_time:
                    frontend_time = normalize_time(found_time)
            except Exception:
                frontend_time = "Error"

            # 3. VERGLEICH
            status = "❓"
            
            if len(backend_times) == 0 and (frontend_time == "---" or frontend_time is None):
                 status = "✅ BEIDE LEER"
            elif len(backend_times) > 0 and frontend_time in backend_times:
                status = "✅ MATCH"
            elif len(backend_times) > 0 and frontend_time == "---":
                status = "❌ GHOST (API hat Daten, Web zeigt nix)"
            elif len(backend_times) == 0 and frontend_time != "---" and frontend_time != "Error":
                status = "⚠️ MISSING (Web hat Zeit, API leer)"
            elif frontend_time not in backend_times and frontend_time != "---":
                status = "⚠️ MISMATCH (Zeiten weichen ab)"

            # Ausgabe formatieren
            backend_sample = "Keine"
            if backend_times:
                sorted_times = sorted(list(backend_times))
                if frontend_time in backend_times:
                    backend_sample = frontend_time 
                else:
                    backend_sample = sorted_times[0] 

            print(f"{name:<30} | {backend_sample:<15} | {str(frontend_time):<15} | {status}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_precise())
