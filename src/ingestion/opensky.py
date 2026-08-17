import csv
import os
import time
import argparse
import requests

from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# CONFIGURATION
# ============================================================

OPENSKY_URL = (
    "https://opensky-network.org/api/flights/all"
)

TOKEN_URL = (
    "https://auth.opensky-network.org/"
    "auth/realms/opensky-network/"
    "protocol/openid-connect/token"
)

CLIENT_ID = os.getenv(
    "OPENSKY_CLIENT_ID"
)

CLIENT_SECRET = os.getenv(
    "OPENSKY_CLIENT_SECRET"
)

BRONZE_DIR = (
    PROJECT_ROOT / "data" / "bronze"
)


# ============================================================
# API RESPONSE COLUMNS
# ============================================================

COLUMNS = [
    "icao24",
    "first_seen",
    "departure_airport",
    "last_seen",
    "arrival_airport",
    "callsign",
    "departure_airport_horiz_distance",
    "departure_airport_vert_distance",
    "arrival_airport_horiz_distance",
    "arrival_airport_vert_distance",
    "departure_airport_candidates",
    "arrival_airport_candidates",
]


# ============================================================
# VALIDATE CREDENTIALS
# ============================================================

def validate_credentials():

    if not CLIENT_ID:
        raise ValueError(
            "OPENSKY_CLIENT_ID is missing from .env"
        )

    if not CLIENT_SECRET:
        raise ValueError(
            "OPENSKY_CLIENT_SECRET is missing from .env"
        )


# ============================================================
# GET ACCESS TOKEN
# ============================================================

def get_access_token():

    print("Authenticating with OpenSky...")

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=30,
    )

    response.raise_for_status()

    token_data = response.json()

    access_token = token_data.get(
        "access_token"
    )

    if not access_token:
        raise RuntimeError(
            "OpenSky authentication succeeded "
            "but no access token was returned."
        )

    print("Authentication successful.")

    return access_token


# ============================================================
# GET LATEST COMPLETED HOUR
# ============================================================

def get_time_window():

    now = datetime.now(
        timezone.utc
    )

    end_time = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    start_time = (
        end_time - timedelta(hours=1)
    )

    return start_time, end_time


# ============================================================
# GET PREVIOUS UTC DAY
# ============================================================

def get_previous_day():

    today = datetime.now(
        timezone.utc
    ).date()

    previous_day = (
        today - timedelta(days=1)
    )

    return get_day_window(
        previous_day
    )


# ============================================================
# GET SPECIFIC UTC DAY
# ============================================================

def get_day_window(
    target_date
):

    start_time = datetime.combine(
        target_date,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    end_time = (
        start_time + timedelta(days=1)
    )

    return start_time, end_time


# ============================================================
# FETCH FLIGHTS
# ============================================================

def fetch_flight_data(
    begin,
    end,
    access_token,
):

    begin_timestamp = int(
        begin.timestamp()
    )

    end_timestamp = int(
        end.timestamp()
    )

    print(
        f"Fetching flights: "
        f"{begin.strftime('%Y-%m-%d %H:%M')} "
        f"→ "
        f"{end.strftime('%Y-%m-%d %H:%M')} UTC"
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        )
    }

    response = requests.get(
        OPENSKY_URL,
        params={
            "begin": begin_timestamp,
            "end": end_timestamp,
        },
        headers=headers,
        timeout=60,
    )

    # No flights found
    if response.status_code == 404:

        print(
            "No flight records found "
            "for this window."
        )

        return []

    # Authentication problem
    if response.status_code == 401:

        raise RuntimeError(
            "OpenSky authentication failed. "
            "Check your credentials."
        )

    # Rate limit / credits
    if response.status_code == 429:

        raise RuntimeError(
            "OpenSky API rate/credit limit "
            "was reached."
        )

    response.raise_for_status()

    data = response.json()

    return data if data else []


# ============================================================
# SAVE TO BRONZE
# ============================================================

