"""Vancouver Park Safety Analyzer — single entry point.

Running `python main.py` performs the full pipeline:
    1. Loads and cleans the Vancouver Parks and VPD Crime datasets.
    2. Prints the formatted text report to the console.
    3. Generates three PNG charts into the charts/ directory.
    4. Saves the interactive Folium map as map.html.

All output paths are resolved relative to the project root, so the
script runs correctly regardless of the caller's working directory.
"""

from loader import DataLoader
from analyzer import ParkCrimeAnalyzer
from charts import generate_all_charts
from map_builder import build_map


def main():
    """Run the full data pipeline from loading to all outputs."""
    # --- Step 1: Load data ---
    loader = DataLoader(data_dir="data")

    print("Loading parks data...")
    parks = loader.load_parks()
    print(f"  Loaded {len(parks)} parks.")

    print("Loading crime data...")
    crime_df = loader.load_crime()
    print(f"  Loaded {len(crime_df):,} crime records.")
    print()

    # --- Step 2: Analyze and print the text report ---
    analyzer = ParkCrimeAnalyzer(parks, crime_df)
    report = analyzer.build_report()
    print(report)
    print()

    # --- Step 3: Generate the three PNG charts ---
    generate_all_charts(analyzer)

    # --- Step 4: Generate the interactive folium map ---
    build_map(analyzer)

    print()
    print("Done. Outputs:")
    print("  - Text report: printed above")
    print("  - Charts:      charts/*.png")
    print("  - Map:         map.html")


if __name__ == "__main__":
    main()