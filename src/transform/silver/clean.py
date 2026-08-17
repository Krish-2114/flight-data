import numpy as np
import pandas as pd

from datetime import datetime, timezone
from pathlib import Path
import argparse


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

BRONZE_DIR = (
    PROJECT_ROOT
    / "data"
    / "bronze"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
)


# ============================================================
# FIND FLIGHT BRONZE FILES FOR PROCESSING DATE
# ============================================================

def get_bronze_files(processing_date):

    pattern = (
        f"flights_{processing_date}_*.csv"
    )

    files = sorted(
        BRONZE_DIR.glob(pattern)
    )

    if not files:

        raise FileNotFoundError(
            f"No Bronze flight files found "
            f"for {processing_date}."
        )

    return files


# ============================================================
# LOAD BRONZE FILES
# ============================================================

def load_bronze(files):

    dataframes = []

    for file in files:

        print(
            f"Reading Bronze file: "
            f"{file.name}"
        )

        df = pd.read_csv(
            file
        )

        # Keep track of source batch
        df["bronze_file"] = file.name

        dataframes.append(df)

    combined = pd.concat(
        dataframes,
        ignore_index=True
    )

    print(
        f"\nTotal Bronze rows: "
        f"{len(combined)}"
    )

    return combined


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean_columns(df):

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(
            " ",
            "_",
            regex=False
        )
    )

    return df


# ============================================================
# CLEAN STRING COLUMNS
# ============================================================

def clean_strings(df):

    string_columns = [
        "icao24",
        "callsign",
        "departure_airport",
        "arrival_airport"
    ]

    for column in string_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    # Convert empty strings to NaN

    df = df.replace(
        r"^\s*$",
        np.nan,
        regex=True
    )

    return df


# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

