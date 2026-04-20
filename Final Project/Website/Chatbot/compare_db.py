from typing import Optional
from sqlalchemy import text
from config import engine, BASE_AGGREGATION_SQL, clean_db_dict
from schemas import CarSearch

def search_car_in_db(search: CarSearch) -> Optional[dict]:
    conditions = []
    params = {}
    
    if search.brand:
        conditions.append("brand ILIKE :brand")
        params["brand"] = f"%{search.brand}%"
    if search.model:
        conditions.append("model ILIKE :model")
        params["model"] = f"%{search.model}%"
    if search.trim:
        conditions.append("trim ILIKE :trim")
        params["trim"] = f"%{search.trim}%"
    if search.year:
        conditions.append("year = :year")
        params["year"] = search.year
    if search.condition:
        normalized_condition = search.condition.strip().lower()
        if normalized_condition in {"new", "brand new"}:
            cond_val = "New"
        elif normalized_condition in {"used", "pre-owned", "second hand"}:
            cond_val = "Used"
        else:
            cond_val = None

        if cond_val:
            conditions.append("(car_condition ILIKE :cond OR condition ILIKE :cond)")
            params["cond"] = f"%{cond_val}%"
        
    if not conditions:
        return None
        
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT {BASE_AGGREGATION_SQL},
            ROUND(AVG(model_average_price::numeric)) AS overall_model_avg_price,
            ROUND(AVG(model_min_price::numeric)) AS overall_model_min_price
        FROM cars 
        WHERE {where_clause}
        HAVING COUNT(*) > 0
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, params).mappings().first()
            if result and result["available_listings"] > 0:
                return clean_db_dict(dict(result))
    except Exception as e:
        print(f"\n⚠️ Database Error: {e}")
        
    return None