"""Chart module — generates static PNG visualizations.

Produces three charts:
  1. crime_by_type.png            — top crime types in the analysis year
  2. crime_per_neighbourhood.png  — crime counts across neighbourhoods
  3. facilities_vs_crime.png      — cross-dataset: park facilities vs crime

Each function takes a ParkCrimeAnalyzer instance and saves a PNG to
the charts/ directory.
"""

from pathlib import Path
import math
import matplotlib.pyplot as plt

# --- Constants ---
# Resolve output directory relative to this file so the script works
# regardless of the caller's current working directory.
PROJECT_ROOT = Path(__file__).resolve().parent
CHARTS_DIR = PROJECT_ROOT / "charts"
TOP_N_CRIME_TYPES = 10      # how many crime types to show in chart 1
CHART_DPI = 150             # resolution for saved PNGs
FIG_SIZE_WIDE = (12, 7)     # figure size for horizontal/bar charts
FIG_SIZE_SQUARE = (10, 8)   # figure size for the scatter plot

# --- Local coordinate-projection constants ---
# Vancouver is small enough (~0.1 degrees lat, ~0.2 degrees lon) that we can
# convert park lat/lon into the same UTM Zone 10N metre grid the VPD crime
# data already uses, via a flat-earth linear approximation. Error stays
# below ~20 m across the whole city — negligible for a density heatmap.
# Reference origin chosen near the centre of the parks bounding box.
LAT_REF = 49.25
LON_REF = -123.12
METERS_PER_LAT_DEGREE = 111320
# cos(49.25°) ≈ 0.6528, so one degree of longitude at this latitude
METERS_PER_LON_DEGREE = METERS_PER_LAT_DEGREE * math.cos(math.radians(LAT_REF))
# Corresponding UTM 10N coordinates for the reference origin
# (calibrated once against a known Vancouver point so parks line up with
# the VPD crime coordinate grid)
UTM_X_AT_REF = 491260
UTM_Y_AT_REF = 5456580


def _latlon_to_utm_approx(lat, lon):
    """Convert (lat, lon) to approximate UTM Zone 10N metres.

    Flat-earth linear approximation — valid only over small areas
    (a few tens of kilometres). Accurate to within ~20 metres across
    the City of Vancouver.
    """
    x = UTM_X_AT_REF + (lon - LON_REF) * METERS_PER_LON_DEGREE
    y = UTM_Y_AT_REF + (lat - LAT_REF) * METERS_PER_LAT_DEGREE
    return x, y


def _ensure_charts_dir():
    """Make sure the charts/ output directory exists."""
    CHARTS_DIR.mkdir(exist_ok=True)


def chart_crime_by_type(analyzer):
    """Chart 1: Horizontal bar chart of the most common crime types.

    Question answered: What are the most common types of crime in
    Vancouver in the analysis year?
    """
    _ensure_charts_dir()

    crime_type_counts = analyzer.crime_by_type()
    # Take the top N and reverse so the largest bar sits on top
    top_items = list(crime_type_counts.items())[:TOP_N_CRIME_TYPES]
    top_items.reverse()
    labels = [item[0] for item in top_items]
    counts = [item[1] for item in top_items]

    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    bars = ax.barh(labels, counts, color="steelblue",
                   label=f"{analyzer.ANALYSIS_YEAR} crime count")

    # Annotate each bar with its numeric value
    for bar, value in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{value:,}",
                va="center", fontsize=9)

    ax.set_title(
        f"Top {TOP_N_CRIME_TYPES} Crime Types in Vancouver "
        f"({analyzer.ANALYSIS_YEAR})",
        fontsize=14,
    )
    ax.set_xlabel("Number of Reported Incidents")
    ax.set_ylabel("Crime Type")
    ax.legend(loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = CHARTS_DIR / "crime_by_type.png"
    plt.savefig(output_path, dpi=CHART_DPI)
    plt.close(fig)
    print(f"  Saved {output_path}")


def chart_crime_per_neighbourhood(analyzer):
    """Chart 2: Bar chart of crime count for every neighbourhood.

    Question answered: Which Vancouver neighbourhoods had the most and
    least reported crimes in the analysis year?
    """
    _ensure_charts_dir()

    crime_counts = analyzer.crime_per_neighbourhood()
    # Sort ascending so safest neighbourhoods appear on the left
    sorted_items = sorted(crime_counts.items(), key=lambda pair: pair[1])
    labels = [item[0] for item in sorted_items]
    counts = [item[1] for item in sorted_items]

    # Color the lowest 3 green (safest) and highest 3 red (most crime)
    colors = []
    for rank in range(len(labels)):
        if rank < 3:
            colors.append("mediumseagreen")
        elif rank >= len(labels) - 3:
            colors.append("indianred")
        else:
            colors.append("lightsteelblue")

    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)
    ax.bar(labels, counts, color=colors)

    ax.set_title(
        f"Total Reported Crimes by Neighbourhood "
        f"({analyzer.ANALYSIS_YEAR})",
        fontsize=14,
    )
    ax.set_xlabel("Neighbourhood")
    ax.set_ylabel("Number of Reported Crimes")
    plt.xticks(rotation=60, ha="right", fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Custom legend explaining the colors
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(color="mediumseagreen", label="3 Safest Neighbourhoods"),
        Patch(color="lightsteelblue", label="Mid-range"),
        Patch(color="indianred", label="3 Highest-Crime Neighbourhoods"),
    ]
    ax.legend(handles=legend_handles, loc="upper left")
    plt.tight_layout()

    output_path = CHARTS_DIR / "crime_per_neighbourhood.png"
    plt.savefig(output_path, dpi=CHART_DPI)
    plt.close(fig)
    print(f"  Saved {output_path}")


