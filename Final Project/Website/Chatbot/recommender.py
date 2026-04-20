import re
from typing import Optional
from sqlalchemy import text
from config import engine, BASE_AGGREGATION_SQL, clean_db_dict
from schemas import CarPreferences

def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in keywords)


def _infer_body_type_from_query(user_query: str) -> Optional[str]:
    lowered = user_query.lower()
    body_type_aliases = {
        "suv": ["suv", "crossover", "4x4", "4wd"],
        "sedan": ["sedan", "saloon"],
        "hatchback": ["hatchback", "hatch"],
        "coupe": ["coupe"],
        "pickup": ["pickup", "pick-up", "truck"],
        "van": ["van", "minivan", "mpv"],
        "wagon": ["wagon", "estate"],
        "convertible": ["convertible", "cabriolet", "roadster"],
    }

    matched = [name for name, aliases in body_type_aliases.items() if any(alias in lowered for alias in aliases)]
    if len(matched) == 1:
        return matched[0]
    return None


def _infer_condition_from_query(user_query: str) -> Optional[str]:
    lowered = user_query.lower()
    if any(w in lowered for w in ["brand new", "new", "zero km", "0 km", "0km"]):
        return "New"
    if any(w in lowered for w in ["used", "second hand", "pre-owned", "pre owned"]):
        return "Used"
    return None


def _infer_min_seats_from_query(user_query: str) -> Optional[int]:
    lowered = user_query.lower()
    direct_match = re.search(r"family\s+of\s+(\d+)", lowered)
    if direct_match:
        return int(direct_match.group(1))
    if any(word in lowered for word in ["family", "kids", "children"]):
        return 5
    return None


def _looks_like_new(car: dict) -> bool:
    value = str(car.get("car_condition") or car.get("condition") or "").strip().lower()
    return "new" in value


def _enforce_hard_constraints(cars: list, min_seats: Optional[int], body_type: Optional[str], condition: Optional[str]) -> list:
    filtered = []
    wanted_new = condition is not None and condition.lower() == "new"
    wanted_used = condition is not None and condition.lower() == "used"

    for car in cars:
        if min_seats is not None:
            seats = _to_float(car.get("seats"))
            if seats is not None and seats < min_seats:
                continue

        if body_type:
            bt = str(car.get("body_type") or "").lower()
            if body_type.lower() not in bt:
                continue

        if wanted_new and not _looks_like_new(car):
            continue
        if wanted_used and _looks_like_new(car):
            continue

        filtered.append(car)

    return filtered

