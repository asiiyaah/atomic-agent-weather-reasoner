import os
import requests   #for api calls
from dotenv import load_dotenv #load env file

load_dotenv()

#url="http://api.openweathermap.org/data/2.5/direct?q={city}&appid={api_key}&units=metric"

def get_weather(city: str) -> dict:   #input is city(string) , o/p is a dict
    api_key=os.getenv("WEATHER_API_KEY")
    if not api_key:
        return {"error":"API KEY IS MISSING"}
    base_url="https://api.openweathermap.org/data/2.5/weather"
    params={
        "q":city,
        "appid":api_key,
        "units":"metric"
    } 
    try:
        response=requests.get(base_url,params=params)
        response.raise_for_status()    #for https errors
        data=response.json()  
        return{
            "city":data["name"],
            "temperature":f"{data['main']['temp']}°C",
            "description":data['weather'][0]['description'],
            "humidity":f"{data['main']['humidity']}%",
            "rain": f"{data.get('rain', {}).get('1h', 0)}mm",
            "wind_speed": f"{data['wind']['speed']} m/s"
        }  #convert to python dict
    except Exception as e:
        return {"error":f"Could not fetch weather data {str(e)}"}
    
if __name__ == "__main__":
    print(get_weather("Riyadh"))