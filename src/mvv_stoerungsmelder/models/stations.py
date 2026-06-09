import csv
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Stations:
    stations: dict[str, str] = field(default_factory=dict, init=False)

    def __post_init__(self):
        # Load all stations from data/stations.csv and store in self.stations as list of dicts with "id" and "name" keys
        with open("../data/stations.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                self.stations[row["Globale ID"]] = row["Name ohne Ort"]

    def get_station_name_by_id(self, station_id: str) -> Optional[str]:
        if station_id not in self.stations:
            return None
        return self.stations.get(station_id)