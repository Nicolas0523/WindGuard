import requests

def analyze_region(polygon, start_date, end_date):
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": polygon
        },
        "start_date": start_date,
        "end_date": end_date
    }

    response = requests.post(
        "https://windguard-1.onrender.com/analyze",
        json=payload
    )

    return response.json()

def analyze_climate(polygon, start_date, end_date):
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": polygon
        },
        "start_date": start_date,
        "end_date": end_date
    }

    response = requests.post(
        "https://windguard-1.onrender.com/analyze/climate",
        json=payload
    )

    return response.json()

def analyze_short(polygon, start_date, end_date):
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": polygon
        },
        "start_date": start_date,
        "end_date": end_date
    }

    response = requests.post(
        "https://windguard-1.onrender.com/analyze/short",
        json=payload
    )

    return response.json()