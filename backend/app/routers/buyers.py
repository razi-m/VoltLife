from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.marketplace_orm import BuyerAccount
from app.core.auth import hash_password, verify_password, create_access_token, verify_token

router = APIRouter(prefix="/api/v1/buyers", tags=["buyers"])
security = HTTPBearer(auto_error=False)

# --- Schemas ---
class BuyerRegister(BaseModel):
    company_name: str
    email: str
    phone: str
    address: str
    username: str
    password: str

class BuyerLogin(BaseModel):
    username: str
    password: str

# --- Security Dependencies ---
def get_current_buyer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> BuyerAccount:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Not authenticated"}}
        )
    token = credentials.credentials
    payload = verify_token(token)
    if not payload or payload.get("type") != "buyer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Could not validate credentials"}}
        )
    buyer_id = payload.get("user_id")
    buyer = db.query(BuyerAccount).filter(BuyerAccount.id == buyer_id).first()
    if not buyer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Buyer account not found"}}
        )
    return buyer

# --- Routes ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_buyer(data: BuyerRegister, db: Session = Depends(get_db)):
    # Check if buyer email already exists
    existing_email = db.query(BuyerAccount).filter(BuyerAccount.email == data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "email_taken", "message": "Email is already registered"}}
        )
    
    # Check if username is taken
    existing_username = db.query(BuyerAccount).filter(BuyerAccount.username == data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "username_taken", "message": "Username is already taken"}}
        )
    
    # Create BuyerAccount
    pw_hash = hash_password(data.password)
    buyer = BuyerAccount(
        company_name=data.company_name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        username=data.username,
        password_hash=pw_hash
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    
    return {
        "status": "success",
        "message": "Buyer registration successful",
        "buyer_id": buyer.id
    }

@router.post("/login")
def login_buyer(data: BuyerLogin, db: Session = Depends(get_db)):
    buyer = db.query(BuyerAccount).filter(BuyerAccount.username == data.username).first()
    if not buyer or not verify_password(data.password, buyer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Invalid username or password"}}
        )
    
    # Generate token with type constraint
    token_payload = {
        "user_id": buyer.id,
        "username": buyer.username,
        "type": "buyer"
    }
    token = create_access_token(token_payload)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "buyer": {
            "id": buyer.id,
            "company_name": buyer.company_name,
            "email": buyer.email
        }
    }

@router.get("/me")
def get_buyer_me(buyer: BuyerAccount = Depends(get_current_buyer)):
    return {
        "id": buyer.id,
        "company_name": buyer.company_name,
        "email": buyer.email,
        "phone": buyer.phone,
        "address": buyer.address,
        "username": buyer.username,
        "created_at": buyer.created_at
    }