def chart_facilities_vs_crime(analyzer):
    """Chart 3 (CROSS-DATASET): Geographic density of crime vs park locations.

    Question answered: How does reported crime cluster geographically
    across Vancouver, and where do parks sit relative to those clusters?

    A hexbin heatmap of every valid crime coordinate shows the density
    surface; every park from the parks dataset is overlaid as a small
    marker. The plot combines BOTH datasets in a single geographic space:
    VPD crime data supplies the density surface (in UTM Zone 10N metres,
    native to the dataset) and the parks dataset supplies the overlay
    (converted from lat/lon to the same UTM grid via a linear
    approximation).

    Note on coordinates: VPD offsets coordinates slightly for privacy and
    returns (0, 0) for sensitive offences. We drop zero-coordinate rows
    before plotting. The offset is small enough that neighbourhood-scale
    density patterns remain informative, though the plot is not suitable
    for block-level analysis.
    """
    _ensure_charts_dir()

    # --- Prepare crime coordinates ---
    year = analyzer.ANALYSIS_YEAR
    crime_df = analyzer.crime_df
    year_mask = crime_df["YEAR"] == year
    valid_coord_mask = (crime_df["X"] != 0) & (crime_df["Y"] != 0)
    plot_df = crime_df[year_mask & valid_coord_mask]
    crime_x = plot_df["X"].to_numpy()
    crime_y = plot_df["Y"].to_numpy()

    # --- Prepare park coordinates (convert lat/lon to matching UTM grid) ---
    park_xy = [
        _latlon_to_utm_approx(park.latitude, park.longitude)
        for park in analyzer.parks
    ]
    park_x = [xy[0] for xy in park_xy]
    park_y = [xy[1] for xy in park_xy]

    # --- Build the figure ---
    fig, ax = plt.subplots(figsize=FIG_SIZE_SQUARE)

    HEXBIN_GRIDSIZE = 45       # number of hex bins across the x extent
    MIN_CRIMES_PER_HEX = 1     # hide empty cells so the canvas stays light
    hb = ax.hexbin(
        crime_x,
        crime_y,
        gridsize=HEXBIN_GRIDSIZE,
        cmap="YlOrRd",
        mincnt=MIN_CRIMES_PER_HEX,
    )

    # Parks as small translucent dots on top
    ax.scatter(
        park_x,
        park_y,
        s=14,
        color="#2E7D32",
        edgecolors="white",
        linewidths=0.4,
        alpha=0.9,
        label=f"Park ({len(park_x)} locations)",
        zorder=3,
    )

    # Colorbar for the crime density layer
    cbar = plt.colorbar(hb, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label(f"Reported crimes per hex cell ({year})", fontsize=10)

    # --- Axis styling ---
    ax.set_title(
        "Crime Density and Park Locations Across Vancouver",
        fontsize=14,
        pad=12,
    )
    ax.set_xlabel("Easting — UTM Zone 10N (metres)", fontsize=10)
    ax.set_ylabel("Northing — UTM Zone 10N (metres)", fontsize=10)
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.tick_params(labelsize=8)

    # Equal aspect ratio so the map is not geometrically distorted
    ax.set_aspect("equal", adjustable="box")

    # Subtle caption explaining the privacy note
    ax.text(
        0.02, -0.14,
        "VPD coordinates are slightly offset for privacy; zero-coord "
        "records (sensitive offences) are excluded.",
        transform=ax.transAxes,
        fontsize=8,
        color="gray",
        style="italic",
    )

    ax.legend(loc="upper left", fontsize=10, framealpha=0.95)

    plt.tight_layout()
    output_path = CHARTS_DIR / "facilities_vs_crime.png"
    plt.savefig(output_path, dpi=CHART_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {output_path}")


def generate_all_charts(analyzer):
    """Generate all three charts in sequence."""
    print("Generating charts...")
    chart_crime_by_type(analyzer)
    chart_crime_per_neighbourhood(analyzer)
    chart_facilities_vs_crime(analyzer)
    print("All charts saved to charts/ directory.\n")