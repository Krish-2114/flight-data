import argparse
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SILVER_FILE = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "flights_enriched.csv"
)

GOLD_DIR = (
    PROJECT_ROOT
    / "data"
    / "gold"
)


# ============================================================
# GOLD SCHEMAS
# ============================================================

AIRPORT_COLUMNS = [
    "flight_date",
    "airport",
    "country",
    "departures",
    "departure_aircraft",
    "arrivals",
    "arrival_aircraft",
    "total_traffic",
    "unique_aircraft"
]

COUNTRY_COLUMNS = [
    "flight_date",
    "country",
    "departures",
    "departure_aircraft",
    "arrivals",
    "arrival_aircraft",
    "total_traffic",
    "unique_aircraft"
]

ROUTE_COLUMNS = [
    "flight_date",
    "departure_airport",
    "arrival_airport",
    "route",
    "flight_count",
    "unique_aircraft"
]


# ============================================================
# LOAD ENRICHED SILVER DATA
# ============================================================

def load_data():

    print(
        f"Reading enriched Silver file:\n"
        f"{SILVER_FILE}"
    )

    if not SILVER_FILE.exists():

        raise FileNotFoundError(
            f"Silver file not found: {SILVER_FILE}"
        )

    df = pd.read_csv(
        SILVER_FILE
    )

    print(
        f"Silver rows loaded: {len(df)}"
    )

    return df


# ============================================================
# FILTER PROCESSING DATE
# ============================================================

def filter_processing_date(
    df,
    processing_date
):

    df["flight_date"] = (
        pd.to_datetime(
            df["flight_date"],
            errors="coerce"
        )
        .dt.strftime("%Y-%m-%d")
    )

    before = len(df)

    df = df[
        df["flight_date"] == processing_date
    ].copy()

    print(
        f"\nProcessing date: {processing_date}"
    )

    print(
        f"Rows before date filter: {before}"
    )

    print(
        f"Rows after date filter: {len(df)}"
    )

    if df.empty:

        raise ValueError(
            f"No Silver records found "
            f"for processing date "
            f"{processing_date}."
        )

    return df


# ============================================================
# CREATE AIRPORT TRAFFIC
# ============================================================

