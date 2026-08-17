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
    / "flights.csv"
)

AIRPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "airports.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "flights_enriched.csv"
)


# ============================================================
# LOAD SILVER FLIGHTS
# ============================================================

def load_flights():

    print(
        f"Reading Silver file: {SILVER_FILE}"
    )

    df = pd.read_csv(
        SILVER_FILE
    )

    print(
        f"Silver rows: {len(df)}"
    )

    return df


# ============================================================
# LOAD AIRPORT REFERENCE
# ============================================================

def load_airports():

    print(
        f"Reading airport reference: "
        f"{AIRPORT_FILE}"
    )

    airports = pd.read_csv(
        AIRPORT_FILE,
        usecols=[
            "ident",
            "name",
            "iso_country",
            "icao_code",
            "iata_code"
        ]
    )

    return airports


# ============================================================
# CLEAN AIRPORT REFERENCE
# ============================================================

def clean_airports(airports):

    # Standardize column names

    airports.columns = (
        airports.columns
        .str.strip()
        .str.lower()
    )

    # Clean airport codes

    for column in [
        "ident",
        "icao_code",
        "iata_code"
    ]:

        airports[column] = (
            airports[column]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    # Clean country code

    airports["iso_country"] = (
        airports["iso_country"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    return airports


# ============================================================
# CREATE AIRPORT LOOKUP
# ============================================================

def create_airport_lookup(airports):

    # We primarily match using ICAO code.

    lookup = airports[
        [
            "icao_code",
            "iata_code",
            "name",
            "iso_country"
        ]
    ].copy()

    lookup = lookup.rename(
        columns={
            "icao_code": "airport_code",
            "iata_code": "airport_iata",
            "name": "airport_name",
            "iso_country": "country_code"
        }
    )

    # Remove rows without ICAO codes

    lookup = lookup[
        lookup["airport_code"].notna()
    ]

    # Remove duplicate airport codes

    lookup = lookup.drop_duplicates(
        subset=["airport_code"]
    )

    return lookup


# ============================================================
# ENRICH DEPARTURE AIRPORT
# ============================================================

def enrich_departure_airport(
    flights,
    lookup
):

    departure_lookup = lookup.rename(
        columns={
            "airport_code":
                "departure_airport",
            "airport_iata":
                "departure_iata",
            "airport_name":
                "departure_airport_name",
            "country_code":
                "departure_country"
        }
    )

    flights = flights.merge(
        departure_lookup,
        on="departure_airport",
        how="left"
    )

    return flights


# ============================================================
# ENRICH ARRIVAL AIRPORT
# ============================================================

def enrich_arrival_airport(
    flights,
    lookup
):

    arrival_lookup = lookup.rename(
        columns={
            "airport_code":
                "arrival_airport",
            "airport_iata":
                "arrival_iata",
            "airport_name":
                "arrival_airport_name",
            "country_code":
                "arrival_country"
        }
    )

    flights = flights.merge(
        arrival_lookup,
        on="arrival_airport",
        how="left"
    )

    return flights


# ============================================================
# SAVE ENRICHED SILVER
# ============================================================

def save_data(df):

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    return OUTPUT_FILE


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("STARTING AIRPORT ENRICHMENT")
    print("=" * 60)

    # Load
    flights = load_flights()

    airports = load_airports()

    # Clean
    airports = clean_airports(
        airports
    )

    # Create lookup
    lookup = create_airport_lookup(
        airports
    )

    print(
        f"Airport lookup rows: "
        f"{len(lookup)}"
    )

    # Departure enrichment
    flights = enrich_departure_airport(
        flights,
        lookup
    )

    # Arrival enrichment
    flights = enrich_arrival_airport(
        flights,
        lookup
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    departure_matched = (
        flights[
            "departure_airport_name"
        ].notna().sum()
    )

    arrival_matched = (
        flights[
            "arrival_airport_name"
        ].notna().sum()
    )

    print()
    print(
        f"Departure airports matched: "
        f"{departure_matched}"
    )

    print(
        f"Arrival airports matched: "
        f"{arrival_matched}"
    )

    # Save
    output_file = save_data(
        flights
    )

    print("\n" + "=" * 60)
    print("AIRPORT ENRICHMENT COMPLETED")
    print("=" * 60)

    print(
        f"Rows: {len(flights)}"
    )

    print(
        f"Output: {output_file}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()