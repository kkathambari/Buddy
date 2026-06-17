import json
import os
import math
from core.config import get_config

VECTOR_DB_PATH = "data/vector_db.json"

def get_embedding(text):
    """
    Calls the configured AI Provider to convert text into a high-dimensional mathematical vector.
    """
    config = get_config()
    provider = config.get("ai_provider", "gemini")
    
    try:
        if provider == "gemini":
            import google.generativeai as genai
            api_key = config.get("gemini_api_key", "")
            if not api_key: return None
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
            
        elif provider == "chatgpt":
            import openai
            api_key = config.get("chatgpt_api_key", "")
            if not api_key: return None
            client = openai.OpenAI(api_key=api_key)
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
            
    except Exception as e:
        print(f"Embedding failed: {e}")
        return None
        
    return None

def cosine_similarity(vec1, vec2):
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
        
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
        
    return dot_product / (magnitude1 * magnitude2)

def load_vector_db():
    if not os.path.exists(VECTOR_DB_PATH):
        return []
    try:
        with open(VECTOR_DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_vector_db(db):
    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
    with open(VECTOR_DB_PATH, "w") as f:
        json.dump(db, f, indent=4)

def store_memory(text):
    if len(text.strip()) < 5:
        return
        
    vector = get_embedding(text)
    if not vector:
        return
        
    db = load_vector_db()
    for item in db:
        if item["text"] == text:
            return
            
    db.append({
        "text": text,
        "vector": vector
    })
    save_vector_db(db)

def retrieve_memory(query, top_k=2):
    query_vector = get_embedding(query)
    if not query_vector:
        return []
        
    db = load_vector_db()
    if not db:
        return []
        
    results = []
    for item in db:
        similarity = cosine_similarity(query_vector, item["vector"])
        results.append((similarity, item["text"]))
        
    results.sort(key=lambda x: x[0], reverse=True)
    relevant_memories = [text for sim, text in results[:top_k] if sim > 0.60]
    return relevant_memories
