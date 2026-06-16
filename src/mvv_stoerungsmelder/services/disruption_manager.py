
import requests

from src.mvv_stoerungsmelder.models.disruption import Disruption
from src.mvv_stoerungsmelder.constants import API_URL_MVG, API_REQUEST_TIMEOUT, UNIQUE_IDENTIFIERS


class DisruptionManager:
    """Manage a collection of Disruption objects and fetching from provider APIs."""

    disruptions: list[Disruption]

    def __init__(self):
        self.disruptions: list[Disruption] = []

    def _fetch_disruptions_from_mvg(self):
        # Fetches disruptions from the MVG API
        response = requests.get(API_URL_MVG, timeout=API_REQUEST_TIMEOUT)
        response.raise_for_status()  # TODO check response status
        disruptions_json = response.json()

        disruptions = []

        # Parses disruptions_json into Disruption objects
        for item in disruptions_json:
            disruption = Disruption(
                title=item["title"],
                description=item["description"],
                disruption_type=item["type"],
                affected_lines={x["label"] for x in item["lines"]},
                affected_modes={x["transportType"] for x in item["lines"]},
                disruption_durations=[{"start": x["from"], "end": x.get("to", None)} for x in item["incidentDurations"]],
                references=[(x["text"], x["url"]) for x in item["links"]],
                affected_stations=set(item["stationGlobalIds"])
            )
            disruptions.append(disruption)

        return disruptions

    def update_disruptions(self):
        # Update self.disruptions with disruptions_new, which is a list of Disruption objects
        # If a disruption in disruptions_new has the same title and type as a disruption in self.disruptions, update the existing disruption with the new data
        # Otherwise, add the new disruption to self.disruptions
        disruptions_new = self._fetch_disruptions_from_mvg()

        for new_d in disruptions_new:
            for old_d in self.disruptions:
                for identifier in UNIQUE_IDENTIFIERS:
                    id_old = getattr(old_d, identifier)
                    id_new = getattr(new_d, identifier)
                    id_old = sorted(id_old) if isinstance(id_old, set) else id_old
                    id_new = sorted(id_new) if isinstance(id_new, set) else id_new
                    if id_old != id_new:
                        break
                else:
                    # TODO check for updates
                    old_d.description = new_d.description
                    old_d.affected_lines = new_d.affected_lines
                    old_d.affected_modes = new_d.affected_modes
                    old_d.disruption_durations = new_d.disruption_durations
                    old_d.references = new_d.references
                    old_d.affected_stations = new_d.affected_stations
                    break
            else:
                self.disruptions.append(new_d)
