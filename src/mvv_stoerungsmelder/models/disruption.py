from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from zoneinfo import ZoneInfo


class TransportMode(Enum):
    S_BAHN = "SBAHN"
    U_BAHN = "UBAHN"
    TRAM = "Tram"
    MVG_BUS = "BUS"
    REGIONAL_BUS = "REGIONAL_BUS"
    BAHN = "BAHN"
    OTHER = "OTHER"

class DisruptionType(Enum):
    INCIDENT = "INCIDENT"
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    OTHER = "OTHER"

class MessageStatus(Enum):
    NOT_SENT = 0
    SENT_PLANNED = 1
    SENT_STARTING_SOON = 2
    SENT_ONGOING = 3
    SENT_CLEARED = 4


def _datetime_from_milliseconds(value: int) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromtimestamp(
        value / 1000,
        tz=ZoneInfo("Europe/Berlin")
    )
    dt = dt.astimezone(timezone.utc)
    return dt


@dataclass
class Disruption:
    """
    Represents a disruption in the Munich public transport area (MVV/MVG/S-Bahn).
    """

    # Short description of the disruption
    title: str

    # Long description of the disruption
    description: str

    # Type of disruption (see :class:DisruptionType)
    disruption_type: DisruptionType

    # All lines affected by the disruption (e.g. ["S1", "S2"])
    affected_lines: set[str]

    # The transport mode affected by the disruption (see :class:TransportMode)
    affected_modes: set[TransportMode]

    # All start and end times of the disruption stored as list of dicts with "start" and "end" keys, e.g.,
    # [{"start": 1700000000, "end": 1700003600}, {"start": 1700007200, "end": 1700010800}]
    disruption_durations: list[dict[str, Optional[datetime]]]

    # [Optional] Reference URL(s) for the disruption stored as list of tuples (description, url)
    references: list[tuple[str, str]] = field(default_factory=list)

    # [Optional] Global ID of the Stations affected by the disruption
    affected_stations: set[str] = field(default_factory=list)

    # Stores whether the disruption has been sent as a message to users, and if so, at which stage (planned, starting soon, ongoing, cleared)
    message_status: MessageStatus = field(default=MessageStatus.NOT_SENT, init=False)

    def __post_init__(self):
        # Parse disruption type if given as string
        if isinstance(self.disruption_type, str):
            try:
                self.disruption_type = DisruptionType(self.disruption_type)
            except ValueError:
                self.disruption_type = DisruptionType.OTHER

        # Parse affected modes if given as strings
        normalized_modes = set()
        for mode in self.affected_modes:
            if isinstance(mode, TransportMode):
                normalized_modes.add(mode)
            elif isinstance(mode, str):
                try:
                    normalized_modes.add(TransportMode(mode))
                except ValueError:
                    normalized_modes.add(TransportMode.OTHER)
            else:
                normalized_modes.add(TransportMode.OTHER)
        self.affected_modes = normalized_modes

        # Normalize datetimes
        normalized_durations = []
        for d in self.disruption_durations:
            start = d["start"]
            end = d["end"]
            if isinstance(start, int):
                start = _datetime_from_milliseconds(start)
            if isinstance(end, int):
                end = _datetime_from_milliseconds(end)
            normalized_durations.append({"start": start, "end": end})
        self.disruption_durations = normalized_durations

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "disruption_type": self.disruption_type.value,
            "affected_lines": list(self.affected_lines),
            "affected_modes": [mode.value for mode in self.affected_modes],
            "disruption_durations": [
                {"start": d["start"].isoformat(), "end": d["end"].isoformat()}
                for d in self.disruption_durations
            ],
            "references": self.references,
            "affected_stations": list(self.affected_stations),
            "message_status": self.message_status.value
        }

    def _handle_unknown_values(self, value: str):
        # TODO
        pass

    # @classmethod
    # def from_dict(cls, data: dict[str, Any]) -> Disruption:
    #     # Accepts dictionaries coming from APIs or stored JSON
    #     kw = data.copy()
    #     # convert modes (list of str) to set
    #     modes = kw.get("affected_modes")
    #     if modes is not None:
    #         kw["affected_modes"] = set(modes)
    #     # parse datetimes -- constructor handles parsing
    #     return cls(**kw)

    # def is_active_at(self, when: Optional[datetime] = None) -> bool:
    #     if when is None:
    #         when = datetime.now(timezone.utc)
    #     if self.start_time and self.end_time:
    #         return self.start_time <= when <= self.end_time
    #     if self.start_time and not self.end_time:
    #         return self.start_time <= when
    #     # no times -> fallback to status
    #     return self.status == Status.ONGOING
    #
    # def affects_line(self, line: str) -> bool:
    #     return line in self.affected_lines
    #
    # def overlaps_with(self, other: "Disruption") -> bool:
    #     # returns True if time windows overlap or share at least one line
    #     if any(l in other.affected_lines for l in self.affected_lines):
    #         # check time overlap if both have times
    #         if self.start_time and self.end_time and other.start_time and other.end_time:
    #             latest_start = max(self.start_time, other.start_time)
    #             earliest_end = min(self.end_time, other.end_time)
    #             return latest_start <= earliest_end
    #         return True
    #     return False


