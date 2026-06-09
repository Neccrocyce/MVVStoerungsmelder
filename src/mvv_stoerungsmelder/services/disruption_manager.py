import requests

from src.mvv_stoerungsmelder.models.disruption import Disruption

API_URL_MVG = "https://www.mvg.de/api/bgw-pt/v3/messages"


class DisruptionManager:
    """Manage a collection of Disruption objects and fetching from provider APIs."""

    disruptions: list[Disruption]

    def __init__(self):
        self.disruptions: list[Disruption] = []

    def fetch_disruptions_from_mvg(self):
        # Fetches disruptions from the MVG API
        response = requests.get(API_URL_MVG, timeout=10)
        response.raise_for_status()  # TODO check response status
        disruptions_json = response.json()

        # Parses disruptions_json into Disruption objects and store in self.disruptions
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
            self.disruptions.append(disruption) # TODO

    def update_disruptions(self, disruptions_new):
        pass
