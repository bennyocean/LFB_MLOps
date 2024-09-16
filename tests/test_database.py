from app.routes.database import add_data

# no data added yet, this is just a placeholder
def test_add_data():
    result = add_data({"IsWeekend": 1, "distance_to_station": 5, "DistanceStationLog": 6.454777}, token=None)
    assert result == {"message": "Data added successfully"}
