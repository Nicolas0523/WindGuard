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
        "http://127.0.0.1:8000/analyze",
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
        "http://127.0.0.1:8000/analyze/climate",
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
        "http://127.0.0.1:8000/analyze/short",
        json=payload
    )

    return response.json()