def save_to_bronze(
    flights,
    start_time,
    end_time,
):

    BRONZE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    start_label = start_time.strftime(
        "%Y-%m-%d_%H-%M"
    )

    end_label = end_time.strftime(
        "%H-%M"
    )

    file_path = (
        BRONZE_DIR
        / (
            f"flights_"
            f"{start_label}"
            f"_to_"
            f"{end_label}.csv"
        )
    )

    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(COLUMNS)

        for flight in flights:

            writer.writerow([
                flight.get("icao24"),
                flight.get("firstSeen"),
                flight.get(
                    "estDepartureAirport"
                ),
                flight.get("lastSeen"),
                flight.get(
                    "estArrivalAirport"
                ),
                flight.get("callsign"),
                flight.get(
                    "estDepartureAirportHorizDistance"
                ),
                flight.get(
                    "estDepartureAirportVertDistance"
                ),
                flight.get(
                    "estArrivalAirportHorizDistance"
                ),
                flight.get(
                    "estArrivalAirportVertDistance"
                ),
                flight.get(
                    "departureAirportCandidatesCount"
                ),
                flight.get(
                    "arrivalAirportCandidatesCount"
                ),
            ])

    return file_path, len(flights)


# ============================================================
# NORMAL INGESTION
# ============================================================

def run_normal_ingestion(
    access_token,
):

    print("=" * 60)
    print("NORMAL FLIGHT INGESTION")
    print("=" * 60)

    start_time, end_time = (
        get_time_window()
    )

    flights = fetch_flight_data(
        start_time,
        end_time,
        access_token,
    )

    file_path, row_count = (
        save_to_bronze(
            flights,
            start_time,
            end_time,
        )
    )

    print()
    print(
        f"Received {row_count} "
        f"flight records."
    )

    print(
        f"Bronze file: {file_path}"
    )


# ============================================================
# BACKFILL A COMPLETE DAY
# ============================================================

def run_backfill(
    access_token,
    target_date=None,
):

    print("=" * 60)
    print("FLIGHT DATA BACKFILL")
    print("=" * 60)

    # --------------------------------------------------------
    # Choose date
    # --------------------------------------------------------

    if target_date is None:

        day_start, day_end = (
            get_previous_day()
        )

    else:

        day_start, day_end = (
            get_day_window(
                target_date
            )
        )

    print()

    print(
        f"Backfilling:"
    )

    print(
        f"{day_start} → {day_end}"
    )

    window_size = timedelta(
        hours=2
    )

    current_start = day_start

    total_flights = 0
    total_files = 0

    while current_start < day_end:

        current_end = min(
            current_start + window_size,
            day_end,
        )

        window_number = (
            total_files + 1
        )

        print()
        print("-" * 60)

        print(
            f"Window {window_number}/12"
        )

        try:

            flights = fetch_flight_data(
                current_start,
                current_end,
                access_token,
            )

            file_path, row_count = (
                save_to_bronze(
                    flights,
                    current_start,
                    current_end,
                )
            )

            total_flights += row_count
            total_files += 1

            print(
                f"Received: {row_count} flights"
            )

            print(
                f"Saved: {file_path}"
            )

        except requests.exceptions.HTTPError as error:

            print(
                f"ERROR in window "
                f"{window_number}: {error}"
            )

            raise

        current_start = current_end

        # Avoid hammering the API
        if current_start < day_end:
            time.sleep(2)

    print()
    print("=" * 60)
    print("BACKFILL COMPLETED")
    print("=" * 60)

    print(
        f"Target date: "
        f"{day_start.strftime('%Y-%m-%d')}"
    )

    print(
        f"Total Bronze files: "
        f"{total_files}"
    )

    print(
        f"Total flight records: "
        f"{total_flights}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "OpenSky flight data ingestion"
        )
    )

    parser.add_argument(
        "--backfill",
        action="store_true",
        help=(
            "Download the complete "
            "previous UTC day"
        ),
    )

    parser.add_argument(
        "--date",
        type=str,
        help=(
            "Download a specific UTC day "
            "in YYYY-MM-DD format"
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Check credentials
    # --------------------------------------------------------

    validate_credentials()

    # --------------------------------------------------------
    # Authenticate once
    # --------------------------------------------------------

    access_token = get_access_token()

    # --------------------------------------------------------
    # Specific date
    # --------------------------------------------------------

    if args.date:

        try:

            target_date = datetime.strptime(
                args.date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            raise ValueError(
                "Invalid date format. "
                "Use YYYY-MM-DD."
            )

        run_backfill(
            access_token,
            target_date,
        )

    # --------------------------------------------------------
    # Previous day
    # --------------------------------------------------------

    elif args.backfill:

        run_backfill(
            access_token
        )

    # --------------------------------------------------------
    # Normal hourly ingestion
    # --------------------------------------------------------

    else:

        run_normal_ingestion(
            access_token
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()