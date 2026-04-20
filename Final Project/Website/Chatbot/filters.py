import re
import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL, TABLE_CONFIG
from car_dicts import bmw_dict, mercedes_dict

engine = create_engine(DATABASE_URL)

# --- Shorthand number safety net (catches LLM output like "50k") ---
_SHORT_RE = re.compile(r'^(\d+(?:\.\d+)?)\s*(k|mil(?:lion)?s?|m|billion)$', re.IGNORECASE)
_MULT = {'k': 1_000, 'm': 1_000_000, 'mil': 1_000_000, 'million': 1_000_000, 'billion': 1_000_000_000}

def _try_expand(val):
    """If val is a shorthand string like '50k', return 50000. Otherwise return val unchanged."""
    if isinstance(val, str):
        m = _SHORT_RE.match(val.strip())
        if m:
            num = float(m.group(1))
            suffix = m.group(2).lower().rstrip('s')
            return int(num * _MULT.get(suffix, 1))
    return val

def expand_shorthand_numbers(filters: dict) -> dict:
    """Walk filter values and expand any remaining shorthand numbers."""
    out = {}
    for k, v in filters.items():
        if isinstance(v, dict):
            out[k] = {op: _try_expand(inner) for op, inner in v.items()}
        elif isinstance(v, list):
            out[k] = [_try_expand(item) for item in v]
        else:
            out[k] = _try_expand(v)
    return out

def get_brands_for_tier(tier_name):
    """Fetch all brands for a specific tier from the database."""
    try:
        table = TABLE_CONFIG['merged']['table']
        query = text(f"SELECT DISTINCT brand FROM {table} WHERE LOWER(brand_tier) = :tier")
        with engine.connect() as conn:
            result = conn.execute(query, {"tier": tier_name.lower()})
            return [row[0] for row in result]
    except Exception as e:
        print(f"❌ Tier Lookup Error: {e}")
        return []

def get_valid_references(brand=None):
    """Fetch unique brands, models, or models for a brand from merged_cars table."""
    try:
        table = TABLE_CONFIG['merged']['table']
        if brand:
            query = text(f"SELECT DISTINCT model, trim FROM {table} WHERE LOWER(brand) = :brand")
            params = {"brand": brand.lower()}
        else:
            query = text(f"SELECT DISTINCT brand FROM {table}")
            params = {}
            
        with engine.connect() as conn:
            df_ref = pd.read_sql(query, conn, params=params)
            return df_ref
    except Exception as e:
        print(f"❌ Reference Lookup Error: {e}")
        return pd.DataFrame()

def normalize_str(s):
    """Normalize string by lowercasing and removing spaces/dashes."""
    if not s: return ""
    return str(s).lower().replace(" ", "").replace("-", "")

def snap_to_valid(value, valid_list):
    """Find the closest match in valid_list using fuzzy normalization."""
    v_norm = normalize_str(value)
    if not v_norm: return None
    
    for valid in valid_list:
        if v_norm == normalize_str(valid): return valid
            
    for valid in valid_list:
        valid_norm = normalize_str(valid)
        if v_norm in valid_norm or valid_norm in v_norm: return valid
    return None

