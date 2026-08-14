import csv
import requests
from datetime import datetime, timezone
from pathlib import Path


OPENSKY_URL = "https://opensky-network.org/api/states/all"

BRONZE_DIR = Path("data/bronze")


# OpenSky state vector column names
COLUMNS = [
    "icao24",
    "callsign",
    "origin_country",
    "time_position",
    "last_contact",
    "longitude",
    "latitude",
    "baro_altitude",
    "on_ground",
    "velocity",
    "true_track",
    "vertical_rate",
    "sensors",
    "geo_altitude",
    "squawk",
    "spi",
    "position_source"
]


def fetch_flight_data():

    response = requests.get(
        OPENSKY_URL,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_to_bronze(data):

    # Create Bronze directory if it doesn't exist
    BRONZE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Extract aircraft states
    states = data.get("states", [])

    # Create timestamp for this ingestion
    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d_%H-%M-%S")

    file_path = (
        BRONZE_DIR
        / f"opensky_{timestamp}.csv"
    )

    # Write aircraft data to CSV
    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        # Header
        writer.writerow(COLUMNS)

        # Aircraft records
        for state in states:

            writer.writerow(state)

    return file_path, len(states)


if __name__ == "__main__":

    print("Fetching data from OpenSky...")

    data = fetch_flight_data()

    file_path, row_count = save_to_bronze(data)

    print(
        f"Received {row_count} aircraft records."
    )

    print(
        f"Bronze data saved to: {file_path}"
    )