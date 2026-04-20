import os
import json
import joblib
import pandas as pd
import numpy as np
import sqlalchemy
import uuid
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS  
from dotenv import load_dotenv

from pipeline import CarAssessmentPipeline
from scoring import calculate_final_score

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
CURRENT_YEAR = 2026
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ["MULTIMODAL_SECRET_KEY"] 
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# ─── Load DB Data ───────────────────────────────────────────────────────────
print("Connecting to PostgreSQL database...")
DB_URI = os.getenv("DATABASE_URL")
if not DB_URI:
    raise RuntimeError("DATABASE_URL is not set. Please define it in .env")
engine_db = sqlalchemy.create_engine(DB_URI)

df = pd.read_sql_table("cars", engine_db)
print(f"Loaded {len(df)} rows.")

rename_map = {
    'brand': 'Brand', 'model': 'Model', 'trim': 'Trim', 'year': 'Year',
    'mileage': 'Mileage', 'color': 'Color', 'brand_tier': 'Brand_Tier',
    'transmission': 'Transmission', 'fuel_type': 'Fuel Type', 'body_type': 'Body Shape',
    'engine': 'Engine', 'engine_capacity': 'Engine Capacity', 'cylinder_count': 'Cylinder Count',
    'turbo_count': 'Turbo Count', 'horsepower': 'HP', 'drivetrain': 'Drivetrain',
    'price': 'Price'
}
df = df.rename(columns=rename_map).drop(columns=["image_paths", "condition", "car_condition", "Condition", "Image Paths"], errors='ignore')

brand_tier_map = df.groupby("Brand")["Brand_Tier"].first().to_dict()

CONDITION_SCORES = {"Excellent": 1.5, "Very Good": 3.5, "Good": 5.5, "Fair": 7.5, "Poor": 9.5}
CONDITION_MULTIPLIERS = {"Excellent": 1.10, "Very Good": 1.05, "Good": 1.00, "Fair": 0.90, "Poor": 0.80}

def get_unique(col):
    return sorted(df[col].dropna().unique().tolist()) if col in df.columns else []

GLOBAL_OPTIONS = {
    "colors": get_unique("Color"), "fuel_types": get_unique("Fuel Type"),
    "body_shapes": get_unique("Body Shape"), "transmissions": get_unique("Transmission"),
    "drivetrains": get_unique("Drivetrain"),
}

# ─── Load Models ─────────────────────────────────────────────────────────────
TRAINING_METADATA_PATH = os.path.join(MODELS_DIR, "training_metadata.pkl")
training_metadata = joblib.load(TRAINING_METADATA_PATH) if os.path.exists(TRAINING_METADATA_PATH) else {}
selected_features = training_metadata.get("selected_features", [])

price_models = {}
for name, filename in {"LightGBM_best": "LightGBM_best.pkl"}.items():
    path = os.path.join(MODELS_DIR, "price", filename)
    if os.path.exists(path):
        price_models[name] = joblib.load(path)
print(f"Loaded {len(price_models)} price model(s).")

condition_pipeline = CarAssessmentPipeline(BASE_DIR)

def _preload_models_on_startup():
    logging.info("Preloading condition models...")
    condition_pipeline.load_all_models()

# ─── Helpers ─────────────────────────────────────────────────────────────────
def lookup_model_average_price(brand, model):
    subset = df.loc[(df["Brand"] == brand) & (df["Model"] == model), "Price"].dropna()
    return float(subset.mean()) if not subset.empty else float(df["Price"].dropna().mean() if "Price" in df.columns else 0.0)

def parse_numeric(val):
    try: return float(str(val).split("/")[0].strip()) if val else 0.0
    except ValueError: return 0.0

def build_model_input(data):
    year = int(parse_numeric(data.get("year")))
    mileage = parse_numeric(data.get("mileage"))
    brand, model = data.get("brand", ""), data.get("model", "")
    car_age = max(CURRENT_YEAR - year, 1)
    
    tier_mapping = {'exotic': 1, 'luxury': 2, 'premium': 3, 'economy': 4}
    brand_tier_raw = brand_tier_map.get(brand, 3)
    brand_tier = tier_mapping.get(str(brand_tier_raw).lower(), 3) if isinstance(brand_tier_raw, str) else brand_tier_raw
        
    condition_label = data.get("condition", "Good")
    condition_score = CONDITION_SCORES.get(condition_label, 5.5)

    row = {
        "Brand": brand, "Model": model, "Trim": data.get("trim", ""), "Year": year,
        "Mileage": mileage, "Color": data.get("color", ""),
        "Fuel Type": data.get("fuel_type", ""), "Body Shape": data.get("body_shape", ""),
        "Transmission": data.get("transmission", ""), "Engine": data.get("engine", ""),
        "Engine Capacity": parse_numeric(data.get("engine_capacity")),
        "Cylinder Count": int(parse_numeric(data.get("cylinder_count"))),
        "Turbo Count": int(parse_numeric(data.get("turbo_count"))),
        "HP": int(parse_numeric(data.get("hp"))),
        "Drivetrain": data.get("drivetrain", ""),
        "car_age": car_age, "miles_per_year": round(mileage / car_age, 1) if car_age > 0 else mileage,
        "Brand_Tier": brand_tier, "Condition": condition_label,
        "Condition_Score": condition_score, "model_average_price": lookup_model_average_price(brand, model),
    }

    if selected_features:
        row = {f: row.get(f, "") for f in selected_features}

    return pd.DataFrame([row]), car_age, row["miles_per_year"], brand_tier, condition_score

