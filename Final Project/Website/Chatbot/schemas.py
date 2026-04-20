from typing import Optional
from pydantic import BaseModel, Field

# --- COMPARE SCHEMAS ---
class CarSearch(BaseModel):
    brand: Optional[str] = Field(description="The brand of the car", default=None)
    model: Optional[str] = Field(description="The model of the car", default=None)
    trim: Optional[str] = Field(description="The specific trim", default=None)
    year: Optional[int] = Field(description="Manufacturing year", default=None)
    condition: Optional[str] = Field(description="Condition (new/used)", default=None)

class ComparisonRequest(BaseModel):
    car1: CarSearch = Field(description="The first car to compare")
    car2: CarSearch = Field(description="The second car to compare")

# --- RECOMMEND SCHEMAS ---
class CarPreferences(BaseModel):
    max_price: Optional[int] = Field(description="Maximum price budget in EGP", default=None)
    min_price: Optional[int] = Field(description="Minimum price budget in EGP", default=None)
    min_seats: Optional[int] = Field(description="Minimum number of seats required (e.g., family usually means 5+)", default=None)
    body_type: Optional[str] = Field(description="Preferred body type (SUV, Sedan, etc). MUST leave null if not explicitly mentioned.", default=None)
    fuel_type: Optional[str] = Field(description="Preferred fuel type (Gas, Electric, Hybrid). MUST leave null if not explicitly mentioned.", default=None)
    condition: Optional[str] = Field(description="Exactly 'New' or 'Used'. MUST leave null if not explicitly mentioned.", default=None)
    brand_tier: Optional[str] = Field(description="Exactly 'Luxury' or 'Economy'. MUST leave null if not explicitly mentioned.", default=None)
    transmission: Optional[str] = Field(description="Exactly 'Automatic' or 'Manual'. MUST leave null if not explicitly mentioned.", default=None)
    drivetrain: Optional[str] = Field(description="Preferred drivetrain (AWD, FWD, RWD, etc). MUST leave null if not explicitly mentioned.", default=None)
    is_fast: Optional[bool] = Field(description="True if the user mentions wanting a fast, sporty, or high-performance car", default=False)