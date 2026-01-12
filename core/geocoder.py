
import requests
import time

class GeocodingService:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'MedicalTerminFinder/3.0'
        }

    def geocode_address(self, address):
        """
        Geocodes an address string to (lat, lon).
        Returns None if not found or error.
        """
        if not address:
            return None
            
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'at' # Restrict to Austria
        }
        
        try:
            # Respect Nominatim usage policy (max 1 req/sec)
            # Since this is a client, we don't expect high load, but good to be safe if called in loop
            # However, dashboard calls it once per search usually.
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
            return None
            
        except Exception as e:
            print(f"Geocoding error for {address}: {e}")
            return None