def get_db_column_mapping(cfg):
    """Fetches actual DB column names dynamically to map to expected config columns."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {cfg['table']} LIMIT 0"))
            db_cols = result.keys()
            
        db_col_map = {c.lower().replace("_", "").replace(" ", ""): c for c in db_cols}
        rename_map = {}
        reverse_map = {}
        
        for expected in cfg['columns']:
            norm_exp = expected.lower().replace("_", "").replace(" ", "")
            if norm_exp in db_col_map:
                actual_db_col = db_col_map[norm_exp]
                rename_map[actual_db_col] = expected
                reverse_map[expected] = actual_db_col
                
        return rename_map, reverse_map
    except Exception as e:
        print(f"❌ Column Mapping Error: {e}")
        return {}, {}

def apply_filters(filters, car_type='merged'):
    if not filters: return pd.DataFrame()
    
    # Safety net: expand any shorthand numbers the LLM may have left as strings
    filters = expand_shorthand_numbers(filters)
    
    cfg = TABLE_CONFIG[car_type]
    rename_map, reverse_map = get_db_column_mapping(cfg)
    
    if not reverse_map:
        return pd.DataFrame() # Cannot map columns

    # Safeguard: Remove 'Used' from condition if LLM hallucinates it
    if 'condition' in filters:
        cond = filters['condition']
        if isinstance(cond, list):
            filters['condition'] = [c for c in cond if str(c).lower() != 'used']
        elif str(cond).lower() == 'used':
            filters.pop('condition')

    # 1. Resolve Tiers -> Brands
    if 'brand tier' in filters or 'Tier' in filters:
        tier_val = filters.pop('brand tier') if 'brand tier' in filters else filters.pop('Tier')
        tier_str = tier_val[0] if isinstance(tier_val, list) else tier_val
        brands_in_tier = get_brands_for_tier(str(tier_str))
        
        if brands_in_tier:
            if 'brand' in filters:
                existing = filters['brand'] if isinstance(filters['brand'], list) else [filters['brand']]
                filters['brand'] = list(set(existing + brands_in_tier))
            else:
                filters['brand'] = brands_in_tier

    # 2. Validate/Snap Brand
    if 'brand' in filters:
        brands = filters['brand'] if isinstance(filters['brand'], list) else [filters['brand']]
        valid_brands_df = get_valid_references()
        if not valid_brands_df.empty:
            valid_brands = valid_brands_df['brand'].tolist()
            snapped_brands = [snap_to_valid(b, valid_brands) for b in brands if snap_to_valid(b, valid_brands)]
            filters['brand'] = snapped_brands if snapped_brands else None

    # 2.5 BMW/Mercedes Dictionary Expansion
    if 'model' in filters and filters.get('brand'):
        models = filters['model'] if isinstance(filters['model'], list) else [filters['model']]
        brands = [str(b).lower() for b in (filters['brand'] if isinstance(filters['brand'], list) else [filters['brand']])]
        
        expanded_models = []
        for m_val in models:
            m_norm = normalize_str(m_val)
            found = False
            if 'bmw' in brands:
                for series, series_models in bmw_dict.items():
                    if m_norm in normalize_str(series):
                        expanded_models.extend(series_models); found = True; break
            if not found and any(b in brands for b in ['mercedes', 'mercedes-benz']):
                for series, series_models in mercedes_dict.items():
                    if m_norm in normalize_str(series) or normalize_str(series) in m_norm:
                        expanded_models.extend(series_models); found = True; break
            if not found:
                expanded_models.append(m_val)
        
        filters['model'] = expanded_models

    # 3. Validate/Snap Model
    if 'model' in filters and filters.get('brand'):
        models = filters['model'] if isinstance(filters['model'], list) else [filters['model']]
        ref_brands = filters['brand'] if isinstance(filters['brand'], list) else [filters['brand']]
        valid_models = []
        for b in ref_brands:
            ref_df = get_valid_references(brand=b)
            if not ref_df.empty:
                valid_models.extend(ref_df['model'].unique().tolist())
        if valid_models:
            snapped_models = [snap_to_valid(m, valid_models) for m in models if snap_to_valid(m, valid_models)]
            filters['model'] = snapped_models if snapped_models else None

    # 4. Self-Correction for Body Types
    body_types = ['suv', 'sedan', 'hatchback', 'coupe', 'truck', 'van', 'mini van', 'crossover']
    if 'model' in filters and filters['model']:
        models = filters['model'] if isinstance(filters['model'], list) else [filters['model']]
        filtered_models = []
        for m in models:
            m_norm = str(m).lower()
            if m_norm in body_types:
                target_col = 'body type'
                if target_col in cfg['columns']:
                    filters[target_col] = m 
            else:
                filtered_models.append(m)
        filters['model'] = filtered_models if filtered_models else None

    # 5. Drivetrain Normalization
    if 'drivetrain' in filters:
        d_val = filters['drivetrain']
        d_vals = d_val if isinstance(d_val, list) else [d_val]
        norm_d = []
        for v in d_vals:
            v_low = str(v).lower()
            if 'rear' in v_low: norm_d.append('RWD')
            elif 'front' in v_low: norm_d.append('FWD')
            elif 'all' in v_low or '4wd' in v_low or '4x4' in v_low: norm_d.append('AWD')
            else: norm_d.append(v)
        filters['drivetrain'] = list(set(norm_d))

    # --- DYNAMIC SQL CONSTRUCTION ---
    sql_clauses = []
    sql_params = {}

    for col, val in filters.items():
        if val is None or not val or col not in cfg['columns'] or col not in reverse_map: 
            continue
            
        db_col = f'"{reverse_map[col]}"'
        is_categorical = col in ['brand', 'model', 'trim', 'condition', 'car condition', 'color', 
                                'body type', 'fuel type', 'transmission', 'drivetrain', 'brand tier', 'engine']
        
        if is_categorical:
            vals = val if isinstance(val, list) else [val]
            
            # Expansion for BMW/Mercedes was moved to pre-validation phase
            
            if col == 'brand':
                expanded_brands = []
                for b_val in vals:
                    if str(b_val).lower() in ['mercedes', 'mercedes-benz']:
                        expanded_brands.extend(['Mercedes', 'Mercedes-Benz'])
                    else:
                        expanded_brands.append(b_val)
                vals = expanded_brands

            # Build SQL ILIKE/Equality logic ignoring spaces/dashes
            cat_clauses = []
            for i, v in enumerate(vals):
                param_key = f"{col.replace(' ', '')}_{i}"
                v_norm = normalize_str(v)
                
                if col in ['condition', 'car condition']:
                    # Exact match
                    sql_params[param_key] = v_norm
                    cat_clauses.append(f"LOWER(REPLACE(REPLACE({db_col}::text, ' ', ''), '-', '')) = :{param_key}")
                elif col == 'engine':
                    m = re.match(r'^([a-z]+)(\d+)$', v_norm)
                    if m and 'cylinder count' in reverse_map:
                        cyl_count = int(m.group(2))
                        cyl_db_col = f'"{reverse_map["cylinder count"]}"'
                        cast_cyl_col = f"CAST(NULLIF(REPLACE({cyl_db_col}::text, ',', ''), '') AS NUMERIC)"
                        
                        param_txt = f"{param_key}_txt"
                        param_cyl = f"{param_key}_cyl"
                        sql_params[param_txt] = f"%{v_norm}%"
                        sql_params[param_cyl] = cyl_count
                        
                        cat_clauses.append(f"(LOWER(REPLACE(REPLACE({db_col}::text, ' ', ''), '-', '')) LIKE :{param_txt} OR {cast_cyl_col} = :{param_cyl})")
                    else:
                        sql_params[param_key] = f"%{v_norm}%"
                        cat_clauses.append(f"LOWER(REPLACE(REPLACE({db_col}::text, ' ', ''), '-', '')) LIKE :{param_key}")
                else:
                    # Contains match
                    sql_params[param_key] = f"%{v_norm}%"
                    cat_clauses.append(f"LOWER(REPLACE(REPLACE({db_col}::text, ' ', ''), '-', '')) LIKE :{param_key}")
            
            if cat_clauses:
                sql_clauses.append(f"({' OR '.join(cat_clauses)})")

        elif col in cfg['numeric']:
            # Handle numbers stored as strings with commas in Postgres
            cast_db_col = f"CAST(NULLIF(REPLACE({db_col}::text, ',', ''), '') AS NUMERIC)"
            
            if isinstance(val, dict):
                for op, v in val.items():
                    param_key = f"{col.replace(' ', '')}_{op.replace('$', '')}"
                    sql_params[param_key] = v
                    if op == '$lt':    sql_clauses.append(f"{cast_db_col} < :{param_key}")
                    elif op == '$lte': sql_clauses.append(f"{cast_db_col} <= :{param_key}")
                    elif op == '$gt':  sql_clauses.append(f"{cast_db_col} > :{param_key}")
                    elif op == '$gte': sql_clauses.append(f"{cast_db_col} >= :{param_key}")
                    elif op == '$eq':  sql_clauses.append(f"{cast_db_col} = :{param_key}")
            else:
                param_key = f"{col.replace(' ', '')}_exact"
                sql_params[param_key] = val
                if col == 'mileage':
                    sql_clauses.append(f"{cast_db_col} BETWEEN :{param_key} - 5000 AND :{param_key} + 5000")
                else:
                    sql_clauses.append(f"{cast_db_col} = :{param_key}")
        else:
            param_key = f"{col.replace(' ', '')}_text"
            sql_params[param_key] = f"%{str(val)}%"
            sql_clauses.append(f"{db_col}::text ILIKE :{param_key}")

    # Build final query
    where_sql = " AND ".join(sql_clauses) if sql_clauses else "1=1"
    final_query = text(f"SELECT * FROM {cfg['table']} WHERE {where_sql}")

    # Execute directly via Pandas
    try:
        with engine.connect() as conn:
            df = pd.read_sql(final_query, conn, params=sql_params)
            
        if not df.empty:
            df = df.rename(columns=rename_map)
            
            # Normalize 'New' condition logic post-load
            if 'car condition' in df.columns and 'condition' in df.columns:
                df.loc[(df['car condition'] == 'New') & (df['condition'] == '-'), 'condition'] = 'New'
                
        return df
    except Exception as e:
        print(f"❌ SQL Execution Error: {e}")
        return pd.DataFrame()