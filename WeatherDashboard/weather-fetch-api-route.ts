from fastapi import APIRouter, HTTPException
import requests

router = APIRouter()

@router.get("/api/weather/current", description="Fetches current weather data for a given location.")
async def get_current_weather(city: str):
    api_key = "your_api_key_here"  # Replace with actual API key or fetch from environment variable
    base_url = "http://api.weatherapi.com/v1/current.json"
    
    params = {
        'key': api_key,
        'q': city
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch weather data")
    
    weather_data = response.json()
    return weather_data