# ─── Flask Routes ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", brands=get_unique("Brand"), options=GLOBAL_OPTIONS, conditions=list(CONDITION_SCORES.keys()))

@app.route("/api/models")
def api_models():
    return jsonify(sorted(df[df["Brand"] == request.args.get("brand", "")]["Model"].dropna().unique().tolist()))

@app.route("/api/trims")
def api_trims():
    return jsonify(sorted(df[(df["Brand"] == request.args.get("brand", "")) & (df["Model"] == request.args.get("model", ""))]["Trim"].dropna().unique().tolist()))

@app.route("/api/engines")
def api_engines():
    brand, model, trim = request.args.get("brand", ""), request.args.get("model", ""), request.args.get("trim", "")
    subset = df[(df["Brand"] == brand) & (df["Model"] == model)]
    trim_subset = subset[subset["Trim"] == trim]
    
    engines = trim_subset["Engine"].dropna().unique().tolist() if not trim_subset.empty else subset["Engine"].dropna().unique().tolist()
    return jsonify(sorted(list(set(engines + ["Electric", "Other"]))))

@app.route("/api/details")
def api_details():
    brand, model, trim, engine = [request.args.get(k, "") for k in ["brand", "model", "trim", "engine"]]
    avg_price = lookup_model_average_price(brand, model)

    def get_vals(col, return_all=False):
        # Fallback hierarchy: Exact Match -> Engine Match -> Model Match
        subs = [
            (df[(df["Brand"] == brand) & (df["Model"] == model) & (df["Trim"] == trim) & (df["Engine"] == engine)], return_all),
            (df[(df["Brand"] == brand) & (df["Model"] == model) & (df["Engine"] == engine)], False),
            (df[(df["Brand"] == brand) & (df["Model"] == model)], False)
        ]
        for sub, ret_all in subs:
            if not sub.empty and col in sub.columns and not sub[col].dropna().empty:
                return sub[col].dropna().unique().tolist() if ret_all else [str(sub[col].dropna().mode().iloc[0])]
        return [""]

    if engine == "Electric":
        return jsonify({
            "engine_capacity": 0, "cylinder_count": 0, "turbo_count": 0,
            "hp": get_vals("HP")[0], "drivetrain": get_vals("Drivetrain")[0],
            "fuel_type": "Electric", "body_shape": get_vals("Body Shape")[0],
            "transmission": "Automatic", "brand_tier": brand_tier_map.get(brand, 3),
            "model_average_price": avg_price, "colors": get_vals("Color", True),
        })

    return jsonify({
        "engine_capacity": get_vals("Engine Capacity")[0] or 0,
        "cylinder_count": get_vals("Cylinder Count")[0] or 0,
        "turbo_count": get_vals("Turbo Count")[0] or 0,
        "hp": get_vals("HP")[0],
        "drivetrain": get_vals("Drivetrain")[0],
        "fuel_type": get_vals("Fuel Type")[0],
        "body_shape": get_vals("Body Shape")[0],
        "transmission": get_vals("Transmission")[0],
        "brand_tier": brand_tier_map.get(brand, 3),
        "model_average_price": avg_price,
        "colors": get_vals("Color", True),
    })

@app.route("/assess", methods=["POST"])
def assess():
    files = request.files.getlist("files")
    valid_files = [f for f in files if f and f.filename and "." in f.filename and f.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT]
    
    if not valid_files:
        return jsonify({"error": "No valid image files sent."}), 400

    sess_dir = os.path.join(UPLOAD_DIR, uuid.uuid4().hex[:8])
    os.makedirs(sess_dir, exist_ok=True)
    
    saved = []
    for f in valid_files:
        path = os.path.join(sess_dir, secure_filename(f.filename))
        f.save(path)
        saved.append(path)

    try:
        score_out = calculate_final_score(condition_pipeline.process_images(saved))
        score = score_out.get("final_score", 6.0)
        
        if score >= 8.5: label = "Excellent"
        elif score >= 7.0: label = "Very Good"
        elif score >= 5.0: label = "Good"
        elif score >= 3.0: label = "Fair"
        else: label = "Poor"

        return jsonify({"condition": label, "raw_score": score, "damage_summary": score_out.get("damage_summary", ""), "total_loss": score_out.get("total_loss", False)})
    except Exception as exc:
        logging.exception("Pipeline error")
        return jsonify({"error": str(exc)}), 500

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        input_data, car_age, miles_per_year, brand_tier, condition_score = build_model_input(data)
        multiplier = CONDITION_MULTIPLIERS.get(data.get("condition", "Good"), 1.0)

        predictions = {}
        for name, mdl in price_models.items():
            try:
                raw_pred = mdl.predict(input_data)[0]
                predictions[name] = round(float(raw_pred * multiplier), 0)
            except Exception as e:
                predictions[name] = f"Error: {e}"

        valid = [v for v in predictions.values() if isinstance(v, (int, float))]
        return jsonify({
            "predictions": predictions,
            "average": round(sum(valid) / len(valid), 0) if valid else 0,
            "inputs": {
                "car_age": car_age, "miles_per_year": miles_per_year, "brand_tier": brand_tier,
                "condition_score": condition_score, "condition_string": data.get("condition", "Good"),
                "model_average_price": input_data.at[0, 'model_average_price']
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    is_debug = os.getenv("MULTIMODAL_DEBUG", "false").lower() == "true"
    is_worker = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    if is_worker or not is_debug:
        _preload_models_on_startup()
        
    app.run(
        debug=is_debug, 
        host=os.environ["MULTIMODAL_HOST"], 
        port=int(os.environ["MULTIMODAL_PORT"])
    )