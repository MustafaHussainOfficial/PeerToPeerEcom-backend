from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Set, Dict, Any, Tuple, Union, Callable
from datetime import datetime
from sqlmodel import Session, select
from db import init_db, get_session
from models import User, Item, Transaction, Image, UserCreate, ItemCreate, TransactionCreate, TransactionRead, UserRead
from contextlib import asynccontextmanager
from sqlalchemy import or_, func
import auth
from auth import get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)

@app.get("/")
def main():
    return { "message": "Hello World" }


    
@app.post("/item-create", response_model=Item)
async def create_item(item_data: ItemCreate,
                        current_user: User = Depends(get_current_user),
                        session: Session = Depends(get_session)) -> Item:
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.loged_in:
        raise HTTPException(status_code=401, detail="User is not logged in.")
    
    # Create item with the current user's ID as seller_id
    item = Item(
        **item_data.dict(),
        seller_id=current_user.id
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
    

@app.post("/transaction-create", response_model=Transaction)
async def create_transaction(transaction_data: TransactionCreate, 
                                session: Session = Depends(get_session)) -> Transaction:
    
    transaction = Transaction(**transaction_data.dict())
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction
    
    

@app.post("/user-logout", response_model=User)
async def logout(
    current_user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
):
    current_user.logged_in = False
    session.add(current_user)
    session.commit()
    return {"detail": f"User {current_user.email} logged out successfully"}     

@app.delete("/remove-item", response_model=Item)
async def remove_item(*,current_user: User = Depends(get_current_user),
                      item_id: int,
                      session: Session = Depends(get_session)) -> Item:
    item = session.exec(select(Item).where(Item.id == item_id)).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Not authorized")
    if not current_user.loged_in:
        raise HTTPException(status_code=401, detail="User is not logged in.")
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this item")
    session.delete(item)
    session.commit()
    return item

@app.delete("/remove-user", response_model=User)
async def remove_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=404, detail="Not authorized")
    if not current_user.loged_in:
        raise HTTPException(status_code=401, detail="User is not logged in.")
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this user")
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return user

@app.get("/users", response_model=List[User])
async def get_users(session: Session = Depends(get_session)) -> List[User]:
    users = session.exec(select(User)).all()
    return users
    

@app.get("/items", response_model=List[Item])
async def get_items(
    name: Optional[str] = None,
    price_upper: Optional[float] = None,
    price_lower: Optional[float] = None,
    q: Optional[str] = None,
    session: Session = Depends(get_session)
) -> List[Item]:

    query = select(Item)
    if name:
        query = query.where(Item.name.contains(name))
    if price_upper:
        query = query.where(Item.price <= price_upper)
    if price_lower:
        query = query.where(Item.price >= price_lower)
    if q:
        query = query.where(
            or_(
                func.lower(Item.name).contains(q.lower()),
                func.lower(Item.description).contains(q.lower())
            )
        )
    items = session.exec(query).all()
    return items
    

@app.get("/transactions", response_model=List[Transaction])
async def get_transactions(session: Session = Depends(get_session)) -> List[Transaction]:
    transactions = session.exec(select(Transaction)).all()
    return transactions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)




