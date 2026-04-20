"""
Loads and cleans parks and crime datasets.
"""
import pandas as pd # read csv files 
from pathlib import Path # handle file paths
from park import Park   # import Park class

# Resolve the data directory relative to this file, not to the process's
# current working directory. That way the loader works whether the user
# runs main.py from the project root, from an IDE, or from anywhere else.
PROJECT_ROOT = Path(__file__).resolve().parent

# Mapping from parks neighbourhood names to crime neighbourhood names.
NEIGHBOURHOOD_MAP = {
    "Arbutus-Ridge": "Arbutus Ridge",
    "Downtown": "Central Business District",
}

class DataLoader:
    """
    Loads and cleans parks and crime datasets.
    """
    def __init__(self, data_dir="data"):
        """
        Initialize a DataLoader instance.

        The data directory is resolved relative to the project root
        (the folder containing loader.py), so the path is valid no
        matter where the caller is invoking Python from.
        """
        self.data_dir = PROJECT_ROOT / data_dir
    
    def load_parks(self, filename="parks.csv"):
        """
        Load and clean the parks dataset, returning a list of Park instances.
        """
        filepath = self.data_dir / "parks.csv" # create file path to parks.csv
        df = pd.read_csv(filepath, sep=";", encoding="utf-8-sig")  # read the csv file into a pandas dataframe
        df = self._clean_parks(df)  # clean the dataframe using the _clean_parks method
 
        parks = []      
        for _, row in df.iterrows():    # iterate through each row of the cleaned dataframe
            lat, lon = self._parse_coordinates(row["GoogleMapDest"])    # parse latitude and longitude from Google Maps destination
            if lat is None: # if parsing fails, skip this park
                continue
 
            park = Park(
                park_id=row["ParkID"],
                name=row["Name"],
                neighbourhood=row["neighbourhood_clean"],
                latitude=lat,
                longitude=lon,
                hectare=row["Hectare"],
                has_facilities=(row["Facilities"] == "Y"),
                has_washroom=(row["Washrooms"] == "Y"),
            )
            parks.append(park)
 
        return parks
    
    def load_crime(self, filename="crime.csv"):
        """
        Load and clean the crime dataset, returning a pandas DataFrame.
        """
        filepath = self.data_dir / "crimedata_csv_AllNeighbourhoods_AllYears.csv"
        df = pd.read_csv(filepath, encoding="utf-8")
        df = self._clean_crime(df)
        return df
        
    def _clean_parks(self, df):
        """
        Clean the parks DataFrame.
        Drops rows with missing names or neighbourhoods, converts
        Hectare to float, and creates a standardized neighbourhood
        column that matches the crime dataset spelling.
        """

        df = df.dropna(subset=["Name", "NeighbourhoodName"]) # drop rows with missing names or neighbourhoods
        df = df.copy() # create a copy of the dataframe to avoid panada SettingWithCopyWarning
 
        # Convert hectare to numeric, fill bad values with 0
        df["Hectare"] = pd.to_numeric(df["Hectare"], errors="coerce").fillna(0.0) # convert the Hectare column to numeric, coercing errors to NaN and filling them with 0.0
 
        # Create a clean neighbourhood name that matches crime data
        df["neighbourhood_clean"] = df["NeighbourhoodName"].replace(
            NEIGHBOURHOOD_MAP
        )
 
        return df
    
    def _clean_crime(self, df):
        """
        Clean the crime DataFrame.
        Drops rows with missing neighbourhood or year, ensures
        year and month are integers, and removes empty neighbourhood entries.
        """

    # Drop rows where neighbourhood is missing or empty
        df = df.dropna(subset=["NEIGHBOURHOOD", "YEAR"])
        df = df[df["NEIGHBOURHOOD"].str.strip() != ""]
        df = df.copy()
 
        # Make sure year and month are integers
        df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
        df["MONTH"] = pd.to_numeric(df["MONTH"], errors="coerce")
        df = df.dropna(subset=["YEAR"])
        df["YEAR"] = df["YEAR"].astype(int)
 
        return df
 
    def _parse_coordinates(self, coord_string):
        """Parse a 'lat, lon' string into two floats.
 
        Args:
            coord_string: A string like '49.249783, -123.15525'.
 
        Returns:
            A tuple (latitude, longitude), or (None, None) if parsing fails.
        """
        try:
            parts = str(coord_string).split(",")
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return lat, lon
        except (ValueError, IndexError):
            return None, None