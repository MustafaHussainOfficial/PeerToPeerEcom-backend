from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from starlette import status
from db import get_session
from models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from models import UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/")
async def create_user(*, db: Session = Depends(get_session), 
                      user_data: UserCreate):
        if db.exec(select(User).where(User.email == user_data.email)).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists");
        create_user_model = User(
            name=user_data.name,
            email=user_data.email,
            password=bcrypt_context.hash(user_data.password),
            profile_photo_url=user_data.profile_photo_url
        ) 
        db.add(create_user_model)
        db.commit()
       
@router.post("/token")
async def login_for_access_token(*, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
                                db: Session = Depends(get_session)):
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect username or password",)
        
        user.loged_in = True
        db.add(user)
        db.commit()

        token = create_access_token(user.email, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        
        return {"access_token": token, "token_type": "bearer"}


def authenticate_user(username: str, password: str, db):
    user = db.exec(select(User).filter(User.email == username)).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user


def create_access_token(email: str, user_id: int, expires_delta: timedelta):
    encode = {
        "sub": email,
        "id": user_id,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_bearer),
    session: Session = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")


                            