import hashlib
import secrets
import hmac
import base64
import json
from datetime import datetime, timedelta
from app.core.config import settings

SECRET_KEY = getattr(settings, "DEMO_KEY", "voltlife_super_secret_session_key")

def hash_password(password: str) -> str:
    """
    Hashes a password using SHA-256 and a random salt.
    Stores the salt and hash together as: salt$hash
    """
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}${pw_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a password against its salt-prefixed hash.
    """
    try:
        salt, pw_hash = hashed_password.split("$", 1)
        test_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        return secrets.compare_digest(pw_hash, test_hash)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Creates a signed HMAC-SHA256 stateless session token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire.isoformat()})
    
    payload_json = json.dumps(to_encode)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')
    
    # Sign it using HMAC
    sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8')
    
    return f"{payload_b64}.{sig_b64}"

def verify_token(token: str) -> dict:
    """
    Verifies the signature and expiration of an access token.
    """
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        
        # Verify signature
        sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8')
        
        if not secrets.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        # Decode payload
        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Check expiration
        exp_str = payload.get("exp")
        if not exp_str:
            return None
        exp = datetime.fromisoformat(exp_str)
        if datetime.utcnow() > exp:
            return None
            
        return payload
    except Exception:
        return None
