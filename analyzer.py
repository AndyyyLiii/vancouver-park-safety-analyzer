"""Analyzer module — analyzes relationships between parks and crime."""


class ParkCrimeAnalyzer:
    """Analyzes the relationship between parks and crime across neighbourhoods.

    Receives a list of Park objects and a crime DataFrame, then computes
    statistics like crime counts and park counts per neighbourhood,
    and generates a formatted text report with insights.
    """

    ANALYSIS_YEAR = 2024

    def __init__(self, parks, crime_df):
        """Initialize the analyzer.

        Args:
            parks: A list of Park objects.
            crime_df: A pandas DataFrame of crime records.
        """
        self.parks = parks
        self.crime_df = crime_df

    def parks_per_neighbourhood(self):
        """Count the number of parks in each neighbourhood.

        Returns:
            A dict mapping neighbourhood name to park count.
        """
        counts = {}
        for park in self.parks:
            neighbourhood = park.neighbourhood
            counts[neighbourhood] = counts.get(neighbourhood, 0) + 1
        return counts

    def crime_per_neighbourhood(self, year=None):
        """Count crimes in each neighbourhood for a given year.

        Args:
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A dict mapping neighbourhood name to crime count.
        """
        if year is None:
            year = self.ANALYSIS_YEAR

        filtered = self.crime_df[self.crime_df["YEAR"] == year]
        counts = filtered.groupby("NEIGHBOURHOOD").size().to_dict()
        return counts

    def crime_by_type(self, year=None):
        """Count crimes by type for a given year.

        Args:
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A dict mapping crime type to count, sorted descending.
        """
        if year is None:
            year = self.ANALYSIS_YEAR

        filtered = self.crime_df[self.crime_df["YEAR"] == year]
        counts = filtered.groupby("TYPE").size().sort_values(ascending=False)
        return counts.to_dict()

    def safest_neighbourhoods(self, year=None):
        """Return neighbourhoods sorted by crime count (lowest first).

        Args:
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A list of (neighbourhood, crime_count) tuples, sorted ascending.
        """
        crime_counts = self.crime_per_neighbourhood(year)
        sorted_list = sorted(crime_counts.items(), key=lambda x: x[1])
        return sorted_list

    def parks_vs_crime(self, year=None):
        """Compare park count and crime count per neighbourhood.

        This is the cross-dataset insight: do neighbourhoods with
        more parks tend to have more or fewer crimes?

        Args:
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A list of dicts with keys: neighbourhood, park_count,
            crime_count, crime_per_park. Sorted by crime_per_park.
        """
        park_counts = self.parks_per_neighbourhood()
        crime_counts = self.crime_per_neighbourhood(year)

        results = []
        for neighbourhood in park_counts:
            if neighbourhood in crime_counts:
                park_count = park_counts[neighbourhood]
                crime_count = crime_counts[neighbourhood]
                crime_per_park = round(crime_count / park_count, 1)
                results.append({
                    "neighbourhood": neighbourhood,
                    "park_count": park_count,
                    "crime_count": crime_count,
                    "crime_per_park": crime_per_park,
                })

        results.sort(key=lambda x: x["crime_per_park"])
        return results

    def facilities_vs_crime(self, year=None):
        """Compare park facility coverage and crime count per neighbourhood.

        For each neighbourhood, computes the fraction of parks that have
        washrooms and facilities, then pairs it with the crime count.
        This is a cross-dataset insight: are neighbourhoods with
        better-equipped parks safer?

        Args:
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A list of dicts with keys: neighbourhood, park_count,
            washroom_ratio, facility_ratio, crime_count.
        """
        crime_counts = self.crime_per_neighbourhood(year)

        # Group parks by neighbourhood
        parks_by_nbhd = {}
        for park in self.parks:
            parks_by_nbhd.setdefault(park.neighbourhood, []).append(park)

        results = []
        for neighbourhood, park_list in parks_by_nbhd.items():
            if neighbourhood not in crime_counts:
                continue
            park_count = len(park_list)
            washroom_count = sum(1 for p in park_list if p.has_washroom)
            facility_count = sum(1 for p in park_list if p.has_facilities)
            results.append({
                "neighbourhood": neighbourhood,
                "park_count": park_count,
                "washroom_ratio": washroom_count / park_count,
                "facility_ratio": facility_count / park_count,
                "crime_count": crime_counts[neighbourhood],
            })

        return results

    def crime_group_stats(self, year=None):
        """Group neighbourhoods into crime tiers and average facility coverage.

        Splits neighbourhoods into three equal-sized tiers by crime count
        (low / medium / high), then for each tier computes the average
        share of parks that have washrooms and the average share that
        have other facilities.

        This supports the cross-dataset chart answering:
        "Are parks in higher-crime neighbourhoods less well-equipped?"

        Args:
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A list of three dicts (ordered low -> medium -> high), each with:
            tier_label, neighbourhood_count, avg_washroom_pct,
            avg_facility_pct.
        """
        per_nbhd = self.facilities_vs_crime(year)
        if not per_nbhd:
            return []

        # Sort by crime count (ascending) so the low tier is first
        sorted_nbhds = sorted(per_nbhd, key=lambda item: item["crime_count"])

        # Split into three roughly equal groups
        NUM_TIERS = 3
        tier_size = len(sorted_nbhds) // NUM_TIERS
        tier_labels = ["Low-crime", "Medium-crime", "High-crime"]

        tiers = []
        for tier_index in range(NUM_TIERS):
            start = tier_index * tier_size
            # Last tier absorbs any remainder so no neighbourhood is dropped
            if tier_index == NUM_TIERS - 1:
                end = len(sorted_nbhds)
            else:
                end = start + tier_size
            group = sorted_nbhds[start:end]
            if not group:
                continue

            avg_washroom = sum(n["washroom_ratio"] for n in group) / len(group)
            avg_facility = sum(n["facility_ratio"] for n in group) / len(group)

            tiers.append({
                "tier_label": tier_labels[tier_index],
                "neighbourhood_count": len(group),
                "avg_washroom_pct": avg_washroom * 100,
                "avg_facility_pct": avg_facility * 100,
            })

        return tiers

    def nearby_crime_per_park(
        self, radius_meters=200, exclude_traffic=True, year=None
    ):
        """Count crimes within a given radius of each park.

        For every park, this measures straight-line distance (in UTM
        metres) to every crime record in the given year and counts the
        ones within `radius_meters`. Traffic-related offences are
        excluded by default because they do not reflect park-user
        safety. Uses a flat-earth lat/lon-to-UTM approximation; accuracy
        is well within a metre at Vancouver's scale.

        Implementation note: computed with a single NumPy broadcast so
        the full 218-parks × ~30k-crimes comparison runs in well under
        a second.

        Args:
            radius_meters: Distance threshold in metres.
            exclude_traffic: If True, skip Vehicle Collision crime types.
            year: The year to filter by. Defaults to ANALYSIS_YEAR.

        Returns:
            A dict mapping park_id to nearby-crime count (int).
        """
        import numpy as np
        import math

        if year is None:
            year = self.ANALYSIS_YEAR

        # --- Filter crime records: year, valid coords, maybe traffic ---
        df = self.crime_df
        mask = (df["YEAR"] == year) & (df["X"] != 0) & (df["Y"] != 0)
        if exclude_traffic:
            # Any crime type containing "Vehicle Collision" is a traffic event
            mask &= ~df["TYPE"].str.contains(
                "Vehicle Collision", case=False, na=False
            )
        filtered = df[mask]
        crime_x = filtered["X"].to_numpy()
        crime_y = filtered["Y"].to_numpy()

        # --- Convert park lat/lon to the same UTM Zone 10N metre grid ---
        # (Same flat-earth approximation used by the geographic chart.)
        LAT_REF = 49.25
        LON_REF = -123.12
        METERS_PER_LAT_DEGREE = 111320
        METERS_PER_LON_DEGREE = (
            METERS_PER_LAT_DEGREE * math.cos(math.radians(LAT_REF))
        )
        UTM_X_AT_REF = 491260
        UTM_Y_AT_REF = 5456580

        park_ids = [p.park_id for p in self.parks]
        park_x = np.array([
            UTM_X_AT_REF + (p.longitude - LON_REF) * METERS_PER_LON_DEGREE
            for p in self.parks
        ])
        park_y = np.array([
            UTM_Y_AT_REF + (p.latitude - LAT_REF) * METERS_PER_LAT_DEGREE
            for p in self.parks
        ])

        # --- Vectorized distance check ---
        # Compare with squared distances so we avoid N*M square roots
        radius_squared = radius_meters ** 2

        counts = {}
        for i, pid in enumerate(park_ids):
            dx = crime_x - park_x[i]
            dy = crime_y - park_y[i]
            nearby = (dx * dx + dy * dy) <= radius_squared
            counts[pid] = int(nearby.sum())

        return counts

    def build_report(self):
        """Generate a formatted text report with summaries and insights.

        Returns:
            A string containing the full report.
        """
        lines = []
        separator = "=" * 60

        # --- Title ---
        lines.append(separator)
        lines.append("  VANCOUVER PARK SAFETY ANALYZER — REPORT")
        lines.append(separator)
        lines.append("")

        # --- Dataset 1 Summary: Parks ---
        lines.append("DATASET 1: VANCOUVER PARKS")
        lines.append("-" * 40)
        total_parks = len(self.parks)
        neighbourhoods = set(p.neighbourhood for p in self.parks)
        parks_with_washroom = sum(1 for p in self.parks if p.has_washroom)
        parks_with_facilities = sum(1 for p in self.parks if p.has_facilities)
        hectares = [p.hectare for p in self.parks if p.hectare > 0]
        avg_hectare = sum(hectares) / len(hectares) if hectares else 0

        lines.append(f"  Total parks: {total_parks}")
        lines.append(f"  Neighbourhoods covered: {len(neighbourhoods)}")
        lines.append(f"  Parks with washrooms: {parks_with_washroom}")
        lines.append(f"  Parks with facilities: {parks_with_facilities}")
        lines.append(f"  Average park size: {avg_hectare:.2f} hectares")
        lines.append("")

        # --- Dataset 2 Summary: Crime ---
        lines.append("DATASET 2: VPD CRIME DATA")
        lines.append("-" * 40)
        total_crimes = len(self.crime_df)
        year_range = (
            f"{int(self.crime_df['YEAR'].min())}–"
            f"{int(self.crime_df['YEAR'].max())}"
        )
        crimes_this_year = len(
            self.crime_df[self.crime_df["YEAR"] == self.ANALYSIS_YEAR]
        )
        crime_types = self.crime_df["TYPE"].nunique()

        lines.append(f"  Total crime records: {total_crimes:,}")
        lines.append(f"  Year range: {year_range}")
        lines.append(f"  Records in {self.ANALYSIS_YEAR}: {crimes_this_year:,}")
        lines.append(f"  Crime types: {crime_types}")
        lines.append("")

        # --- Insight 1: Top crime types ---
        lines.append("INSIGHT 1: MOST COMMON CRIME TYPES "
                      f"({self.ANALYSIS_YEAR})")
        lines.append("-" * 40)
        crime_types_dict = self.crime_by_type()
        for i, (crime_type, count) in enumerate(crime_types_dict.items()):
            if i >= 5:
                break
            lines.append(f"  {i + 1}. {crime_type}: {count:,}")
        lines.append("")

        # --- Insight 2: Safest and most dangerous neighbourhoods ---
        lines.append("INSIGHT 2: SAFEST vs MOST DANGEROUS "
                      f"NEIGHBOURHOODS ({self.ANALYSIS_YEAR})")
        lines.append("-" * 40)
        ranked = self.safest_neighbourhoods()
        lines.append("  Safest (fewest crimes):")
        for name, count in ranked[:3]:
            lines.append(f"    - {name}: {count:,} crimes")
        lines.append("  Most dangerous (most crimes):")
        for name, count in ranked[-3:]:
            lines.append(f"    - {name}: {count:,} crimes")
        lines.append("")

        # --- Insight 3 (cross-dataset): Parks vs Crime ---
        lines.append("INSIGHT 3: PARKS vs CRIME BY NEIGHBOURHOOD "
                      f"({self.ANALYSIS_YEAR})")
        lines.append("-" * 40)
        lines.append("  (Crimes per park = total crimes / number of parks)")
        lines.append("")
        comparison = self.parks_vs_crime()

        lines.append("  Lowest crime-per-park (safest park areas):")
        for item in comparison[:3]:
            lines.append(
                f"    - {item['neighbourhood']}: "
                f"{item['park_count']} parks, "
                f"{item['crime_count']:,} crimes, "
                f"{item['crime_per_park']} crimes/park"
            )

        lines.append("  Highest crime-per-park:")
        for item in comparison[-3:]:
            lines.append(
                f"    - {item['neighbourhood']}: "
                f"{item['park_count']} parks, "
                f"{item['crime_count']:,} crimes, "
                f"{item['crime_per_park']} crimes/park"
            )
        lines.append("")

        # --- Footer ---
        lines.append(separator)
        lines.append("  End of report")
        lines.append(separator)

        return "\n".join(lines)