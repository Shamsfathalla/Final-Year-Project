import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_results_by_similarity(df: pd.DataFrame, raw_query: str) -> pd.DataFrame:
    """
    Ranks a DataFrame of hard SQL matches based on their textual similarity 
    to the user's raw query using TF-IDF and Cosine Similarity.
    """
    if df.empty or len(df) <= 1:
        return df

    # 1. Define columns to build the car's "content profile"
    # We include both text features and stringified numbers (like year)
    profile_columns = [
        'brand', 'model', 'trim', 'year', 'color', 'body type', 
        'transmission', 'drivetrain', 'condition', 'car condition',
        'engine', 'fuel type'
    ]
    
    # Ensure we only use columns that actually exist in the DataFrame
    available_cols = [c for c in profile_columns if c in df.columns]

    # 2. Synthesize a text profile for each row
    def build_profile(row):
        # Join available attributes into a single space-separated string
        parts = [str(row[c]) for c in available_cols if pd.notna(row[c])]
        return " ".join(parts).lower()

    df['synthesized_profile'] = df.apply(build_profile, axis=1)

    # 3. Vectorize the text profiles AND the user's raw query
    # We fit them together so the TF-IDF vocabulary knows all terms
    vectorizer = TfidfVectorizer(stop_words='english')
    all_texts = df['synthesized_profile'].tolist() + [raw_query.lower()]
    
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # 4. Separate the query vector from the car vectors
    query_vector = tfidf_matrix[-1]  # The raw query is the last item
    car_vectors = tfidf_matrix[:-1]  # Everything else is the cars

    # 5. Calculate Cosine Similarity
    # Flatten the array to get a 1D list of scores corresponding to the rows
    similarity_scores = cosine_similarity(query_vector, car_vectors).flatten()

    # 6. Assign scores, sort, and clean up
    df['similarity_score'] = similarity_scores
    df = df.sort_values(by=['similarity_score', 'price'], ascending=[False, True])
    
    # Drop the temporary profile column (keep the score if you want to display it)
    df = df.drop(columns=['synthesized_profile'])

    return df