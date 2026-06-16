from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional

from src.mvv_stoerungsmelder.constants import NOTIFICATION_DAYS, UNIQUE_IDENTIFIERS
from src.mvv_stoerungsmelder.utils.datetime_utils import datetime_from_milliseconds, datetime_now


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


class DisruptionStatus(Enum):
    # Planned disruption that will not start within the next 7 days
    PLANNED = 0

    # Planned disruption that will start within the next 7 days
    UPCOMING = 1

    # Disruption that has started and is currently ongoing
    ACTIVE = 2

    # Disruption that is no longer active and there is no upcoming disruption planned
    CLEARED = 3

    # Disruption that is no longer listed in the API
    NOT_FOUND = 4



class NotificationType(Enum):
    # No notification should be sent
    NONE = "NONE"

    # A disruption has entered the 7-day announcement window and should be announced to users
    ANNOUNCEMENT = "ANNOUNCEMENT"

    # A disruption has become active and is now affecting service
    ACTIVATION = "ACTIVATION"

    # An existing disruption has changed (e.g. description, affected lines, start/end time, durations, etc.)
    UPDATE = "UPDATE"

    # A disruption has temporarily ended is no longer affecting service at the time of the update
    TEMP_CLEARANCE = "TEMP_CLEARANCE"

    # A disruption has (temporarily) ended or has been removed and is no longer affecting service at the time of the update
    CLEARANCE = "CLEARANCE"

    # A disruption that was planned has been canceled and will not occur
    CANCELLATION = "CANCELLATION"


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
    # TODO define as set
    disruption_durations: list[dict[str, Optional[datetime]]]

    # [Optional] Reference URL(s) for the disruption stored as list of tuples (description, url)
    # TODO define as set
    references: list[tuple[str, str]] = field(default_factory=list)

    # [Optional] Global ID of the Stations affected by the disruption
    affected_stations: set[str] = field(default_factory=list)

    # Stores the current status of this disruption
    status: DisruptionStatus = field(default=DisruptionStatus.PLANNED, init=False, compare=False)

    # Stores the type of notification that should be sent to users based on the latest update to this disruption
    notification: NotificationType = field(default=NotificationType.NONE, init=False, compare=False)

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
                start = datetime_from_milliseconds(start)
            if isinstance(end, int):
                end = datetime_from_milliseconds(end)
            normalized_durations.append({"start": start, "end": end})
        self.disruption_durations = normalized_durations

        # TODO Update status

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
            "message_status": self.status.value
        }

    def _compute_status(self) -> DisruptionStatus:
        """
        Compute the current status of the disruption based on its durations and the current time.
        """
        now = datetime_now()

        # check if disruption is not found or cleared
        if self.status == DisruptionStatus.NOT_FOUND:
            return DisruptionStatus.NOT_FOUND

        # check if disruption is cleared
        # If the disruption is already marked as cleared, we keep it as cleared regardless of the durations.
        if self.status == DisruptionStatus.CLEARED:
            return DisruptionStatus.CLEARED

        # If there are no durations, we consider the disruption as active until it is explicitly cleared.
        if not self.disruption_durations:
            return DisruptionStatus.ACTIVE

        # A disruption is considered cleared if all of its durations have ended
        # (i.e. for all durations, end is not None and end <= now).
        is_cleared = all(d["end"] is not None and d["end"] <= now for d in self.disruption_durations)
        if is_cleared:
            return DisruptionStatus.CLEARED

        # A disruption is active if at least one of its durations is active.
        is_active = any(
            (d["start"] is None or d["start"] <= now) and   # check if started (treat missing start as already started)
            (d["end"] is None or d["end"] > now)            # check if not ended (treat missing end as ongoing)
            for d in self.disruption_durations
        )
        if is_active:
            return DisruptionStatus.ACTIVE

        # A disruption is upcoming if it is not active and at least one of its durations starts within the next 7 days
        # (i.e. exists x: now <= x.start <= now + 7 days).
        window_end = now + timedelta(days=NOTIFICATION_DAYS)
        is_upcoming = any(
            (d["start"] is not None and now <= d["start"] <= window_end) for d in self.disruption_durations
        )
        if is_upcoming:
            return DisruptionStatus.UPCOMING

        # A disruption is planned if it is not active and at least one of its durations starts more than 7 days from now
        # (i.e. exists x: now + 7 days < x.start).
        return DisruptionStatus.PLANNED

    def _compute_notification_type(self, old_status, new_status):
        if old_status == new_status:
            return NotificationType.NONE

        if new_status == DisruptionStatus.PLANNED:
            if old_status == DisruptionStatus.UPCOMING:
                return NotificationType.NONE
            elif old_status == DisruptionStatus.ACTIVE:
                return NotificationType.TEMP_CLEARANCE
            else:
                raise ValueError("Invalid status transition from {} to {}".format(old_status, new_status))

        if new_status == DisruptionStatus.UPCOMING:
            if old_status == DisruptionStatus.PLANNED:
                return NotificationType.ANNOUNCEMENT
            elif old_status == DisruptionStatus.ACTIVE:
                return NotificationType.TEMP_CLEARANCE
            else:
                raise ValueError("Invalid status transition from {} to {}".format(old_status, new_status))

        if new_status == DisruptionStatus.ACTIVE:
            if old_status in [DisruptionStatus.PLANNED, DisruptionStatus.UPCOMING]:
                return NotificationType.ACTIVATION
            else:
                raise ValueError("Invalid status transition from {} to {}".format(old_status, new_status))

        if new_status == DisruptionStatus.CLEARED:
            if old_status in DisruptionStatus.PLANNED:
                return NotificationType.NONE
            elif old_status == DisruptionStatus.UPCOMING:
                return NotificationType.CANCELLATION
            elif old_status == DisruptionStatus.ACTIVE:
                return NotificationType.CLEARANCE
            else:
                raise ValueError("Invalid status transition from {} to {}".format(old_status, new_status))

        if new_status == DisruptionStatus.NOT_FOUND:
            if old_status in [DisruptionStatus.PLANNED, DisruptionStatus.CLEARED]:
                return NotificationType.NONE
            elif old_status == DisruptionStatus.UPCOMING:
                return NotificationType.CANCELLATION
            elif old_status == DisruptionStatus.ACTIVE:
                return NotificationType.CLEARANCE
            else:
                raise ValueError("Invalid status transition from {} to {}".format(old_status, new_status))

        raise ValueError("Invalid new status: {}".format(new_status))

    def update_status_and_notification(self):
        old_status = self.status
        new_status = self._compute_status()

        self.status = new_status
        self.notification = self._compute_notification_type(old_status, new_status)
        # TODO check for other changes that would trigger an update notification (e.g. description, affected lines, durations, etc.)

    def matches_disruption(self, other: Disruption) -> bool:
        # Check if this disruption matches another disruption based on the unique identifiers (e.g. title, affected lines, affected stations)
        return all(getattr(self, identifier) == getattr(other, identifier) for identifier in UNIQUE_IDENTIFIERS)


    def update_from(self, other: Disruption):
        # Update this disruption with the data from another disruption (e.g. a new version of the same disruption fetched from the API)
        # This should be used when we have determined that the other disruption is the same as this disruption
        if self != other:
            # TODO set notification type to UPDATE
            self.description = other.description
            self.affected_lines = other.affected_lines
            self.affected_modes = other.affected_modes
            self.disruption_durations = other.disruption_durations
            self.references = other.references
            self.affected_stations = other.affected_stations

        self.update_status_and_notification()

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

    def _handle_unknown_values(self, value: str):
        # TODO unknown values in the json responded by the API
        pass



