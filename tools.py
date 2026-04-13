import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather(city: str) -> dict:
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return {"error": "API KEY IS MISSING"}

    # --- STEP 1: Use Geocoding API to find best match (handles typos + small places) ---
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {
        "q": city,
        "limit": 5,          # get up to 5 matches
        "appid": api_key
    }

    try:
        geo_response = requests.get(geo_url, params=geo_params)
        geo_response.raise_for_status()
        locations = geo_response.json()

        if not locations:
            # --- STEP 2: If no match, return helpful error ---
            return {
                "error": f"Could not find '{city}'. It may be too small or misspelled.",
                "suggestion": "Try a nearby larger town or city instead."
            }

        # Pick the best match (first result)
        best = locations[0]
        lat = best["lat"]
        lon = best["lon"]
        matched_name = best.get("name", city)
        country = best.get("country", "")
        state = best.get("state", "")

        # --- STEP 3: Fetch weather using coordinates (most accurate) ---
        weather_url = "https://api.openweathermap.org/data/2.5/weather"
        weather_params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric"
        }

        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()
        data = weather_response.json()

        # Build a note if the name was corrected / a nearby place was used
        searched_name_clean = city.strip().lower()
        matched_name_clean = matched_name.strip().lower()
        note = None
        if searched_name_clean != matched_name_clean:
            location_label = matched_name
            if state:
                location_label += f", {state}"
            if country:
                location_label += f", {country}"
            note = f"Showing weather for '{location_label}' (closest match to '{city}')"

        result= {
            "city": matched_name,
            "state": state,
            "country": country,
            "temperature": f"{data['main']['temp']}°C",
            "feels_like": f"{data['main']['feels_like']}°C",
            "description": data['weather'][0]['description'],
            "humidity": f"{data['main']['humidity']}%",
            "rain": f"{data.get('rain', {}).get('1h', 0)}mm",
            "wind_speed": f"{data['wind']['speed']} m/s",
        }
        if note:
            result["note"] = note

        return result

    except Exception as e:
        return {"error": f"Could not fetch weather data: {str(e)}"}


if __name__ == "__main__":
    print(get_weather("Mananthavady"))   # small place
    print(get_weather("Landan"))         # typo for London
    print(get_weather("Kochi"))          # normal city