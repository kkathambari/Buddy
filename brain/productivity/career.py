import re
from typing import Dict, Any, List
from core.logging import setup_logger

logger = setup_logger("career")

class CareerCoach:
    """
    Career Coach & Resume ATS Analyzer.
    Analyzes resume relevance scores against target job specifications.
    """
    @staticmethod
    def analyze_resume_ats(resume_text: str, job_desc: str) -> Dict[str, Any]:
        """Compares resume keywords against job requirements and scores alignment."""
        resume_clean = resume_text.lower()
        jd_clean = job_desc.lower()
        
        # Hardcoded dictionary of common high-value tech stack keywords
        tech_keywords = [
            "python", "fastapi", "docker", "kubernetes", "react", 
            "javascript", "typescript", "sql", "git", "aws", "cicd", 
            "machine learning", "rest api", "testing", "asyncio"
        ]
        
        jd_requirements = []
        for kw in tech_keywords:
            if kw in jd_clean:
                jd_requirements.append(kw)
                
        if not jd_requirements:
            # Fallback to general tech keywords if JD is empty or non-specific
            jd_requirements = ["python", "git", "sql"]
            
        matched_keywords = []
        missing_keywords = []
        
        for req in jd_requirements:
            if req in resume_clean:
                matched_keywords.append(req)
            else:
                missing_keywords.append(req)
                
        score = int((len(matched_keywords) / len(jd_requirements)) * 100)
        
        improvements = []
        for kw in missing_keywords:
            improvements.append(f"Consider adding practical experience with '{kw}' to align with job requirements.")
            
        if len(resume_text.split()) < 100:
            improvements.append("Resume length is very short. Expand on project achievements and impact metrics.")
            
        logger.info(f"ATS analysis complete. Match Score: {score}%")
        return {
            "match_score": score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "improvements": improvements
        }
