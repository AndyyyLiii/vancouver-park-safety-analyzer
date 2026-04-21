# Vancouver Park Safety Analyzer

A Python application that combines City of Vancouver park data with Vancouver Police Department (VPD) crime data to analyze the relationship between parks and neighbourhood safety. The project produces a text report, three static charts, and an interactive web map.

## Live Links

## Live Links

- **GitHub repository:** https://github.com/AndyyyLiii/vancouver-park-safety-analyzer
- **Live interactive map (GitHub Pages):** https://andyyyliii.github.io/vancouver-park-safety-analyzer/

## What This Project Does

Running `python main.py` executes the full pipeline in one command:

1. Loads and cleans the Vancouver Parks dataset and the VPD Crime dataset.
2. Prints a formatted text report to the console (dataset summaries, top crime types, safest and most dangerous neighbourhoods, and a cross-dataset parks-vs-crime comparison).
3. Generates three static PNG charts in `charts/`:
   - `crime_by_type.png` — top 10 crime types in 2024
   - `crime_per_neighbourhood.png` — total reported crimes per neighbourhood
   - `facilities_vs_crime.png` — a geographic heatmap of 2024 crime density with all 218 parks overlaid (cross-dataset)
4. Generates `map.html` — an interactive Folium map with one marker per park. Each popup shows the park's facilities and the number of 2024 crimes within a 200 m radius, compared against the city-wide average.

## How to Run

1. Make sure Python 3.9+ is installed.
2. Install the required libraries:

   ```
   pip install pandas matplotlib folium numpy
   ```

3. Place the two CSV files in the `data/` folder (see **Datasets** below for download links).
4. Run the pipeline:

   ```
   python main.py
   ```

   All outputs appear automatically: the text report in the console, PNG charts in `charts/`, and `map.html` in the project root.

## Datasets

1. **Vancouver Parks**
   - Source: City of Vancouver Open Data Portal
   - Download: https://opendata.vancouver.ca/explore/dataset/parks/
   - Click Export → CSV (semicolon-separated). Save as `data/parks.csv`.

2. **VPD Crime Data**
   - Source: Vancouver Police Department GeoDASH Open Data
   - Download: https://geodash.vpd.ca/opendata/
   - Select All Years, All Neighbourhoods, then download. Save as `data/crimedata_csv_AllNeighbourhoods_AllYears.csv`.

## Libraries Used

- `pandas` — data loading and manipulation
- `matplotlib` — static chart generation (PNG output)
- `folium` — interactive Leaflet map generation (HTML output)
- `numpy` — vectorized distance calculations for the nearby-crime analysis

## Project Structure

```
├── main.py              Single entry point — runs everything
├── loader.py            DataLoader class — reads and cleans both CSVs
├── analyzer.py          ParkCrimeAnalyzer class — computes all statistics
├── charts.py            Generates the three static PNG charts
├── map_builder.py       Generates the interactive folium map
├── park.py              Park class (plain data container)
├── data/                Input CSVs (not checked into git)
├── charts/              Output PNG charts (generated)
└── map.html             Output interactive map (generated)
```

## Known Limitations

- **Geographic scope:** The parks dataset is limited to City of Vancouver properties and the VPD dataset is limited to VPD jurisdiction. Burnaby, Richmond, Surrey, and other Metro Vancouver municipalities are not represented.
- **Neighbourhood name mismatches:** The parks and crime datasets use slightly different neighbourhood labels in some cases (e.g. `Arbutus-Ridge` vs `Arbutus Ridge`, `Downtown` vs `Central Business District`). The loader handles the known mismatches through an explicit mapping, but some neighbourhoods such as Musqueam and Stanley Park appear in the crime dataset without matching parks in the parks dataset.
- **VPD coordinate privacy:** VPD offsets reported (X, Y) coordinates slightly for privacy and returns (0, 0) for sensitive offences. Zero-coordinate records (~9% of the data) are excluded from the geographic chart and the nearby-crime calculation. This is sufficient for neighbourhood-scale density patterns but unsuitable for block-level analysis.
- **Analysis year:** Reports and charts focus on 2024 data by default. The constant `ParkCrimeAnalyzer.ANALYSIS_YEAR` controls this and can be changed to study other years.