def rank_recommendations(cars: list, prefs: CarPreferences, user_query: str) -> list:
    if not cars:
        return []

    query = user_query.lower()
    weights = {"speed": 1.0, "acceleration": 1.0, "power": 1.0, "efficiency": 1.0, "value": 1.0, "practicality": 1.0, "size": 1.0}

    if prefs.is_fast or _contains_any(query, ["fast", "quick", "sport", "sporty", "performance", "speed", "accelerat"]):
        weights["speed"] += 2.0; weights["acceleration"] += 2.0; weights["power"] += 1.5
    if _contains_any(query, ["efficient", "economy", "fuel", "range", "ev", "electric", "hybrid", "consumption"]):
        weights["efficiency"] += 2.5; weights["value"] += 0.5
    if prefs.max_price is not None or _contains_any(query, ["budget", "affordable", "cheap", "value", "price", "under", "within"]):
        weights["value"] += 2.0
    if prefs.min_seats is not None or _contains_any(query, ["family", "kids", "children", "space", "spacious", "roomy"]):
        weights["practicality"] += 2.0; weights["size"] += 1.0
    if _contains_any(query, ["compact", "small", "city", "easy parking"]):
        weights["size"] += 2.0
    if _contains_any(query, ["luxury", "premium"]):
        weights["power"] += 1.0; weights["speed"] += 0.5

    fields = {
        "max_speed": [(_to_float(c.get("avg_max_speed")), c) for c in cars],
        "acceleration": [(_to_float(c.get("avg_acceleration")), c) for c in cars],
        "horsepower": [(_to_float(c.get("avg_horsepower")), c) for c in cars],
        "torque": [(_to_float(c.get("avg_torque")), c) for c in cars],
        "fuel_consumption": [(_to_float(c.get("avg_fuel_consumption")), c) for c in cars],
        "ev_range": [(_to_float(c.get("avg_ev_range")), c) for c in cars],
        "price": [(_to_float(c.get("avg_price")), c) for c in cars],
        "seats": [(_to_float(c.get("seats")), c) for c in cars],
        "wheelbase": [(_to_float(c.get("avg_wheelbase")), c) for c in cars],
        "length": [(_to_float(c.get("avg_length")), c) for c in cars],
    }

    min_max = {}
    for name, values in fields.items():
        nums = [v for v, _ in values if v is not None]
        min_max[name] = (min(nums), max(nums)) if nums else (None, None)

    def normalize(value: Optional[float], metric: str, reverse: bool = False) -> float:
        if value is None: return 0.45
        lo, hi = min_max[metric]
        if lo is None or hi is None or hi == lo: return 0.5
        scaled = (value - lo) / (hi - lo)
        return 1 - scaled if reverse else scaled

    compact_preferred = _contains_any(query, ["compact", "small", "city", "easy parking"])
    wants_efficiency = _contains_any(query, ["efficient", "economy", "fuel", "consumption", "range"])
    wants_electrified = (
        (prefs.fuel_type or "").lower() in ["electric", "ev", "hybrid", "phev"]
        or _contains_any(query, ["electric", "ev", "hybrid", "phev"])
    )
    required_condition = prefs.condition.lower() if prefs.condition else None
    required_seats = prefs.min_seats
    required_body = prefs.body_type.lower() if prefs.body_type else None
    total_weight = sum(weights.values())

    ranked = []
    for car in cars:
        speed_score = normalize(_to_float(car.get("avg_max_speed")), "max_speed")
        acceleration_score = normalize(_to_float(car.get("avg_acceleration")), "acceleration", reverse=True)
        power_score = (normalize(_to_float(car.get("avg_horsepower")), "horsepower") + normalize(_to_float(car.get("avg_torque")), "torque")) / 2
        fuel_eff_score = normalize(_to_float(car.get("avg_fuel_consumption")), "fuel_consumption", reverse=True)
        ev_range_score = normalize(_to_float(car.get("avg_ev_range")), "ev_range")
        if wants_electrified:
            efficiency_score = (fuel_eff_score * 0.45) + (ev_range_score * 0.55)
        else:
            efficiency_score = (fuel_eff_score * 0.9) + (ev_range_score * 0.1)

        # Keep recommendations aligned with hard preferences when data is imperfect.
        if required_condition == "new" and not _looks_like_new(car):
            efficiency_score *= 0.55
        if required_condition == "used" and _looks_like_new(car):
            efficiency_score *= 0.7
        if required_seats is not None:
            seats = _to_float(car.get("seats"))
            if seats is not None and seats < required_seats:
                efficiency_score *= 0.7
        if required_body:
            car_body = str(car.get("body_type") or "").lower()
            if required_body not in car_body:
                efficiency_score *= 0.65

        if wants_efficiency:
            efficiency_score = min(1.0, efficiency_score * 1.15)
        value_score = normalize(_to_float(car.get("avg_price")), "price", reverse=True)
        practicality_score = (normalize(_to_float(car.get("seats")), "seats") * 0.6 + normalize(_to_float(car.get("avg_wheelbase")), "wheelbase") * 0.4)
        
        size_score = (normalize(_to_float(car.get("avg_length")), "length", reverse=compact_preferred) * 0.6 + normalize(_to_float(car.get("avg_wheelbase")), "wheelbase", reverse=compact_preferred) * 0.4)

        final_score = (
            speed_score * weights["speed"] + acceleration_score * weights["acceleration"] +
            power_score * weights["power"] + efficiency_score * weights["efficiency"] +
            value_score * weights["value"] + practicality_score * weights["practicality"] +
            size_score * weights["size"]
        ) / total_weight

        enriched = dict(car)
        enriched["match_score"] = round(final_score, 3)
        ranked.append(enriched)

    ranked.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return ranked[:4]


