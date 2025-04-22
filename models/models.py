from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import List, Optional
from datetime import datetime


class CurrentWeather(BaseModel):
    """Raw API response structure"""
    temperature_2m: float = Field(..., description="Air temperature at 2m")
    windspeed_10m: float = Field(..., description="Wind speed at 10m")
    weather_code: int = Field(..., description="WMO weather code")
    is_day: int = Field(..., description="1=Day, 0=Night")
    time: str = Field(..., description="Observation time")
    precipitation: Optional[float] = Field(None)
    relative_humidity_2m: Optional[float] = Field(None)
    
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True
    )

class WeatherResponse(BaseModel):
    """Complete API response validation"""
    latitude: float
    longitude: float
    current: CurrentWeather

class ProcessedWeatherData(BaseModel):
    """Agent-ready weather data"""
    location_name: str
    coordinates: str
    temperature: float
    windspeed: float
    weather_code: int
    is_day: bool
    time: str
    precipitation: Optional[float]
    humidity: Optional[float]
    
    @computed_field
    @property
    def condition_description(self) -> str:
        codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
            3: "Overcast", 45: "Fog", 48: "Rime fog",
            51: "Light drizzle", 56: "Freezing drizzle",
            61: "Slight rain", 66: "Freezing rain",
            80: "Rain showers", 95: "Thunderstorm",
            96: "Severe thunderstorm"
        }
        return codes.get(self.weather_code, "Unknown condition")
    
    model_config = ConfigDict(extra="ignore")


# Define the Pydantic model for itinerary data
class ProcessedItineraryData(BaseModel):
    destination: str
    days: int
    interests: List[str]
    current_date: str
    weather: Optional[str] = None  # Optional field for weather info

class roomInfo(BaseModel):
    id: Optional[str] = Field(default=None, description="UUID of the room")
    room_number: str = Field(..., min_length=1, max_length=50, description="Unique room number or label")
    room_type: str = Field(..., pattern=r"^(Standard|Family|Deluxe)$", description="Type of the room")
    description: str = Field(..., description="Room description and features")
    max_guests: int = Field(..., gt=0, description="Maximum number of guests allowed")
    status: str = Field(..., pattern=r"^(Available|Occupied|Under Maintenance)$", description="Current room status")
    price_per_night: float = Field(..., gt=0, description="Cost per night")
    image_id: Optional[str] = Field(default=None, description="Optional image reference ID")
    created_at: Optional[str] = Field(
        default_factory=lambda: str(datetime.now()),
        description="Room creation timestamp"
    )

    model_config = ConfigDict(extra="forbid")