
from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get("/api/weather/current")
async def fetch_weather_api(location: str):
    try:
        response = requests.get(f"https://api.weather.com/location/{location}")
        if response.status_code == 200:
            return {"weather_data": response.json()}
        else:
            raise HTTPException(status_code=404, detail="Weather data not found for the given location")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
