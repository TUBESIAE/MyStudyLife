from typing import List
from pydantic import BaseModel

class User(BaseModel):
    username: str
    hashed_password: str

users_db: List[User] = []
