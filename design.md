# Design Document — Vancouver Park Safety Analyzer

## Project Overview

This application combines City of Vancouver park data with Vancouver Police Department crime data to answer: which Vancouver parks and neighbourhoods are safest, and how does park density relate to crime? It produces a formatted text report with statistics and insights drawn from both datasets.

## Class 1: `Park`

Responsibility: Models a single park. Stores its name, location, neighbourhood, and facilities. A plain data container.

Key attributes:
- `name: str`
- `neighbourhood: str`
- `latitude: float`, `longitude: float`
- `facilities: list[str]`
- `has_washroom: bool`

Key methods:
- `__init__(name, neighbourhood, latitude, longitude, facilities, has_washroom)`
- `__repr__() -> str`
- `facility_count() -> int`

## Class 2: `DataLoader`

Responsibility: Loads and cleans both datasets. Returns a list of Park objects and a crime DataFrame. All file I/O lives here.

Key attributes:
- `data_dir: Path`

Key methods:
- `load_parks() -> list[Park]`
- `load_crime() -> pd.DataFrame`
- `_clean_parks(df) -> pd.DataFrame`
- `_clean_crime(df) -> pd.DataFrame`

## Class 3: `ParkCrimeAnalyzer`

Responsibility: Analyzes the relationship between parks and crime across neighbourhoods, and generates the text report.

Key attributes:
- `parks: list[Park]`
- `crime_df: pd.DataFrame`

Key methods:
- `crime_by_neighbourhood() -> pd.DataFrame`
- `parks_by_neighbourhood() -> dict[str, list[Park]]`
- `safest_neighbourhoods() -> list[str]`
- `build_report() -> str`

## How the Classes Interact

`DataLoader` loads both CSVs and returns `Park` objects and a crime DataFrame. `ParkCrimeAnalyzer` receives both, compares park density and crime rates by neighbourhood, and builds the report. `text_report.py` calls both in order and prints the result.