"""
Global constants for the MVVStoerungsmelder application.

This module contains all configuration constants used throughout the application,
such as API endpoints, timeouts, and notification settings.
"""

# ========================
# API Configuration
# ========================

# URL for fetching disruptions from the MVG API
API_URL_MVG = "https://www.mvg.de/api/bgw-pt/v3/messages"

# Timeout for API requests (in seconds)
API_REQUEST_TIMEOUT = 10

# ========================
# Notification Settings
# ========================

# Number of days a planned disruption should be notified in advance
# (e.g. 7 means that planned disruptions will be notified up to 7 days before they start)
NOTIFICATION_DAYS = 7

UNIQUE_IDENTIFIERS = {
    "title",
    "affected_lines",
    "affected_stations"
}

# ========================
# Time Zone Settings
# ========================

# Default timezone for datetime conversions
DEFAULT_TIMEZONE = "Europe/Berlin"



