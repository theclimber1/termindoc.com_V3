import asyncio
import sys
import os

# Ensure we can import modules from the current directory
sys.path.append(os.getcwd())

from scrapers.custom_aichinger import CustomAichingerScraper
from scrapers.custom_perfect_smile import CustomPerfectSmileScraper
from scrapers.latido import LatidoScraper

async def test_scrapers():
    print("--- Testing New Scrapers ---")

    # Test Kletz (Latido)
    print("\n[TEST] Dr. Marco Kletz (Latido)")
    kletz_config = {
        "id": "kletz_latido",
        "name": "Dr. Marco Kletz",
        "booking_url": "https://patient.latido.at/arzt/_OA_Dr._Marco_Kletz",
        "doctor_id": "67ebf690810bb835c4749889",
        "calendar_id": "67ebf694ba021b5fc672f7cc",
        "type_id": "67ebf693ef1f14c32de62983"
    }
    try:
        scraper = LatidoScraper(kletz_config)
        doctors = await scraper.scrape()
        for doc in doctors:
            print(f"  > Found doctor: {doc.name}")
            print(f"  > Slots found: {len(doc.slots)}")
            if doc.slots:
                print(f"  > First slot: {doc.slots[0]}")
    except Exception as e:
        print(f"  > ERROR: {e}")

    # Test Aichinger (Custom)
    print("\n[TEST] Dr. Helmut Aichinger (Custom)")
    aichinger_config = {
        "id": "aichinger_custom",
        "name": "Dr. Helmut Aichinger",
        "booking_url": "https://www.hautarzt-aichinger.at/",
        "scraper_type": "custom_aichinger"
    }
    try:
        scraper = CustomAichingerScraper(aichinger_config)
        doctors = await scraper.scrape()
        for doc in doctors:
            print(f"  > Found doctor: {doc.name}")
            print(f"  > Slots found: {len(doc.slots)}")
            if doc.slots:
                print(f"  > First slot: {doc.slots[0]}")
    except Exception as e:
        print(f"  > ERROR: {e}")

    # Test Perfect Smile (Custom)
    print("\n[TEST] Perfect Smile (Custom)")
    smile_config = {
        "id": "perfect_smile",
        "name": "Perfect Smile",
        "booking_url": "https://perfect-smile.at/online-terminvereinbarung/",
        "scraper_type": "custom_perfect_smile"
    }
    try:
        scraper = CustomPerfectSmileScraper(smile_config)
        doctors = await scraper.scrape()
        for doc in doctors:
            print(f"  > Found doctor: {doc.name}")
            print(f"  > Slots found: {len(doc.slots)}")
            print(f"  > Note: Should be 0 slots (login required)")
    except Exception as e:
        print(f"  > ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
