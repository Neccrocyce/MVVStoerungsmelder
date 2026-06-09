from dataclasses import dataclass, field

from src.mvv_stoerungsmelder.models.disruption import TransportMode, DisruptionType


@dataclass
class UserSetting:
    """
    Represents a user setting for receiving notifications about disruptions in the Munich public transport area (MVV/MVG/S-Bahn).
    """

    # Set of disruption types the user wants to receive notifications for (see :class:DisruptionType)
    disruption_types: set[DisruptionType] = field(default_factory=set, init=False)

    # Set of transport modes the user wants to receive notifications for (see :class:TransportMode)
    transport_modes: set[TransportMode] = field(default_factory=set, init=False)

    # Set of lines the user wants to receive notifications for
    lines: set[str] = field(default_factory=set, init=False)

    # Whether the user wants to receive notifications about planned disruptions up front
    # True: 1 week before the disruption starts and when it starts
    # False: only when the disruption starts or is ongoing
    notify_planned: bool = True

    # Whether the user wants to receive updates to ongoing disruptions
    notify_ongoing: bool = False

    # Whether the user wants to receive notifications about cleared disruptions as soon as they are cleared
    notify_cleared: bool = True

    # Whether the user wants detailed notifications with descriptions and references, or only short notifications with title and type
    detailed_notifications: bool = True





