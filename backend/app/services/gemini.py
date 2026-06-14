import os
import re
import json
import httpx
from app.core.logging import logger

def parse_use_case_fallback(use_case_text: str) -> dict:
    """
    Deterministic local parser that extracts grade, capacity, and quantity from free-text.
    Useful for offline, keyless demo execution and safety fallback.
    """
    use_case_text_lower = use_case_text.lower()
    
    # 1. Parse Grade: S, A, B, C
    grade = None
    # Look for patterns like "grade A", "grade: A", "grade-A", "grade S"
    grade_match = re.search(r'\bgrade\s*[:\-]?\s*([sabc])\b', use_case_text_lower)
    if grade_match:
        grade = grade_match.group(1).upper()
    else:
        # Fallback keyword checks
        for g in ["S", "A", "B", "C"]:
            if f"grade {g.lower()}" in use_case_text_lower or f"grade-{g.lower()}" in use_case_text_lower:
                grade = g
                break
            
    # 2. Parse Capacity (kWh)
    capacity_kwh = None
    # Look for numbers preceding kwh, kw, or kilowatt
    cap_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kwh|kw|kilowatt\s*hours?)\b', use_case_text_lower)
    if cap_match:
        capacity_kwh = float(cap_match.group(1))
        
    # 3. Parse Quantity (units)
    quantity = None
    # Look for numbers preceding units, packs, batteries, qty, quantity, pcs, pieces
    qty_match = re.search(r'(\d+)\s*(?:units?|packs?|batteries|qty|quantity|pcs|pieces?)\b', use_case_text_lower)
    if qty_match:
        quantity = int(qty_match.group(1))
        
    return {
        "grade": grade,
        "capacity_kwh": capacity_kwh,
        "quantity": quantity,
        "source": "local_fallback"
    }

def parse_use_case(use_case_text: str) -> dict:
    """
    Parses a buyer's free-text requirement into structured parameters.
    Attempts to call Gemini API if key is present, otherwise falls back to local parsing.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY not set. Using local fallback parser.")
        return parse_use_case_fallback(use_case_text)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = (
        "Analyze the following user requirement for second-life batteries and extract three structured parameters in JSON format.\n"
        "Parameters to extract:\n"
        "1. \"grade\": Must be one of: \"S\", \"A\", \"B\", \"C\", or null (if not specified).\n"
        "2. \"capacity_kwh\": A floating point number representing the requested total battery capacity in kWh, or null (if not specified).\n"
        "3. \"quantity\": An integer representing the requested number of battery units/packs, or null (if not specified).\n\n"
        "Response format must be valid JSON matching this schema:\n"
        "{\n"
        "  \"grade\": string or null,\n"
        "  \"capacity_kwh\": number or null,\n"
        "  \"quantity\": integer or null\n"
        "}\n\n"
        f"User requirement: \"{use_case_text}\""
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        # 10s timeout to prevent hanging UI
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                result_json = response.json()
                # Parse text from candidate
                candidates = result_json.get("candidates", [])
                if candidates:
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if content_parts:
                        text_response = content_parts[0].get("text", "")
                        parsed_data = json.loads(text_response.strip())
                        
                        # Validate extracted values
                        grade = parsed_data.get("grade")
                        if grade:
                            grade = str(grade).upper().replace("GRADE", "").strip()
                            if grade not in ["S", "A", "B", "C"]:
                                grade = None
                                
                        capacity = parsed_data.get("capacity_kwh")
                        if capacity is not None:
                            try:
                                capacity = float(capacity)
                            except ValueError:
                                capacity = None
                                
                        quantity = parsed_data.get("quantity")
                        if quantity is not None:
                            try:
                                quantity = int(quantity)
                            except ValueError:
                                quantity = None
                                
                        return {
                            "grade": grade,
                            "capacity_kwh": capacity,
                            "quantity": quantity,
                            "source": "gemini_api"
                        }
            
            logger.warning(f"Gemini API returned status code {response.status_code}. Falling back to local parser.")
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}. Falling back to local parser.")
        
    return parse_use_case_fallback(use_case_text)
