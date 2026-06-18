from typing import List, Dict, Any
from shared.storage import safe_load
from memory.semantic import retrieve_memory

def retrieve_relevant_facts(query: str) -> List[str]:
    """Retrieves relevant facts from working database segments and semantic vector memories."""
    facts = []
    query_lower = query.lower()
    
    # 1. Check user profile for keywords
    try:
        from memory.user_profile import load_profile
        profile = load_profile()
        if "name" in query_lower and profile.get("name") != "Developer":
            facts.append(f"User's name is {profile['name']}.")
        if "college" in query_lower and profile.get("college") != "None":
            facts.append(f"User attends {profile['college']}.")
        if "language" in query_lower and profile.get("favorite_language") != "None":
            facts.append(f"User's favorite programming language is {profile['favorite_language']}.")
        if "goal" in query_lower and profile.get("goals"):
            facts.append(f"User's active goals: {', '.join(profile['goals'])}.")
    except Exception:
        pass
        
    # 2. Check study/learning logs
    try:
        progress = safe_load("data/learning_progress.json", {})
        for topic, val in progress.items():
            if topic.lower() in query_lower:
                facts.append(f"User has {val}% mastery in {topic}.")
    except Exception:
        pass
        
    # 3. Check career databases
    try:
        career = safe_load("data/career_progress.json", {})
        if "job" in query_lower or "career" in query_lower or "role" in query_lower:
            if career.get("target_role"):
                facts.append(f"User is targeting the role of {career['target_role']}.")
        if "ats" in query_lower and career.get("ats_score"):
            facts.append(f"User's last resume ATS match score was {career['ats_score']}%.")
    except Exception:
        pass
        
    # 4. Check semantic vector database
    try:
        semantic_memories = retrieve_memory(query, top_k=3)
        for m in semantic_memories:
            facts.append(m)
    except Exception:
        pass
        
    return list(set(facts)) # De-duplicate
