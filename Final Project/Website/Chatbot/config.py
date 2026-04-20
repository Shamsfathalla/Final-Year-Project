import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_ollama import ChatOllama

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")
LLM_JSON_MODEL = os.getenv("LLM_JSON_MODEL", LLM_MODEL)

engine = create_engine(DATABASE_URL)

base_llm = ChatOllama(model=LLM_MODEL, temperature=0)
json_llm = ChatOllama(
    model=LLM_JSON_MODEL, temperature=0, format="json", 
    num_predict=768, num_ctx=4096, timeout=120, num_gpu=-1
)

# --- SHARED UTILITIES ---
def clean_db_dict(car_dict: dict) -> dict:
    """Removes None, empty strings, and dashes to save LLM tokens."""
    return {k: v for k, v in car_dict.items() if v is not None and v != "" and str(v).strip() != "-"}

# Centralized SQL projection for comparing and recommending aggregated cars
BASE_AGGREGATION_SQL = """
   MAX(car_id) AS car_id, MAX(image_paths) AS image_paths, MAX(brand) AS brand, MAX(model) AS model, MAX(trim) AS trim, MAX(year) AS year, MAX(car_condition) AS car_condition,
    COUNT(*) AS available_listings, ROUND(AVG(price::numeric)) AS avg_price, ROUND(AVG(mileage::numeric)) AS avg_mileage,
    MAX(engine) AS engine, ROUND(AVG(engine_capacity::numeric)) AS avg_engine_capacity, ROUND(AVG(horsepower::numeric)) AS avg_horsepower,
    ROUND(AVG(torque::numeric)) AS avg_torque, ROUND(AVG(cylinder_count::numeric)) AS avg_cylinders, ROUND(AVG(turbo_count::numeric)) AS avg_turbos,
    MAX(transmission) AS transmission, ROUND(AVG(number_of_gears::numeric)) AS avg_gears, MAX(drivetrain) AS drivetrain,
    ROUND(AVG(max_speed::numeric)) AS avg_max_speed, ROUND(AVG(acceleration::numeric), 1) AS avg_acceleration,
    MAX(fuel_type) AS fuel_type, ROUND(AVG(fuel_consumption::numeric), 2) AS avg_fuel_consumption, 
    ROUND(AVG(electric_fuel_consumption::numeric), 2) AS avg_electric_consumption, ROUND(AVG(max_electric_driving_range::numeric)) AS avg_ev_range,
    MAX(body_type) AS body_type, ROUND(AVG(seats::numeric)) AS seats, ROUND(AVG(length::numeric)) AS avg_length,
    ROUND(AVG(width::numeric)) AS avg_width, ROUND(AVG(wheelbase::numeric)) AS avg_wheelbase,
    ROUND(AVG(fuel_tank_capacity::numeric)) AS avg_fuel_tank
"""

TABLE_CONFIG = {
    'merged': {
        'table': 'cars',
        'columns': [
            'Car ID', 'brand', 'model', 'trim', 'year', 'price', 'mileage', 'color', 
            'brand tier', 'transmission', 'fuel type', 'body type', 'condition', 
            'car condition', 'engine', 'engine capacity', 'cylinder count', 
            'turbo count', 'horsepower', 'torque', 'max speed', 'acceleration', 
            'drivetrain', 'number of gears', 'fuel tank capacity', 'fuel consumption', 
            'electric fuel consumption', 'max electric driving range', 'width', 
            'length', 'height', 'wheelbase', 'seats', 'image paths'
        ],
        'numeric': [
            'year', 'price', 'mileage', 'engine capacity', 'cylinder count', 
            'turbo count', 'horsepower', 'torque', 'max speed', 'acceleration', 
            'number of gears', 'fuel tank capacity', 'fuel consumption', 
            'electric fuel consumption', 'max electric driving range', 
            'width', 'length', 'height', 'wheelbase', 'seats'
        ],
        'prompt_keys': 'brand, model, trim, year, price, mileage, color, brand tier, transmission, fuel type, body type, condition, car condition, engine, engine capacity, cylinder count, turbo count, horsepower, torque, max speed, acceleration, drivetrain, number of gears, fuel tank capacity, fuel consumption, electric fuel consumption, max electric driving range, width, length, height, wheelbase, seats'
    }
}