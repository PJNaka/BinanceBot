# backend/api/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer # OAuth2PasswordBearer for get_current_user
from sqlalchemy.orm import Session
from datetime import timedelta

# Relative imports assuming 'api' is a package within 'backend'
from .. import crud_user, schemas, auth_utils, hashing, models 
from ..db_setup import get_db
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, JWT_ALGORITHM # For token expiry & decoding

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# This defines how to get the token from the request (e.g. "Authorization: Bearer <token>")
# The tokenUrl should point to your login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = crud_user.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    db_user_by_username = crud_user.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        
    created_user = crud_user.create_user(db=db, user=user)
    return created_user

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not hashing.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for 401
        )
    if not user.is_active:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Data to encode in JWT: "sub" (subject) is standard for username/user_id
    access_token = auth_utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth_utils.decode_access_token(token) # Uses SECRET_KEY and ALGORITHM from auth_utils
    if payload is None: # Token decoding failed (expired, invalid, etc.)
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None: # Subject claim not found in token
        raise credentials_exception
    
    # Optional: Store username in TokenData schema for validation, though not strictly needed here
    # token_data = schemas.TokenData(username=username) 
    
    user = crud_user.get_user_by_username(db, username=username)
    if user is None: # User not found in DB
        raise credentials_exception
    if not user.is_active: # Check if user is currently active
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

# Dependency for getting the current active user (often used directly in path operations)
# get_current_user already checks for is_active, so this is a convenience wrapper
# if you want to be explicit in your endpoint dependencies about requiring an *active* user.
async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    # The active check is already performed in get_current_user.
    # This function mainly serves as a clear dependency name.
    # If additional "active" logic was needed beyond user.is_active, it would go here.
    return current_user


# Example Protected Route (for testing get_current_user dependency)
@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    # By depending on get_current_active_user, we ensure the user is active.
    # If we only depended on get_current_user, the active check is still done there.
    return current_user