def convert_numeric_columns(df):

    numeric_columns = [
        "first_seen",
        "last_seen",
        "departure_airport_horiz_distance",
        "departure_airport_vert_distance",
        "arrival_airport_horiz_distance",
        "arrival_airport_vert_distance",
        "departure_airport_candidates",
        "arrival_airport_candidates"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


# ============================================================
# CONVERT UNIX TIMESTAMPS
# ============================================================

def convert_timestamps(df):

    df["departure_time"] = pd.to_datetime(
        df["first_seen"],
        unit="s",
        utc=True,
        errors="coerce"
    )

    df["arrival_time"] = pd.to_datetime(
        df["last_seen"],
        unit="s",
        utc=True,
        errors="coerce"
    )

    return df


# ============================================================
# VALIDATE FLIGHT DATA
# ============================================================

def validate_data(df):

    # --------------------------------------------------------
    # Arrival cannot happen before departure
    # --------------------------------------------------------

    invalid_time = (
        df["departure_time"].notna()
        &
        df["arrival_time"].notna()
        &
        (
            df["arrival_time"]
            <
            df["departure_time"]
        )
    )

    df.loc[
        invalid_time,
        [
            "departure_time",
            "arrival_time"
        ]
    ] = pd.NaT

    # --------------------------------------------------------
    # Airport distances cannot be negative
    # --------------------------------------------------------

    distance_columns = [
        "departure_airport_horiz_distance",
        "departure_airport_vert_distance",
        "arrival_airport_horiz_distance",
        "arrival_airport_vert_distance"
    ]

    for column in distance_columns:

        df.loc[
            df[column] < 0,
            column
        ] = np.nan

    return df


# ============================================================
# REMOVE DUPLICATE FLIGHT RECORDS
# ============================================================

def remove_duplicates(df):

    before = len(df)

    # Aircraft + first_seen + last_seen
    # represents the flight record grain.

    df = df.drop_duplicates(
        subset=[
            "icao24",
            "first_seen",
            "last_seen"
        ]
    )

    after = len(df)

    print(
        f"Duplicates removed: "
        f"{before - after}"
    )

    print(
        f"Rows after deduplication: "
        f"{after}"
    )

    return df


# ============================================================
# CALCULATE FLIGHT DURATION
# ============================================================

def add_flight_duration(df):

    df["flight_duration_minutes"] = (
        (
            df["arrival_time"]
            -
            df["departure_time"]
        )
        .dt.total_seconds()
        / 60
    )

    # Negative durations should not exist

    df.loc[
        df["flight_duration_minutes"] < 0,
        "flight_duration_minutes"
    ] = np.nan

    return df


# ============================================================
# CREATE ROUTE
# ============================================================

def add_route(df):

    valid_route = (
        df["departure_airport"].notna()
        &
        df["arrival_airport"].notna()
    )

    df["route"] = pd.NA

    df.loc[
        valid_route,
        "route"
    ] = (
        df.loc[
            valid_route,
            "departure_airport"
        ]
        + " -> "
        + df.loc[
            valid_route,
            "arrival_airport"
        ]
    )

    return df


# ============================================================
# ADD TIME FEATURES
# ============================================================

def add_time_features(df):

    df["flight_date"] = (
        df["departure_time"]
        .dt.date
    )

    df["departure_hour"] = (
        df["departure_time"]
        .dt.hour
    )

    return df


# ============================================================
# ADD PIPELINE METADATA
# ============================================================

def add_metadata(df):

    df["processed_at"] = datetime.now(
        timezone.utc
    )

    return df


# ============================================================
# SELECT FINAL SILVER COLUMNS
# ============================================================

def select_silver_columns(df):

    columns = [
        "icao24",
        "callsign",
        "departure_airport",
        "arrival_airport",
        "departure_time",
        "arrival_time",
        "flight_duration_minutes",
        "route",
        "flight_date",
        "departure_hour",
        "bronze_file",
        "processed_at"
    ]

    return df[
        columns
    ]


# ============================================================
# SAVE SILVER
# ============================================================

def save_silver(df):

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        SILVER_DIR
        / "flights.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Silver flight transformation"
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
    print("STARTING SILVER FLIGHT TRANSFORMATION")
    print("=" * 60)

    print(
        f"\nProcessing date: "
        f"{processing_date}"
    )

    # --------------------------------------------------------
    # 1. Find Bronze files ONLY for this date
    # --------------------------------------------------------

    bronze_files = get_bronze_files(
        processing_date
    )

    print(
        f"\nBronze flight files found: "
        f"{len(bronze_files)}"
    )

    # --------------------------------------------------------
    # 2. Load Bronze
    # --------------------------------------------------------

    df = load_bronze(
        bronze_files
    )

    # --------------------------------------------------------
    # 3. Clean column names
    # --------------------------------------------------------

    df = clean_columns(df)

    # --------------------------------------------------------
    # 4. Clean strings
    # --------------------------------------------------------

    df = clean_strings(df)

    # --------------------------------------------------------
    # 5. Convert numeric columns
    # --------------------------------------------------------

    df = convert_numeric_columns(df)

    # --------------------------------------------------------
    # 6. Convert timestamps
    # --------------------------------------------------------

    df = convert_timestamps(df)

    # --------------------------------------------------------
    # 7. Validate data
    # --------------------------------------------------------

    df = validate_data(df)

    # --------------------------------------------------------
    # 8. Remove duplicates
    # --------------------------------------------------------

    df = remove_duplicates(df)

    # --------------------------------------------------------
    # 9. Calculate flight duration
    # --------------------------------------------------------

    df = add_flight_duration(df)

    # --------------------------------------------------------
    # 10. Create route
    # --------------------------------------------------------

    df = add_route(df)

    # --------------------------------------------------------
    # 11. Add time features
    # --------------------------------------------------------

    df = add_time_features(df)

    # --------------------------------------------------------
    # 12. Add metadata
    # --------------------------------------------------------

    df = add_metadata(df)

    # --------------------------------------------------------
    # 13. Select final Silver columns
    # --------------------------------------------------------

    df = select_silver_columns(df)

    # --------------------------------------------------------
    # 14. Save Silver
    # --------------------------------------------------------

    output_file = save_silver(
        df
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 60)
    print("SILVER TRANSFORMATION COMPLETED")
    print("=" * 60)

    print(
        f"Processing date: "
        f"{processing_date}"
    )

    print(
        f"Bronze files processed: "
        f"{len(bronze_files)}"
    )

    print(
        f"Final Silver rows: "
        f"{len(df)}"
    )

    print(
        f"Flights with departure airport: "
        f"{df['departure_airport'].notna().sum()}"
    )

    print(
        f"Flights with arrival airport: "
        f"{df['arrival_airport'].notna().sum()}"
    )

    print(
        f"Flights with complete route: "
        f"{df['route'].notna().sum()}"
    )

    print(
        f"Silver file: "
        f"{output_file}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()