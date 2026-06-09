#!/usr/bin/env python3
"""
Main entry point for the MVVStoerungsmelder application.

This script fetches and displays disruptions from the S-Bahn, MVG, and MVV networks.
"""
from src.mvv_stoerungsmelder.models.disruption import TransportMode
from src.mvv_stoerungsmelder.services.disruption_manager import DisruptionManager


def main():
    """Fetch and display disruptions from the MVG API."""
    print("Fetching disruptions from MVG API...")
    print("-" * 80)

    try:
        # Initialize the disruption manager, which automatically fetches from the API
        manager = DisruptionManager()

        # Display summary
        print(f"Found {len(manager.disruptions)} disruption(s)")
        print("-" * 80)

        # Display each disruption
        for i, disruption in enumerate(manager.disruptions, 1):
            if any(x in disruption.affected_modes for x in [TransportMode.REGIONAL_BUS, TransportMode.MVG_BUS]):
                continue

            if not TransportMode.S_BAHN in disruption.affected_modes:
                continue
            print(f"\nDisruption #{i}")
            print(f"  Title: {disruption.title}")
            print(f"  Type: {disruption.disruption_type.value}")
            print(f"  Description: {disruption.description[:100]}...")
            print(f"  Affected Lines: {', '.join(sorted(disruption.affected_lines))}")
            print(
                f"  Affected Modes: {', '.join(mode.value for mode in sorted(disruption.affected_modes, key=lambda m: m.value))}")
            print(f"  Status: {disruption.message_status.value}")

            # Display durations
            if disruption.disruption_durations:
                print(f"  Durations:")
                for duration in disruption.disruption_durations:
                    print(f"    - {duration['start']} to {duration['end']}")

            # Display references if available
            if disruption.references:
                print(f"  References:")
                for desc, url in disruption.references:
                    print(f"    - {desc}: {url}")

        print("-" * 80)
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()