def query_recommendations(prefs: CarPreferences, user_query: str) -> list:
    conditions = []
    params = {}
    
    if prefs.max_price:
        conditions.append("price <= :max_price"); params["max_price"] = prefs.max_price
    if prefs.min_price:
        conditions.append("price >= :min_price"); params["min_price"] = prefs.min_price
    inferred_condition = _infer_condition_from_query(user_query)
    inferred_min_seats = _infer_min_seats_from_query(user_query)

    effective_min_seats = prefs.min_seats if prefs.min_seats is not None else inferred_min_seats
    if effective_min_seats:
        conditions.append("seats >= :min_seats"); params["min_seats"] = effective_min_seats
        
    bad_words = ["unknown", "unspecified", "any", "n/a", "none"]
    
    inferred_body_type = _infer_body_type_from_query(user_query)
    body_type_value = prefs.body_type
    if (
        inferred_body_type
        and (not body_type_value or body_type_value.lower() in bad_words)
    ):
        body_type_value = inferred_body_type

    if body_type_value and body_type_value.lower() not in bad_words:
        conditions.append("body_type ILIKE :body_type")
        params["body_type"] = f"%{body_type_value}%"
    if prefs.fuel_type and prefs.fuel_type.lower() not in bad_words:
        conditions.append("fuel_type ILIKE :fuel_type"); params["fuel_type"] = f"%{prefs.fuel_type}%"
    effective_condition = prefs.condition or inferred_condition
    if effective_condition and effective_condition.lower() not in bad_words:
        cond_val = "New" if effective_condition.lower() == "new" else "Used"
        # Filter on listing-level car_condition to avoid leaking mixed-condition groups.
        conditions.append("car_condition ILIKE :cond")
        params["cond"] = f"%{cond_val}%"
    if prefs.brand_tier and prefs.brand_tier.lower() not in bad_words:
        conditions.append("brand_tier ILIKE :tier"); params["tier"] = f"%{prefs.brand_tier}%"
    if prefs.transmission and prefs.transmission.lower() not in bad_words:
        conditions.append("transmission ILIKE :transmission"); params["transmission"] = f"%{prefs.transmission}%"
    if prefs.drivetrain and prefs.drivetrain.lower() not in bad_words:
        conditions.append("drivetrain ILIKE :drivetrain"); params["drivetrain"] = f"%{prefs.drivetrain}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = text(f"""
        SELECT {BASE_AGGREGATION_SQL}
        FROM cars 
        WHERE {where_clause}
        GROUP BY brand, model
        LIMIT 80
    """)
    
    recommended_cars = []
    try:
        with engine.connect() as conn:
            results = conn.execute(query, params).mappings().fetchall()
            for row in results:
                recommended_cars.append(clean_db_dict(dict(row)))
    except Exception as e:
        print(f"\n⚠️ Database Error: {e}")
        
    effective_body_type = body_type_value if body_type_value else None
    recommended_cars = _enforce_hard_constraints(
        recommended_cars,
        min_seats=effective_min_seats,
        body_type=effective_body_type,
        condition=effective_condition,
    )

    # Carry inferred constraints into ranking when extractor misses them.
    ranking_prefs = prefs.model_copy(deep=True) if hasattr(prefs, "model_copy") else prefs.copy(deep=True)
    if ranking_prefs.min_seats is None:
        ranking_prefs.min_seats = effective_min_seats
    if not ranking_prefs.condition:
        ranking_prefs.condition = effective_condition
    if not ranking_prefs.body_type and effective_body_type:
        ranking_prefs.body_type = effective_body_type

    return rank_recommendations(recommended_cars, ranking_prefs, user_query)