import re
from typing import Dict, Any, List
from core.feature_flags import FeatureFlags

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", 
    "at", "by", "for", "with", "about", "against", "between", "into", "through", 
    "during", "before", "after", "above", "below", "to", "from", "up", "down", 
    "in", "out", "on", "off", "over", "under", "again", "further", "then", 
    "once", "here", "there", "when", "where", "why", "how", "all", "any", 
    "both", "each", "few", "more", "most", "other", "some", "such", "no", 
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", 
    "t", "can", "will", "just", "don", "should", "now", "let", "lets", "want", "like"
}

class AttentionEngine:
    """
    Attention Engine.
    Filters raw queries and determines focal points to limit memory retrieval noise.
    """
    
    @classmethod
    def determine_attention(cls, message: str, chat_context: str = "") -> Dict[str, Any]:
        """
        Parses raw text and conversation history to compute the primary focus domain,
        attentional keywords, and recommended memory retrieval limits.
        """
        raw_text = message.lower().strip()
        
        # 1. Check feature flag override
        if not FeatureFlags.is_enabled("attention_engine"):
            # If disabled, attention is generic and maps full message with default limits
            return {
                "primary_focus": "companionship",
                "focus_keywords": [message],
                "memory_limit": 5,
                "attention_level": 0.5
            }
            
        # 2. Match focus categories
        primary_focus = "companionship"
        attention_level = 0.5
        
        # Learning focus
        if any(w in raw_text for w in ["learn", "study", "exam", "quiz", "concept", "viva", "database", "python"]):
            primary_focus = "learning"
            attention_level = 0.8
        # Career focus
        elif any(w in raw_text for w in ["resume", "job", "career", "interview", "ats", "internship", "hired"]):
            primary_focus = "career"
            attention_level = 0.8
        # Emotional focus
        elif any(w in raw_text for w in ["sad", "tired", "frustrated", "happy", "angry", "feeling", "stuck", "bored"]):
            primary_focus = "emotion"
            attention_level = 0.9
            
        # 3. Keyword extraction (strip out stopwords and punctuation)
        words = re.findall(r'\b\w+\b', raw_text)
        keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        
        # Fallback to raw text if no keywords extracted
        if not keywords:
            keywords = [message]
            
        # 4. Limit retrieved memories based on attention score
        # Higher emotional or structured focus limits retrieval to prevent dilution
        if primary_focus in ["learning", "career"]:
            memory_limit = 2 # Keep it very specific
        elif primary_focus == "emotion":
            memory_limit = 1 # Only retrieve core comfort/preferences
        else:
            memory_limit = 3 # Standard companionship conversation limit
            
        return {
            "primary_focus": primary_focus,
            "focus_keywords": keywords[:3], # Target top 3 key terms
            "memory_limit": memory_limit,
            "attention_level": attention_level
        }

    @classmethod
    def optimize_token_budget(cls, context_chunks: List[str], max_tokens: int = 1500) -> List[str]:
        """
        Ranks and trims context chunks to ensure the total token budget is not exceeded.
        Uses a simple word-count estimation (1 word ~= 1.3 tokens).
        """
        if not context_chunks:
            return []
            
        ranked_chunks = []
        for chunk in context_chunks:
            word_count = len(chunk.split())
            token_estimate = int(word_count * 1.3)
            ranked_chunks.append((token_estimate, chunk))

        accumulated_tokens = 0
        accepted_chunks = []
        for token_est, chunk in ranked_chunks:
            if accumulated_tokens + token_est <= max_tokens:
                accepted_chunks.append(chunk)
                accumulated_tokens += token_est
            else:
                # If first chunk itself exceeds, truncate it to fit
                if not accepted_chunks and token_est > max_tokens:
                    words = chunk.split()
                    allowed_words = int(max_tokens / 1.3)
                    truncated_chunk = " ".join(words[:allowed_words]) + "..."
                    accepted_chunks.append(truncated_chunk)
                break
                
        return accepted_chunks
