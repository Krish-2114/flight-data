# ✈️ Flight Data Intelligence Pipeline & Analytics Dashboard

> An end-to-end aviation analytics platform that transforms raw OpenSky flight data into business-ready airport, country, and route intelligence using Python, PostgreSQL/Supabase, and Power BI.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811)


---

## 📑 Table of Contents

1. [Overview](#-overview)
2. [Dashboard Preview](#-dashboard-preview)
3. [Objectives](#-objectives)
4. [Technology Stack](#-technology-stack)
5. [Pipeline & Data Architecture](#-pipeline--data-architecture)
6. [Gold Analytical Datasets](#-gold-analytical-datasets)
7. [Power BI Dashboard Details](#-power-bi-dashboard-details)
8. [Project Structure](#-project-structure)
9. [Installation & Setup](#-installation--setup)
10. [Running the Pipeline](#-running-the-pipeline)
11. [Supabase / PostgreSQL](#-supabase--postgresql)
12. [Analytical Questions](#-analytical-questions)
13. [Key Concepts Demonstrated](#-key-concepts-demonstrated)
14. [Why Bronze → Silver → Gold?](#-why-bronze--silver--gold)
15. [Future Improvements](#-future-improvements)
16. [Data Sources](#-data-sources)
17. [Author](#-author)

---

## 📌 Overview

Modern aviation generates large volumes of operational data. Raw flight data, however, is not immediately suitable for analysis: it contains inconsistent fields, raw timestamps, missing values, bare airport codes, and low-level flight records.

This project builds a complete analytical pipeline that ingests flight data from the **OpenSky Network API**, processes it through a **Bronze → Silver → Gold** architecture, enriches it with airport reference data, loads the analytical datasets into **PostgreSQL/Supabase**, and presents the results in an interactive **Power BI** dashboard.

The goal is to turn raw flight records into actionable insights at the **airport, country, and route levels**.

---

## 📸 Dashboard Preview

The Power BI dashboard has four analytical pages. All pages support interactive filtering and cross-filtering.

### 🌎 1. Global Flight Traffic Overview

High-level snapshot of the flight network for a selected date: total traffic, countries, airports, routes, plus the top 10 airports, countries, and routes.

<img width="622" height="344" alt="image" src="https://github.com/user-attachments/assets/2852f965-a07c-43dc-9ec7-7e8a9477dbc6" />

### 🛫 2. Airport Traffic Analysis

Airport-level traffic ranking, departures vs. arrivals, and drill-down by country or airport.

<img width="622" height="344" alt="WhatsApp Image 2026-09-28 at 21 46 36" src="https://github.com/user-attachments/assets/114ef267-ce32-4f05-8613-1645283a722d" />

### 🌍 3. Route Intelligence

Route-level connectivity: top routes by flight count, aircraft activity per route, and a detailed departure–arrival route table.

<img width="622" height="344" alt="image" src="https://github.com/user-attachments/assets/8fc5a7ad-7707-41cf-83d7-69635c107e58" />

### 🛣️ 4. Country Traffic Analysis

Geographical view of flight activity with a global map, total traffic by country, and arrivals vs. departures.


<img width="622" height="344" alt="WhatsApp Image 2026-09-28 at 21 46 54" src="https://github.com/user-attachments/assets/f079c5a9-9c73-4cc4-b657-9dfc915e763b" />

---

## 🎯 Objectives

- Collect flight data from the OpenSky Network API
- Store raw API responses as Bronze data
- Clean and standardize flight records
- Handle timestamps, missing values, duplicates, and invalid records
- Calculate useful flight-level features
- Enrich flights with airport metadata
- Create analytical Gold datasets
- Analyze traffic at multiple business levels
- Load aggregated data into PostgreSQL/Supabase
- Build an interactive Power BI dashboard

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Data Source | OpenSky Network API |
| Programming | Python |
| Data Processing | Pandas |
| API Integration | Requests |
| Data Storage | CSV / PostgreSQL |
| Environment Management | Python-dotenv |
| Visualization | Microsoft Power BI |
| Version Control | Git / GitHub |

---

## 🏗️ Pipeline & Data Architecture

### End-to-End Flow

```text
                 ┌─────────────────────┐
                 │   OpenSky Network   │
                 │        API          │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       BRONZE        │
                 │   Raw Flight Data   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       SILVER        │
                 │ Cleaning & Feature  │
                 │    Engineering      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Airport Enrichment │
                 │  Reference Dataset  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │        GOLD         │
                 │ Analytical Datasets │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌─────────────────┐   ┌─────────────────┐
        │ PostgreSQL /    │   │   CSV Outputs   │
        │    Supabase     │   │                 │
        └────────┬────────┘   └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │    Power BI     │
        │    Dashboard    │
        └─────────────────┘
```

The complete daily pipeline is orchestrated through `src/pipeline.py`.

### 🥉 Bronze Layer — Raw Data

Stores flight data exactly as retrieved from the OpenSky API.

**Ingestion supports:**

- Normal hourly ingestion
- Previous-day backfills
- Specific date processing
- API authentication
- API error handling
- Rate-limit handling

**Raw records contain:**

- Aircraft ICAO identifier
- Callsign
- Departure and arrival airports
- First seen / last seen timestamps
- Airport distance information
- Airport candidate counts

```text
data/
└── bronze/
    └── flights_YYYY-MM-DD_HH-MM_to_HH-MM.csv
```

Raw data is kept separate from transformed data so downstream processing can be reproduced without repeatedly querying the API.

### 🥈 Silver Layer — Cleaning & Enrichment

Converts raw flight records into a clean analytical dataset.

**Data cleaning:**

- Standardizing column names
- Cleaning string values
- Converting numeric fields
- Converting Unix timestamps
- Validating records
- Removing duplicates
- Handling missing values

**Feature engineering:**

- Flight duration
- Flight date and hour
- Day-of-week information
- Route creation (e.g. `BOM → DEL`, `DEL → BLR`, `LHR → JFK`)
- Processing metadata

**Airport enrichment:**

Flight records are joined with an airport reference dataset, independently for both the departure and arrival airport, adding:

- Airport name
- IATA code
- ICAO code
- Country
- Country code

This lets the dashboard move beyond airport codes to meaningful geographical analysis.

### 🥇 Gold Layer — Business-Ready Data

Aggregated datasets designed specifically for analytics and visualization (see [Gold Analytical Datasets](#-gold-analytical-datasets)).

### Pipeline Steps

| Step | Stage | Description |
|---|---|---|
| 1 | OpenSky ingestion | OpenSky API → Bronze CSV |
| 2 | Silver transformation | Cleaning → Validation → Feature engineering |
| 3 | Airport enrichment | Silver flights + airport reference data |
| 4 | Gold aggregation | Airport, Country, and Route traffic datasets |
| 5 | Database loading | Gold CSV → Supabase PostgreSQL |
| 6 | Visualization | PostgreSQL → Power BI dashboard |

---

## 🧱 Gold Analytical Datasets

### 🛫 Airport Traffic

Daily traffic statistics for individual airports.

```text
flight_date | airport | country | departures | departure_aircraft |
arrivals | arrival_aircraft | total_traffic | unique_aircraft
```

### 🌍 Country Traffic

Flight activity aggregated by country.

```text
flight_date | country | departures | departure_aircraft |
arrivals | arrival_aircraft | total_traffic | unique_aircraft
```

### 🛣️ Route Traffic

Traffic statistics at the route level.

```text
flight_date | departure_airport | arrival_airport | route |
flight_count | unique_aircraft
```

---

## 📊 Power BI Dashboard Details

The Power BI layer sits on top of the Gold datasets:

```text
                    GOLD LAYER
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 Airport Traffic   Country Traffic   Route Traffic
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                PostgreSQL / Supabase
                        │
                        ▼
                    Power BI
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
     Airport         Country           Route
     Analysis        Analysis        Intelligence
```

### Page Breakdown

| Page | KPIs | Visualizations |
|---|---|---|
| **Global Overview** | Total Flight Traffic, Countries, Airports, Routes | Top 10 airports, countries, and routes by flight movements |
| **Airport Analysis** | Total Traffic, Departures, Arrivals, Total Aircraft | Airport ranking, departures vs. arrivals, airport comparison |
| **Country Analysis** | Total Traffic, Total Aircraft, Total Airports | Global activity map, traffic by country, arrivals vs. departures |
| **Route Intelligence** | Total Flights, Total Aircraft, Observed Routes | Top routes, route activity, aircraft activity, detailed route table |

### Interactive Features

**Filters** (depending on page): Date, Country, Airport, Departure Airport, Arrival Airport.

**Cross-filtering:** Selecting an airport, country, or route dynamically updates the relevant KPIs and visualizations across the page, so the dashboard works as an exploratory analytical tool rather than a static report.

---

## 📁 Project Structure

```text
flight-data/
│
├── assets/
│   └── dashboard/
│       ├── global-flight-traffic-overview.png
│       ├── airport-traffic-analysis.png
│       ├── country-traffic-analysis.png
│       └── route-intelligence.png
│
├── data/
│   └── reference/
│       └── airports.csv
│
├── src/
│   ├── ingestion/
│   │   └── opensky.py
│   ├── transform/
│   │   ├── silver/
│   │   │   ├── clean.py
│   │   │   └── enrich_airports.py
│   │   └── gold/
│   │       └── aggregate.py
│   ├── load/
│   │   ├── supabase.py
│   │   └── test_connection.py
│   └── pipeline.py
│
├── Flight_Data.pbix
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd flight-data
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENSKY_CLIENT_ID=your_opensky_client_id
OPENSKY_CLIENT_SECRET=your_opensky_client_secret

SUPABASE_DB_HOST=your_database_host
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=your_database_name
SUPABASE_DB_USER=your_database_user
SUPABASE_DB_PASSWORD=your_database_password
```



---

## ▶️ Running the Pipeline

### Full daily pipeline

```bash
python -m src.pipeline
```

The pipeline automatically determines the previous UTC date and runs: OpenSky Backfill → Silver Cleaning → Airport Enrichment → Gold Aggregation.

### Individual components

**OpenSky ingestion (hourly)**

```bash
python -m src.ingestion.opensky
```

**OpenSky previous-day backfill**

```bash
python -m src.ingestion.opensky --backfill
```

**Silver transformation (specific date)**

```bash
python -m src.transform.silver.clean --date 2026-09-27
```

**Airport enrichment**

```bash
python -m src.transform.silver.enrich_airports
```

**Gold aggregation**

```bash
python -m src.transform.gold.aggregate --date 2026-09-27
```

---

## 🗄️ Supabase / PostgreSQL

The Gold layer is loaded into Supabase PostgreSQL, creating/upserting records for:

```text
gold.airport_traffic
gold.country_traffic
gold.route_traffic
```

Run the loader with:

```bash
python -m src.load.supabase
```

The loader uses conflict handling so existing records for the same analytical key are updated rather than duplicated.

---

## 📈 Analytical Questions

**Airport Analysis**

- Which airports have the highest total traffic?
- How many arrivals and departures does each airport handle?
- Which airports have the highest number of unique aircraft?
- How does airport activity change over time?

**Country Analysis**

- Which countries have the highest aviation activity?
- How does arrival activity compare with departure activity?
- Which countries have the highest number of unique aircraft?

**Route Analysis**

- Which routes have the highest flight volume?
- Which routes connect the most frequently used airports?
- How does route activity change over time?
- How many unique aircraft operate on a route?

---

## 🧠 Key Concepts Demonstrated

- REST API ingestion and authentication
- Incremental ingestion and historical backfilling
- Raw data preservation
- Medallion architecture
- Data cleaning, validation, and deduplication
- Feature engineering
- Reference-data enrichment
- Aggregation
- PostgreSQL loading with upsert logic
- Pipeline orchestration
- Business intelligence and data visualization

---

## 💡 Why Bronze → Silver → Gold?

| Layer | Question it answers | Contents |
|---|---|---|
| **Bronze** | What did the source provide? | Raw, minimally processed data |
| **Silver** | What does the cleaned data look like? | Validated and enriched flight-level records |
| **Gold** | What does the business need for analysis? | Aggregated datasets optimized for dashboards |

This separation makes the system easier to maintain and debug, and allows Silver and Gold to be reprocessed without repeatedly fetching data from the external API.

---

## 🚀 Future Improvements

- Automate scheduled ingestion with Airflow or another workflow scheduler
- Add real-time streaming capabilities
- Add flight-delay or estimated-delay analysis
- Add geographic flight and route map visualizations
- Introduce data quality monitoring
- Add automated pipeline tests
- Containerize the pipeline with Docker
- Implement incremental database loading
- Add historical trend analysis
- Add anomaly detection for unusual traffic patterns
- Implement CI/CD for the data pipeline

---

## 📚 Data Sources

- **OpenSky Network** — flight data via the OpenSky Network API
- **Airport Reference Data** — maintained separately and used to enrich flight records with airport names, IATA codes, ICAO codes, and country information

---

## 👨‍💻 Author

**Krish Shah**
B.Tech — Electronics & Telecommunication Engineering, Sardar Patel Institute of Technology

Interested in **Data Analytics, Data Science, Data Engineering, and Business Intelligence**.

---

## ⭐ Project Summary

> An end-to-end aviation analytics platform that transforms raw OpenSky flight data into business-ready airport, country, and route intelligence using Python, PostgreSQL/Supabase, and Power BI.
