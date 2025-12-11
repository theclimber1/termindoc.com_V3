from abc import ABC, abstractmethod
from typing import List
from core.models import Doctor

class BaseScraper(ABC):
    def __init__(self, doctor_config: dict):
        """
        Initialisiert den Scraper mit der Konfiguration für einen spezifischen Arzt.
        :param doctor_config: Ein Dictionary mit Schlüsseln wie 'id', 'name', 'url', etc.
        """
        self.config = doctor_config
        self.doctor_id = doctor_config.get('id')
        self.doctor_name = doctor_config.get('name')
        self.url = doctor_config.get('url')

    @abstractmethod
    async def scrape(self) -> List[Doctor]:
        """
        Führt den Scraping-Vorgang aus und gibt eine Liste von Doctor-Objekten zurück.
        Muss asynchron implementiert sein.
        """
        pass