def create_airport_traffic(df):

    print(
        "\nCreating airport traffic..."
    )

    # --------------------------------------------------------
    # DEPARTURES
    # --------------------------------------------------------

    departures = (
        df[
            df["departure_airport"].notna()
        ]
        .groupby(
            [
                "flight_date",
                "departure_airport",
                "departure_country"
            ],
            as_index=False
        )
        .agg(
            departures=(
                "icao24",
                "count"
            ),

            departure_aircraft=(
                "icao24",
                "nunique"
            )
        )
        .rename(
            columns={
                "departure_airport": "airport",
                "departure_country": "country"
            }
        )
    )

    # --------------------------------------------------------
    # ARRIVALS
    # --------------------------------------------------------

    arrivals = (
        df[
            df["arrival_airport"].notna()
        ]
        .groupby(
            [
                "flight_date",
                "arrival_airport",
                "arrival_country"
            ],
            as_index=False
        )
        .agg(
            arrivals=(
                "icao24",
                "count"
            ),

            arrival_aircraft=(
                "icao24",
                "nunique"
            )
        )
        .rename(
            columns={
                "arrival_airport": "airport",
                "arrival_country": "country"
            }
        )
    )

    # --------------------------------------------------------
    # MERGE DEPARTURES + ARRIVALS
    # --------------------------------------------------------

    airport_traffic = pd.merge(
        departures,
        arrivals,
        on=[
            "flight_date",
            "airport",
            "country"
        ],
        how="outer"
    )

    # --------------------------------------------------------
    # FILL MISSING METRICS
    # --------------------------------------------------------

    metric_columns = [
        "departures",
        "arrivals",
        "departure_aircraft",
        "arrival_aircraft"
    ]

    for column in metric_columns:

        airport_traffic[column] = (
            airport_traffic[column]
            .fillna(0)
            .astype(int)
        )

    # --------------------------------------------------------
    # TOTAL TRAFFIC
    # --------------------------------------------------------

    airport_traffic["total_traffic"] = (
        airport_traffic["departures"]
        + airport_traffic["arrivals"]
    )

    # --------------------------------------------------------
    # UNIQUE AIRCRAFT
    # --------------------------------------------------------

    departure_aircraft = (
        df[
            df["departure_airport"].notna()
        ][
            [
                "flight_date",
                "departure_airport",
                "icao24"
            ]
        ]
        .rename(
            columns={
                "departure_airport": "airport"
            }
        )
    )

    arrival_aircraft = (
        df[
            df["arrival_airport"].notna()
        ][
            [
                "flight_date",
                "arrival_airport",
                "icao24"
            ]
        ]
        .rename(
            columns={
                "arrival_airport": "airport"
            }
        )
    )

    aircraft_data = pd.concat(
        [
            departure_aircraft,
            arrival_aircraft
        ],
        ignore_index=True
    )

    unique_aircraft = (
        aircraft_data
        .groupby(
            [
                "flight_date",
                "airport"
            ],
            as_index=False
        )
        .agg(
            unique_aircraft=(
                "icao24",
                "nunique"
            )
        )
    )

    airport_traffic = airport_traffic.merge(
        unique_aircraft,
        on=[
            "flight_date",
            "airport"
        ],
        how="left"
    )

    airport_traffic["unique_aircraft"] = (
        airport_traffic["unique_aircraft"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # ENFORCE SCHEMA
    # --------------------------------------------------------

    airport_traffic = airport_traffic[
        AIRPORT_COLUMNS
    ]

    airport_traffic = (
        airport_traffic
        .sort_values(
            "total_traffic",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return airport_traffic


# ============================================================
# CREATE COUNTRY TRAFFIC
# ============================================================

def create_country_traffic(df):

    print(
        "Creating country traffic..."
    )

    # --------------------------------------------------------
    # DEPARTURES
    # --------------------------------------------------------

    departures = (
        df[
            df["departure_country"].notna()
        ]
        .groupby(
            [
                "flight_date",
                "departure_country"
            ],
            as_index=False
        )
        .agg(
            departures=(
                "icao24",
                "count"
            ),

            departure_aircraft=(
                "icao24",
                "nunique"
            )
        )
        .rename(
            columns={
                "departure_country": "country"
            }
        )
    )

    # --------------------------------------------------------
    # ARRIVALS
    # --------------------------------------------------------

    arrivals = (
        df[
            df["arrival_country"].notna()
        ]
        .groupby(
            [
                "flight_date",
                "arrival_country"
            ],
            as_index=False
        )
        .agg(
            arrivals=(
                "icao24",
                "count"
            ),

            arrival_aircraft=(
                "icao24",
                "nunique"
            )
        )
        .rename(
            columns={
                "arrival_country": "country"
            }
        )
    )

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    country_traffic = pd.merge(
        departures,
        arrivals,
        on=[
            "flight_date",
            "country"
        ],
        how="outer"
    )

    metric_columns = [
        "departures",
        "arrivals",
        "departure_aircraft",
        "arrival_aircraft"
    ]

    for column in metric_columns:

        country_traffic[column] = (
            country_traffic[column]
            .fillna(0)
            .astype(int)
        )

    # --------------------------------------------------------
    # TOTAL TRAFFIC
    # --------------------------------------------------------

    country_traffic["total_traffic"] = (
        country_traffic["departures"]
        + country_traffic["arrivals"]
    )

    # --------------------------------------------------------
    # UNIQUE AIRCRAFT
    # --------------------------------------------------------

    departure_aircraft = (
        df[
            df["departure_country"].notna()
        ][
            [
                "flight_date",
                "departure_country",
                "icao24"
            ]
        ]
        .rename(
            columns={
                "departure_country": "country"
            }
        )
    )

    arrival_aircraft = (
        df[
            df["arrival_country"].notna()
        ][
            [
                "flight_date",
                "arrival_country",
                "icao24"
            ]
        ]
        .rename(
            columns={
                "arrival_country": "country"
            }
        )
    )

    aircraft_data = pd.concat(
        [
            departure_aircraft,
            arrival_aircraft
        ],
        ignore_index=True
    )

    unique_aircraft = (
        aircraft_data
        .groupby(
            [
                "flight_date",
                "country"
            ],
            as_index=False
        )
        .agg(
            unique_aircraft=(
                "icao24",
                "nunique"
            )
        )
    )

    country_traffic = country_traffic.merge(
        unique_aircraft,
        on=[
            "flight_date",
            "country"
        ],
        how="left"
    )

    country_traffic["unique_aircraft"] = (
        country_traffic["unique_aircraft"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # ENFORCE SCHEMA
    # --------------------------------------------------------

    country_traffic = country_traffic[
        COUNTRY_COLUMNS
    ]

    country_traffic = (
        country_traffic
        .sort_values(
            "total_traffic",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return country_traffic


# ============================================================
# CREATE ROUTE TRAFFIC
# ============================================================

def create_route_traffic(df):

    print(
        "Creating route traffic..."
    )

    valid_routes = df[
        df["departure_airport"].notna()
        &
        df["arrival_airport"].notna()
    ].copy()

    # --------------------------------------------------------
    # ROUTE AGGREGATION
    # --------------------------------------------------------

    route_traffic = (
        valid_routes
        .groupby(
            [
                "flight_date",
                "departure_airport",
                "arrival_airport",
                "route"
            ],
            as_index=False
        )
        .agg(
            flight_count=(
                "icao24",
                "count"
            )
        )
    )

    # --------------------------------------------------------
    # UNIQUE AIRCRAFT PER ROUTE
    # --------------------------------------------------------

    route_aircraft = (
        valid_routes[
            [
                "flight_date",
                "departure_airport",
                "arrival_airport",
                "icao24"
            ]
        ]
        .groupby(
            [
                "flight_date",
                "departure_airport",
                "arrival_airport"
            ],
            as_index=False
        )
        .agg(
            unique_aircraft=(
                "icao24",
                "nunique"
            )
        )
    )

    route_traffic = route_traffic.merge(
        route_aircraft,
        on=[
            "flight_date",
            "departure_airport",
            "arrival_airport"
        ],
        how="left"
    )

    route_traffic["unique_aircraft"] = (
        route_traffic["unique_aircraft"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # ENFORCE SCHEMA
    # --------------------------------------------------------

    route_traffic = route_traffic[
        ROUTE_COLUMNS
    ]

    route_traffic = (
        route_traffic
        .sort_values(
            "flight_count",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return route_traffic


# ============================================================
# SAVE HISTORICAL GOLD
# ============================================================

def save_gold(
    airport_traffic,
    country_traffic,
    route_traffic,
    processing_date
):

    GOLD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    airport_file = (
        GOLD_DIR
        / "airport_traffic.csv"
    )

    country_file = (
        GOLD_DIR
        / "country_traffic.csv"
    )

    route_file = (
        GOLD_DIR
        / "route_traffic.csv"
    )

    # ========================================================
    # AIRPORT
    # ========================================================

    if airport_file.exists():

        print(
            "\nExisting airport Gold found."
        )

        existing_airport = pd.read_csv(
            airport_file
        )

        # Remove the date being reprocessed.
        # This prevents duplicates.

        existing_airport = (
            existing_airport[
                existing_airport["flight_date"]
                .astype(str)
                != processing_date
            ]
        )

        airport_traffic = pd.concat(
            [
                existing_airport,
                airport_traffic
            ],
            ignore_index=True
        )

    # Explicit schema enforcement.
    # This also removes any obsolete columns
    # from an older Gold file.

    airport_traffic = airport_traffic[
        AIRPORT_COLUMNS
    ]

    airport_traffic = (
        airport_traffic
        .sort_values(
            [
                "flight_date",
                "total_traffic"
            ],
            ascending=[
                True,
                False
            ]
        )
        .reset_index(drop=True)
    )

    airport_traffic.to_csv(
        airport_file,
        index=False
    )

    # ========================================================
    # COUNTRY
    # ========================================================

    if country_file.exists():

        print(
            "Existing country Gold found."
        )

        existing_country = pd.read_csv(
            country_file
        )

        existing_country = (
            existing_country[
                existing_country["flight_date"]
                .astype(str)
                != processing_date
            ]
        )

        country_traffic = pd.concat(
            [
                existing_country,
                country_traffic
            ],
            ignore_index=True
        )

    country_traffic = country_traffic[
        COUNTRY_COLUMNS
    ]

    country_traffic = (
        country_traffic
        .sort_values(
            [
                "flight_date",
                "total_traffic"
            ],
            ascending=[
                True,
                False
            ]
        )
        .reset_index(drop=True)
    )

    country_traffic.to_csv(
        country_file,
        index=False
    )

    # ========================================================
    # ROUTE
    # ========================================================

    if route_file.exists():

        print(
            "Existing route Gold found."
        )

        existing_route = pd.read_csv(
            route_file
        )

        existing_route = (
            existing_route[
                existing_route["flight_date"]
                .astype(str)
                != processing_date
            ]
        )

        route_traffic = pd.concat(
            [
                existing_route,
                route_traffic
            ],
            ignore_index=True
        )

    route_traffic = route_traffic[
        ROUTE_COLUMNS
    ]

    route_traffic = (
        route_traffic
        .sort_values(
            [
                "flight_date",
                "flight_count"
            ],
            ascending=[
                True,
                False
            ]
        )
        .reset_index(drop=True)
    )

    route_traffic.to_csv(
        route_file,
        index=False
    )

    return (
        airport_file,
        country_file,
        route_file
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Create daily historical Gold "
            "flight traffic datasets"
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        help=(
            "Processing date in "
            "YYYY-MM-DD format"
        )
    )

    args = parser.parse_args()

    processing_date = args.date

    # ========================================================
    # START
    # ========================================================

    print("=" * 60)
    print("STARTING GOLD AGGREGATION")
    print("=" * 60)

    print(
        f"\nProcessing date: "
        f"{processing_date}"
    )

    # ========================================================
    # LOAD
    # ========================================================

    df = load_data()

    # ========================================================
    # FILTER DATE
    # ========================================================

    df = filter_processing_date(
        df,
        processing_date
    )

    # ========================================================
    # CREATE GOLD
    # ========================================================

    airport_traffic = (
        create_airport_traffic(df)
    )

    country_traffic = (
        create_country_traffic(df)
    )

    route_traffic = (
        create_route_traffic(df)
    )

    # ========================================================
    # SAVE HISTORICAL GOLD
    # ========================================================

    (
        airport_file,
        country_file,
        route_file
    ) = save_gold(
        airport_traffic,
        country_traffic,
        route_traffic,
        processing_date
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 60)
    print("GOLD AGGREGATION COMPLETED")
    print("=" * 60)

    print(
        f"\nProcessing date: "
        f"{processing_date}"
    )

    print(
        f"Airport records for this day: "
        f"{len(airport_traffic)}"
    )

    print(
        f"Country records for this day: "
        f"{len(country_traffic)}"
    )

    print(
        f"Route records for this day: "
        f"{len(route_traffic)}"
    )

    print("\nFiles updated:")

    print(
        f"Airport: {airport_file}"
    )

    print(
        f"Country: {country_file}"
    )

    print(
        f"Route: {route_file}"
    )

    # ========================================================
    # PREVIEW
    # ========================================================

    print("\n" + "-" * 60)
    print("TOP 10 AIRPORTS")
    print("-" * 60)

    print(
        airport_traffic
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "-" * 60)
    print("TOP 10 COUNTRIES")
    print("-" * 60)

    print(
        country_traffic
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "-" * 60)
    print("TOP 10 ROUTES")
    print("-" * 60)

    print(
        route_traffic
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()