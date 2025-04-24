import json
import os
from typing import Dict, List


class MemoryStorage:
    def __init__(self, file_path: str = "sessions.json"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def save_trip(self, user_input: Dict, itinerary: Dict) -> None:
        trips = self.load_trips()
        trips.append({"input": user_input, "itinerary": itinerary})
        with open(self.file_path, "w") as f:
            json.dump(trips, f, indent=4)

    def load_trips(self) -> List[Dict]:
        with open(self.file_path, "r") as f:
            return json.load(f)