import json
import os
from typing import List, Dict
from .models import Doctor

class DBManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(self.data_dir, "appointments.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_data(self) -> Dict[str, dict]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save_doctor(self, doctor: Doctor):
        data = self.load_data()
        
        # Convert Pydantic model to dict
        doc_dict = doctor.model_dump()
        
        # Check if doctor exists to merge slots logic if needed
        # For now, we overwrite/update the doctor entry
        # In a real scenario, we might want to merge slots intelligently
        
        # Overwrite the doctor entry to ensure we don't keep stale slots
        # and respect the limit set in main.py
        data[doctor.id] = doc_dict

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[DB] Saved/Updated doctor: {doctor.name} ({len(doc_dict['slots'])} slots)")

    def remove_stale_doctors(self, active_ids: List[str]):
        """Removes doctors from the DB that are not in the active_ids list."""
        data = self.load_data()
        
        # Find keys to remove
        keys_to_remove = [k for k in data.keys() if k not in active_ids]
        
        if not keys_to_remove:
            return
            
        for k in keys_to_remove:
            del data[k]
            print(f"[DB] Removed stale doctor: {k}")
            
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
