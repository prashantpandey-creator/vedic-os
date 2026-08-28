from pydantic import BaseModel, PositiveFloat

class Weather(BaseModel):
    city: str
    temperature: float
    description: str
    humidity: PositiveFloat
    wind_speed: PositiveFloat

    class Config:
        schema_extra = {
            "example": {
                "city": "New York",
                "temperature": 15.2,
                "description": "light rain",
                "humidity": 89.0,
                "wind_speed": 4.6
            }
        }