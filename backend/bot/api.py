import time
import requests

BASE_URL = "https://windguard-1.onrender.com"


def poll_result(job_id, timeout=120):
    start = time.time()
    url = f"{BASE_URL}/analyze/status/{job_id}"

    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "done":
                    return data

                if status in ["failed", "error"]:
                    return {"error": "Job failed on server", "details": data}
        except Exception:
            pass

        time.sleep(3)

    return {"error": "Timeout"}


def _send_analysis_request(endpoint: str, polygon: list, start_date: str, end_date: str):
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": polygon
        },
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=15)
        
        if response.status_code not in [200, 201, 202]:
            return {"error": f"Server returned status {response.status_code}", "details": response.text}

        data = response.json()
        job_id = data.get("job_id")  

        if not job_id:
            return {"error": "No job_id returned from server", "response": data}

        return poll_result(job_id)

    except KeyboardInterrupt:
        return {"error": "Process cancelled by user"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def analyze_region(polygon, start_date, end_date):
    return _send_analysis_request("/analyze", polygon, start_date, end_date)


def analyze_climate(polygon, start_date, end_date):
    return _send_analysis_request("/analyze/climate", polygon, start_date, end_date)


def analyze_short(polygon, start_date, end_date):
    return _send_analysis_request("/analyze/short", polygon, start_date, end_date)