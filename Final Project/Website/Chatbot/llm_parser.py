import json
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from config import TABLE_CONFIG

# --- Shorthand number multipliers ---
_MULTIPLIERS = {
    'k': 1_000,
    'm': 1_000_000,
    'mil': 1_000_000,
    'million': 1_000_000,
    'billion': 1_000_000_000,
}

def get_intent(query):
    q = query.lower()
    
    used_bias = ['used', 'second hand', 'pre-owned', 'pre owned', 'old',
                 'mileage', 'km', 'kilometer', 'kilometers', 'miles', 
                 'overall condition', 'car condition']
    condition_keywords = ['poor', 'fair', 'good', 'very good', 'excellent']
    
    if any(w in q for w in used_bias) or any(w in q for w in condition_keywords):
        return 'used'
        
    new_bias = ['new', 'brand new', 'zero km', '0 km', '0km', '2025', '2026']
    if any(w in q for w in new_bias):
        return 'new'
        
    return 'both'

def normalize_query(query: str) -> str:
    """Pre-process the user query to remove math burdens from the small LLM."""
    
    # 1. Expand shorthands: 50k -> 50000, 1.5mil -> 1500000
    def _replace_shorthand(m):
        number = float(m.group(1))
        suffix = m.group(2).lower().rstrip('s')
        mult = _MULTIPLIERS.get(suffix, 1)
        return str(int(number * mult))

    pattern_shorthand = r'(\d+(?:\.\d+)?)\s*(k|mil(?:lion)?s?|m|billion)\b'
    query = re.sub(pattern_shorthand, _replace_shorthand, query, flags=re.IGNORECASE)

    # 2. Pre-calculate "around X" to "between Y and Z" (±20%)
    def _replace_around(m):
        val = int(m.group(1))
        lower = int(val * 0.9)
        upper = int(val * 1.1)
        return f"between {lower} and {upper}"

    pattern_around = r'\baround\s+(\d+)\b'
    query = re.sub(pattern_around, _replace_around, query, flags=re.IGNORECASE)

    return query

# --- LLM Initialization ---
llm = ChatOllama(
    model="gemma3:4b", 
    temperature=0,      # Strict zero for zero creativity/hallucination
    format="json",      # Forces standard JSON output
    num_predict=512,
    num_ctx=2048,
    timeout=120,
    num_gpu=-1,         # Offloads completely to GPU for maximum speed
)

def get_filters(query, car_type='merged'):
    # Normalise query BEFORE the LLM sees it
    query = normalize_query(query)
    cfg = TABLE_CONFIG['merged']
    
    # Few-shot prompt designed specifically for smaller models
    prompt = f"""You are a strict data extraction AI. Convert the car search query into a JSON object.

Available Keys: {cfg['prompt_keys']}

CRITICAL RULES:
1. ONLY extract keys EXPLICITLY mentioned. If a key isn't mentioned, OMIT IT entirely.
2. Arrays: Use lists for multiple values (e.g., "brand": ["Audi", "BMW"]).
3. Words like Economy/Premium/Luxury go to "brand tier". SUV/Sedan/Van go to "body type". DO NOT put these in "brand" or "model".
4. "condition" must ONLY be: New, Excellent, Very Good, Good, Fair, Poor.
5. "car condition" must ONLY be: New, Used.
6. Numbers/Ranges:
   - "under X" or "less than X" -> {{"$lte": X}}
   - "older than X" -> {{"$lt": X}}
   - "newer than X" -> {{"$gt": X}}
7. Engine Types: Words like "v8", "i6", "v12", "i3", "s6" should be extracted into "engine" as a list (e.g., {{"engine": ["v8"]}}).

EXAMPLES:
Query: "i want luxury suv 2022 to 2024"
{{"brand tier": ["Luxury"], "body type": ["SUV"], "year": {{"$gte": 2022, "$lte": 2024}}}}

Query: "i want toyota corolla, good or very good condition, between 50000 to 60000 km, under 1500000, grey, 2020"
{{"brand": ["Toyota"], "model": ["Corolla"], "condition": ["Good", "Very Good"], "mileage": {{"$gte": 50000, "$lte": 60000}}, "price": {{"$lte": 1500000}}, "color": ["grey"], "year": 2020}}

Query: "i want new bmw 320i and mercedes c180"
{{"car condition": "New", "brand": ["BMW", "Mercedes"], "model": ["320i", "C180"]}}

Query: "i want v8 or v12 sedan"
{{"engine": ["v8", "v12"], "body type": ["Sedan"]}}

Query: "i want a premium, rwd, sedan"
{{"brand tier": ["Premium"], "drivetrain": ["RWD"], "body type": ["Sedan"]}}

Query: "i want luxury and premium sedan, under 50000 km, around 2000000"
{{"brand tier": ["Luxury", "Premium"], "body type": ["Sedan"], "mileage": {{"$lte": 50000}}, "price": {{"$gte": 1800000, "$lte": 2200000}}}}

Query: "i want jeep older than 2020"
{{"brand": ["Jeep"], "year": {{"$lt": 2020}}}}

Query: "I want van newer than 2023"
{{"body type": ["Van"], "year": {{"$gt": 2023}}}}

Now, process this Query:
Query: "{query}"
"""

    print(f"⏳ AI is analyzing your request...")

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        text = response.content.strip()

        if not text:
            return {}

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                return {}
        
        valid_keys = set(cfg['columns']).union({'Tier', 'brand tier'})
        sanitized = sanitize_filters(parsed, valid_keys)
        
        if 'Tier' in sanitized:
            sanitized['brand tier'] = sanitized.pop('Tier')
        
        sanitized = {k: v for k, v in sanitized.items()
                     if v is not None and v != '' and v != {} and v != []
                     and not (isinstance(v, str) and v.strip().lower() == 'null')}
        return sanitized
                
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return {}

def sanitize_filters(raw, valid_keys):
    result = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k in valid_keys:
                result[k] = v
            elif k in ('$and', '$or') and isinstance(v, list):
                for item in v:
                    result.update(sanitize_filters(item, valid_keys))
            elif isinstance(v, dict):
                result.update(sanitize_filters(v, valid_keys))
    return result