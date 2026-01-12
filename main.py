import asyncio
import json
import os
import glob
from core.database import DBManager
from scrapers.custom_palasser import CustomPalasserScraper
from scrapers.medineum import MedineumScraper
from scrapers.kutschera import KutscheraScraper
from scrapers.latido import LatidoScraper
from scrapers.custom_aichinger import CustomAichingerScraper
from scrapers.custom_perfect_smile import CustomPerfectSmileScraper

from scrapers.doctena import DoctenaScraper
from scrapers.timesloth import TimeslothScraper
from scrapers.mobimed import MobimedScraper
from scrapers.timify import TimifyScraper

# Factory Map: Mapping von String-Typ zu Klasse
SCRAPER_MAP = {
    "latido": LatidoScraper, # Generic Latido
    "custom_palasser": CustomPalasserScraper,
    "custom_aichinger": CustomAichingerScraper,
    "custom_perfect_smile": CustomPerfectSmileScraper,
    "medineum": MedineumScraper,
    "kutschera": KutscheraScraper,
    "doctena": DoctenaScraper,
    "timesloth": TimeslothScraper,
    "mobimed": MobimedScraper,
    "timify": TimifyScraper
}

def run_scraper_for_single_doctor(doctor_config):
    """
    Synchronous wrapper to run a single scraper for the verification bot.
    Returns a list of slots.
    """
    scraper_type = doctor_config.get("scraper_type")
    
    if scraper_type in SCRAPER_MAP:
        scraper_class = SCRAPER_MAP[scraper_type]
        scraper = scraper_class(doctor_config)
        
        try:
            # Run the async scrape method synchronously
            results = asyncio.run(scraper.scrape())
            
            # Collect all slots
            all_slots = []
            for doc in results:
                all_slots.extend(doc.slots)
            return all_slots
        except Exception as e:
            print(f"Error running scraper for {doctor_config.get('name')}: {e}")
            return []
    else:
        print(f"Unknown scraper type: {scraper_type}")
        return []

def load_all_registries():
    combined_registry = []
    
    # Pfad zum Ordner "registry"
    # Wir gehen davon aus, dass der Ordner im gleichen Verzeichnis wie main.py liegt
    registry_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry")
    
    if not os.path.exists(registry_path):
        print(f"⚠️ Registry folder not found at {registry_path}")
        return []

    # Suche alle .json Dateien in diesem Ordner
    files = glob.glob(os.path.join(registry_path, "*.json"))
    
    print(f"📂 Loading registry from {len(files)} files...")
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_registry.extend(data)
                    filename = os.path.basename(file_path)
                    print(f"   ✅ {filename}: {len(data)} doctors loaded.")
                else:
                    print(f"   ⚠️ {os.path.basename(file_path)} is not a list, skipping.")
        except Exception as e:
            print(f"   ❌ Error loading {file_path}: {e}")

    return combined_registry

async def main():
    registry = load_all_registries()
    
    if not registry:
        print("❌ No doctors found in registry!")
        return
    print("--- Starting Med-Aggregator (Registry Mode) ---")
    db_manager = DBManager()
    
    print(f"Loaded {len(registry)} doctors from registry.")
    
    # Cleanup stale entries
    active_ids = [doc.get("id") for doc in registry if "id" in doc]
    db_manager.remove_stale_doctors(active_ids)
    
    scraper_instances = []
    
    for doctor_config in registry:
        scraper_type = doctor_config.get("scraper_type")
        
        if scraper_type in SCRAPER_MAP:
            scraper_class = SCRAPER_MAP[scraper_type]
            # Instanziiere Scraper mit der Config
            scraper_instances.append(scraper_class(doctor_config))
        else:
            print(f"Warning: Unknown scraper type '{scraper_type}' for doctor {doctor_config.get('name')}")

    if not scraper_instances:
        print("No valid scrapers initialized.")
        return

    # Run all scrapers in parallel
    print(f"Running {len(scraper_instances)} scrapers...")
    
    tasks = [scraper.scrape() for scraper in scraper_instances]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            print(f"Scraper failed with error: {result}")
        elif result:
            # Result is a list of Doctor objects
            for doctor in result:
                # Limit to 50 slots per doctor as requested
                if len(doctor.slots) > 50:
                    doctor.slots = doctor.slots[:50]
                db_manager.save_doctor(doctor)
                
    print("--- Aggregation Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
