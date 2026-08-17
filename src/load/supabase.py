import os

import pandas as pd
import psycopg2

from dotenv import load_dotenv
from psycopg2.extras import execute_values


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return psycopg2.connect(
        host=os.getenv("SUPABASE_DB_HOST"),
        port=os.getenv("SUPABASE_DB_PORT"),
        database=os.getenv("SUPABASE_DB_NAME"),
        user=os.getenv("SUPABASE_DB_USER"),
        password=os.getenv("SUPABASE_DB_PASSWORD")
    )


# ============================================================
# CONVERT NaN TO NONE
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return None

    return value


# ============================================================
# LOAD AIRPORT TRAFFIC
# ============================================================

def load_airport_traffic(
    connection,
    file_path
):

    df = pd.read_csv(
        file_path
    )

    print(
        f"Airport rows to load: {len(df)}"
    )

    records = []

    for row in df.itertuples(
        index=False
    ):

        records.append(
            (
                clean_value(row.flight_date),
                clean_value(row.airport),
                clean_value(row.country),
                clean_value(row.departures),
                clean_value(row.departure_aircraft),
                clean_value(row.arrivals),
                clean_value(row.arrival_aircraft),
                clean_value(row.total_traffic),
                clean_value(row.unique_aircraft)
            )
        )

    query = """
        INSERT INTO gold.airport_traffic (
            flight_date,
            airport,
            country,
            departures,
            departure_aircraft,
            arrivals,
            arrival_aircraft,
            total_traffic,
            unique_aircraft
        )
        VALUES %s

        ON CONFLICT (
            flight_date,
            airport
        )

        DO UPDATE SET
            country = EXCLUDED.country,
            departures = EXCLUDED.departures,
            departure_aircraft = EXCLUDED.departure_aircraft,
            arrivals = EXCLUDED.arrivals,
            arrival_aircraft = EXCLUDED.arrival_aircraft,
            total_traffic = EXCLUDED.total_traffic,
            unique_aircraft = EXCLUDED.unique_aircraft;
    """

    cursor = connection.cursor()

    execute_values(
        cursor,
        query,
        records,
        page_size=1000
    )

    connection.commit()

    cursor.close()

    print(
        "Airport load completed."
    )


# ============================================================
# LOAD COUNTRY TRAFFIC
# ============================================================

def load_country_traffic(
    connection,
    file_path
):

    df = pd.read_csv(
        file_path
    )

    print(
        f"Country rows to load: {len(df)}"
    )

    records = []

    for row in df.itertuples(
        index=False
    ):

        records.append(
            (
                clean_value(row.flight_date),
                clean_value(row.country),
                clean_value(row.departures),
                clean_value(row.departure_aircraft),
                clean_value(row.arrivals),
                clean_value(row.arrival_aircraft),
                clean_value(row.total_traffic),
                clean_value(row.unique_aircraft)
            )
        )

    query = """
        INSERT INTO gold.country_traffic (
            flight_date,
            country,
            departures,
            departure_aircraft,
            arrivals,
            arrival_aircraft,
            total_traffic,
            unique_aircraft
        )
        VALUES %s

        ON CONFLICT (
            flight_date,
            country
        )

        DO UPDATE SET
            departures = EXCLUDED.departures,
            departure_aircraft = EXCLUDED.departure_aircraft,
            arrivals = EXCLUDED.arrivals,
            arrival_aircraft = EXCLUDED.arrival_aircraft,
            total_traffic = EXCLUDED.total_traffic,
            unique_aircraft = EXCLUDED.unique_aircraft;
    """

    cursor = connection.cursor()

    execute_values(
        cursor,
        query,
        records,
        page_size=1000
    )

    connection.commit()

    cursor.close()

    print(
        "Country load completed."
    )


# ============================================================
# LOAD ROUTE TRAFFIC
# ============================================================

def load_route_traffic(
    connection,
    file_path
):

    df = pd.read_csv(
        file_path
    )

    print(
        f"Route rows to load: {len(df)}"
    )

    records = []

    for row in df.itertuples(
        index=False
    ):

        records.append(
            (
                clean_value(row.flight_date),
                clean_value(row.departure_airport),
                clean_value(row.arrival_airport),
                clean_value(row.route),
                clean_value(row.flight_count),
                clean_value(row.unique_aircraft)
            )
        )

    query = """
        INSERT INTO gold.route_traffic (
            flight_date,
            departure_airport,
            arrival_airport,
            route,
            flight_count,
            unique_aircraft
        )
        VALUES %s

        ON CONFLICT (
            flight_date,
            departure_airport,
            arrival_airport
        )

        DO UPDATE SET
            route = EXCLUDED.route,
            flight_count = EXCLUDED.flight_count,
            unique_aircraft = EXCLUDED.unique_aircraft;
    """

    cursor = connection.cursor()

    execute_values(
        cursor,
        query,
        records,
        page_size=1000
    )

    connection.commit()

    cursor.close()

    print(
        "Route load completed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    gold_dir = os.path.join(
        project_root,
        "data",
        "gold"
    )

    airport_file = os.path.join(
        gold_dir,
        "airport_traffic.csv"
    )

    country_file = os.path.join(
        gold_dir,
        "country_traffic.csv"
    )

    route_file = os.path.join(
        gold_dir,
        "route_traffic.csv"
    )

    print("=" * 60)
    print("STARTING GOLD → SUPABASE LOAD")
    print("=" * 60)

    connection = None

    try:

        connection = get_connection()

        print(
            "Connected to Supabase PostgreSQL"
        )

        # ----------------------------------------------------
        # Airport
        # ----------------------------------------------------

        load_airport_traffic(
            connection,
            airport_file
        )

        # ----------------------------------------------------
        # Country
        # ----------------------------------------------------

        load_country_traffic(
            connection,
            country_file
        )

        # ----------------------------------------------------
        # Route
        # ----------------------------------------------------

        load_route_traffic(
            connection,
            route_file
        )

        print("\n" + "=" * 60)
        print("GOLD → SUPABASE LOAD COMPLETED")
        print("=" * 60)

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            f"\nERROR: {error}"
        )

        raise

    finally:

        if connection:
            connection.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()