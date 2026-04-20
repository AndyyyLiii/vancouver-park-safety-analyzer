class Park:
    """
    Stores the park's name, neighbourhood, location, size,
    available facilities, and whether it has washrooms.
    """
    def __init__(self, park_id, name, neighbourhood, latitude
                 , longitude, hectare, has_facilities, has_washroom):
        """
        Initialize a Park instance.
        """
        self.park_id = park_id
        self.name = name
        self.neighbourhood = neighbourhood
        self.latitude = latitude
        self.longitude = longitude
        self.hectare = hectare
        self.has_facilities = has_facilities
        self.has_washroom = has_washroom
    def __repr__(self):
        """
        Return a readable string representation of the Park.
        """
        return f"Park(name='{self.name}', neighbourhood='{self.neighbourhood}')"
    