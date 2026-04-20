"""Map module — generates an interactive folium map of Vancouver parks.

Outputs map.html: a self-contained interactive map with one marker per
park. Each marker has a clickable popup showing park details alongside
the 2024 crime count for that park's neighbourhood — combining both
datasets into the popup itself.
"""

from pathlib import Path
import folium

# --- Constants ---
# Resolve output path relative to this file so the script works no
# matter where Python is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent
MAP_OUTPUT_PATH = PROJECT_ROOT / "map.html"
VANCOUVER_CENTER = (49.26, -123.12)  # lat, lon — near the geographic middle
DEFAULT_ZOOM = 12
MARKER_ICON_COLOR = "green"
MARKER_ICON = "tree"
NEARBY_RADIUS_M = 200   # popup counts crimes within this many metres of park


def _build_popup_html(park, nearby_crime_count, city_average):
    """Build the HTML shown inside a park marker's popup.

    Args:
        park: A Park instance.
        nearby_crime_count: Number of non-traffic 2024 crimes within
            NEARBY_RADIUS_M of this park.
        city_average: Average nearby-crime count across all parks, used
            for the "above / below average" comparison line.

    Returns:
        An HTML string suitable for folium.Popup.
    """
    washroom_text = "✓ Yes" if park.has_washroom else "✗ No"
    facilities_text = "✓ Yes" if park.has_facilities else "✗ No"

    if park.hectare > 0:
        hectare_text = f"{park.hectare:.2f} hectares"
    else:
        hectare_text = "Not recorded"

    # Comparison: is this park above or below the city-wide average?
    diff = nearby_crime_count - city_average
    if diff > city_average * 0.1:           # clearly above avg (>10% higher)
        comparison_text = "higher than the city-wide average"
        comparison_color = "#C0392B"        # muted red
    elif diff < -city_average * 0.1:        # clearly below avg
        comparison_text = "lower than the city-wide average"
        comparison_color = "#2E7D32"        # muted green
    else:
        comparison_text = "near the city-wide average"
        comparison_color = "#888"

    html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px;
                min-width: 230px; line-height: 1.5;">
        <h4 style="margin: 0 0 8px 0; color: #2E7D32;">{park.name}</h4>
        <div><b>Neighbourhood:</b> {park.neighbourhood}</div>
        <div><b>Size:</b> {hectare_text}</div>
        <div><b>Washroom:</b> {washroom_text}</div>
        <div><b>Other facilities:</b> {facilities_text}</div>
        <hr style="margin: 8px 0; border: none; border-top: 1px solid #ddd;">
        <div style="font-size: 12px;">
            <b>Crimes within {NEARBY_RADIUS_M} m in 2024:</b>
            <span style="font-size: 15px; font-weight: bold;
                         color: {comparison_color};">
                {nearby_crime_count:,}
            </span>
            <div style="color: {comparison_color}; font-style: italic;
                        margin-top: 2px;">
                {comparison_text} ({city_average:.0f})
            </div>
            <div style="color: #999; font-size: 11px; margin-top: 4px;">
                Traffic-collision reports excluded.
            </div>
        </div>
    </div>
    """
    return html


def build_map(analyzer):
    """Generate map.html with one marker per park.

    Precomputes nearby-crime counts once for every park (vectorized via
    NumPy) and uses each park's value + the city-wide average in its
    popup. This makes the map a truly cross-dataset artifact: each
    marker fuses parks data (location, facilities) with VPD crime data
    (count of nearby 2024 incidents within a 200 m radius).

    Args:
        analyzer: A ParkCrimeAnalyzer instance.
    """
    print("Generating map...")

    # Precompute nearby-crime count for every park (single pass).
    nearby_counts = analyzer.nearby_crime_per_park(
        radius_meters=NEARBY_RADIUS_M, exclude_traffic=True
    )
    count_values = list(nearby_counts.values())
    city_average = sum(count_values) / len(count_values) if count_values else 0

    # Base map
    # CartoDB Voyager — a soft-colour tile style tailored for data
    # overlays. No HTTP Referer restriction (unlike OSM's main tile
    # servers, which block local file:// previews with a 403).
    voyager_tiles = (
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/"
        "{z}/{x}/{y}{r}.png"
    )
    voyager_attribution = (
        '&copy; <a href="https://www.openstreetmap.org/copyright">'
        'OpenStreetMap</a> contributors &copy; '
        '<a href="https://carto.com/attributions">CARTO</a>'
    )
    m = folium.Map(
        location=VANCOUVER_CENTER,
        zoom_start=DEFAULT_ZOOM,
        tiles=voyager_tiles,
        attr=voyager_attribution,
    )

    marker_count = 0
    for park in analyzer.parks:
        nearby = nearby_counts.get(park.park_id, 0)
        popup_html = _build_popup_html(park, nearby, city_average)
        folium.Marker(
            location=(park.latitude, park.longitude),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=park.name,
            icon=folium.Icon(color=MARKER_ICON_COLOR, icon=MARKER_ICON,
                             prefix="fa"),
        ).add_to(m)
        marker_count += 1

    m.save(str(MAP_OUTPUT_PATH))
    print(f"  Saved {MAP_OUTPUT_PATH} ({marker_count} park markers, "
          f"city avg {city_average:.1f} nearby crimes/park)")