import pandas as pd
import numpy as np
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Centralized Config & Schemas
from config import base_llm
from schemas import ComparisonRequest, CarPreferences

# Feature imports
from compare_db import search_car_in_db as compare_search_db
from recommender import query_recommendations
from llm_parser import get_filters, get_intent
from filters import apply_filters
from ranking import rank_results_by_similarity

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)
CORS(app) 

def do_compare(user_input):
    structured_llm_compare = base_llm.with_structured_output(ComparisonRequest)
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract the two cars the user wants to compare. Correct obvious typos. Extract as much info as possible (brand, model, trim, year, condition) and leave missing fields as null. Condition is optional and should only be set if the user explicitly mentions a condition (like new/used). If a user specifies a trim (like 'M Sport', 'Advantage', 'Luxury'), place it in the trim field."),
        ("user", "{input}")
    ])
    
    extraction_chain = extract_prompt | structured_llm_compare
    parsed_req = extraction_chain.invoke({"input": user_input})
    
    car1_db = compare_search_db(parsed_req.car1)
    car2_db = compare_search_db(parsed_req.car2)
    
    if not car1_db and not car2_db:
        return "⚠️ I couldn't find either of those cars in the database. Please try another query with different models or years.", []
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert, objective car comparison assistant. The user wants to compare two cars. "
         "CRITICAL INSTRUCTIONS:\n"
         "1. All prices provided in the data are in EGP (Egyptian Pounds).\n"
         "2. All mileage values provided in the data are in kilometers (km).\n"
         "3. Do NOT infer or assume missing specs. If a field is missing for one or both cars, explicitly say it is unavailable in the listings data.\n"
         "4. ALWAYS provide a final recommendation on which car is better for the user's request.\n"
         "5. If key data is missing, still give a best-judgment recommendation and clearly state confidence as High/Medium/Low.\n\n"
         "Note that the data provided represents the *average* specs across multiple listings. "
         "Provide a simple, easy-to-understand explanation of the differences. "
         "Keep it concise, structured, and helpful. Format your response as a Markdown comparison table contrasting both cars.\n"
         "The table should feature exactly these columns: Feature | Car 1 | Car 2 | Verdict.\n"
         "The 'Verdict' column should state which car wins for that specific feature.\n"
         "After the table, provide a 'Final Verdict' section as a short summary paragraph naming the recommended car and briefly explaining why."),
        ("user", 
         "User Query: {query}\n\n"
         "Car 1 Averaged Specs from DB:\n{car1_specs}\n\n"
         "Car 2 Averaged Specs from DB:\n{car2_specs}\n\n"
         "Please compare these two cars directly, highlighting main differences.")
    ])
    
    chain = prompt | base_llm
    response = chain.invoke({
        "query": user_input,
        "car1_specs": car1_db if car1_db else "Car 1 not found in database.",
        "car2_specs": car2_db if car2_db else "Car 2 not found in database."
    })
    
    return response.content, []

def do_recommend(user_input):
    structured_llm_recommend = base_llm.with_structured_output(CarPreferences)
    
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a strict data extractor. Extract the user's car preferences into the structured format.\n\n"
         "CRITICAL RULES:\n"
         "1. If a detail is NOT explicitly mentioned, you MUST leave it NULL. Do NOT guess.\n"
         "2. Convert all budget numbers into integers.\n"
         "3. Infer 'min_seats' if they mention family size.\n"
         "4. Extract words like 'SUV', 'Sedan', 'Hatchback', or 'Van' into the body_type field."),
        ("user", "{input}")
    ])
    
    extraction_chain = extract_prompt | structured_llm_recommend
    prefs = extraction_chain.invoke({"input": user_input})
    matching_cars = query_recommendations(prefs, user_input)

    llm_visible_cars = [
        { k: v for k, v in car.items() if k not in {"car_id", "image_paths"} }
        for car in matching_cars
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an elite car matchmaker. The user has given you a prompt detailing what kind of car they want. "
         "Write a friendly, personalized recommendation response highlighting WHY each car fits their request based on the data provided. "
         "ONLY recommend the cars explicitly listed in the 'Matching Cars' data. "
         "If the user asked for New/Used or a body type, only describe matches that satisfy that request. "
         "Do NOT invent or convert units (for example, do not call values MPG unless MPG is explicitly provided). "
         "CRITICAL INSTRUCTION: NEVER mention 'car_id' or any internal database keys in your response. "
         "End your response immediately after the recommendations."),
        ("user", 
         "User's Request: {query}\n\n"
         "Matching Cars from Database:\n{cars}\n\n"
         "Please recommend these cars to the user without asking any questions.")
    ])
    
    chain = prompt | base_llm
    response = chain.invoke({
        "query": user_input,
        "cars": llm_visible_cars if llm_visible_cars else "None found in database. Do not recommend any cars."
    })
    
    return response.content, matching_cars

def do_search(user_input):
    intent = get_intent(user_input)
    filters = get_filters(user_input)

    if 'car condition' not in filters:
        if intent == 'new':
            filters['car condition'] = 'New'
        elif intent == 'used':
            filters['car condition'] = 'Used'

    if not filters:
        return "I couldn't identify specific filters in your query. Could you try rephrasing? For example, 'Show me used BMW SUVs under 2 million EGP'.", []

    results = apply_filters(filters)

    if results.empty:
        return "I couldn't find any cars matching your exact criteria. Try broadening your search terms or budget.", []

    results = rank_results_by_similarity(results, user_input)
    if 'Car ID' in results.columns:
        results = results.drop_duplicates(subset=['Car ID'])
    else:
        subset_cols = [c for c in results.columns if c != 'similarity_score']
        results = results.drop_duplicates(subset=subset_cols)

    results = results.replace({np.nan: None})
    cars_list = results.head(100).to_dict(orient='records')
    
    return f"Here are the top cars that match your search:", cars_list

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('query', '').strip()
    
    if not user_input:
        return jsonify({"text": "Please provide a query.", "cars": []}), 400

    lower_input = user_input.lower()
    first_word = lower_input.split()[0] if lower_input else ""

    try:
        if first_word.startswith("compare"):
            text, cars = do_compare(user_input)
        elif first_word.startswith("recommend"):
            text, cars = do_recommend(user_input)
        else:
            text, cars = do_search(user_input)
            
        return jsonify({"text": text, "cars": cars})
        
    except Exception as e:
        logging.error(f"Error handling chat request: {e}")
        return jsonify({"text": "⚠️ Sorry, I encountered an internal error while processing your request.", "cars": []}), 500

if __name__ == "__main__":
    chatbot_port = int(os.environ["CHATBOT_PORT"])
    chatbot_host = os.environ["CHATBOT_HOST"]
    chatbot_debug = os.getenv("CHATBOT_DEBUG", "false").lower() == "true"
    
    print(f"🚀 Python AI Server running on http://{chatbot_host}:{chatbot_port}")
    app.run(host=chatbot_host, port=chatbot_port, debug=chatbot_debug)