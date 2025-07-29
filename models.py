from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from typing import List, Optional, Set, Dict, Any, Tuple, Union, Callable
from datetime import datetime
from contextlib import asynccontextmanager


class UserBase(SQLModel):
    
    name: str
    email: str
    password: str
    profile_photo_url: Optional[str] = None
    

class UserCreate(UserBase):
    pass

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    items_offered: List["Item"] = Relationship(back_populates="seller")
    purchases: List["Transaction"] = Relationship(back_populates="buyer")
    loged_in: Optional[bool] = False

    
class UserRead(SQLModel):
    id: Optional[int]
    username: str
    email: str
    created_at: Optional[str] = None

class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    item_id: int = Field(foreign_key="item.id")
    
    item: Optional["Item"] = Relationship(back_populates="images")

class ItemBase(SQLModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    seller_id: int = Field(foreign_key="user.id")
    thumbnail_url: Optional[str] = None
    

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    seller: User = Relationship(back_populates="items_offered")
    transactions: List["Transaction"] = Relationship(back_populates="item")
    images: List[Image] = Relationship(back_populates="item")

class ItemCreate(ItemBase):
    pass


class TransactionBase(SQLModel):
    buyer_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: int
    total_price: float



class TransactionRead(TransactionBase):
    id: int
    transaction_date: datetime


class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_date: datetime = Field(default_factory=datetime.utcnow)

    buyer: Optional["User"] = Relationship(back_populates="purchases")
    item: Optional["Item"] = Relationship(back_populates="transactions")

class TransactionCreate(TransactionBase):
    pass

