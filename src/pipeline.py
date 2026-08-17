from datetime import datetime, timezone, timedelta
import subprocess
import sys


# ============================================================
# RUN PYTHON MODULE
# ============================================================

def run_step(
    module,
    arguments=None
):

    if arguments is None:
        arguments = []

    command = [
        sys.executable,
        "-m",
        module
    ] + arguments

    print("\n" + "=" * 60)
    print(
        f"RUNNING: {module}"
    )
    print("=" * 60)

    print(
        "Command:",
        " ".join(command)
    )

    result = subprocess.run(
        command,
        check=False
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Pipeline step failed: "
            f"{module}"
        )

    print(
        f"\nCOMPLETED: {module}"
    )


# ============================================================
# GET PREVIOUS UTC DATE
# ============================================================

def get_previous_date():

    today = datetime.now(
        timezone.utc
    ).date()

    previous_day = (
        today - timedelta(days=1)
    )

    return previous_day.strftime(
        "%Y-%m-%d"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("FLIGHT DATA DAILY PIPELINE")
    print("=" * 60)

    # --------------------------------------------------------
    # Determine previous UTC day
    # --------------------------------------------------------

    processing_date = (
        get_previous_date()
    )

    print(
        f"\nProcessing previous UTC day: "
        f"{processing_date}"
    )

    # ========================================================
    # STEP 1 — OPENSKY BACKFILL
    # ========================================================

    run_step(
        "src.ingestion.opensky",
        [
            "--backfill"
        ]
    )

    # ========================================================
    # STEP 2 — SILVER CLEANING
    # ========================================================

    run_step(
        "src.transform.silver.clean",
        [
            "--date",
            processing_date
        ]
    )

    # ========================================================
    # STEP 3 — AIRPORT ENRICHMENT
    # ========================================================

    run_step(
        "src.transform.silver.enrich_airports"
    )

    # ========================================================
    # STEP 4 — GOLD AGGREGATION
    # ========================================================

    run_step(
        "src.transform.gold.aggregate",
        [
            "--date",
            processing_date
        ]
    )

    # ========================================================
    # COMPLETED
    # ========================================================

    print("\n" + "=" * 60)
    print("DAILY FLIGHT PIPELINE COMPLETED")
    print("=" * 60)

    print(
        f"\nSuccessfully processed: "
        f"{processing_date}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()   