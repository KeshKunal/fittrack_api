from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from pydantic import BaseModel

# User Model: Stores user credentials
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    
    # Establish the one-to-many relationship to WorkoutSession
    workout_sessions: List["WorkoutSession"] = Relationship(back_populates="user")

# Exercise Model: A library of available exercises
class Exercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str
    muscle_group: str = Field(index=True)

# WorkoutSet Model: A single set of an exercise within a session
class WorkoutSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reps: int
    weight: float 
    
    # Foreign keys to link to the session and exercise
    session_id: int = Field(foreign_key="workoutsession.id")
    exercise_id: int = Field(foreign_key="exercise.id")
    session: "WorkoutSession" = Relationship(back_populates="sets")
    exercise: "Exercise" = Relationship()

# WorkoutSession Model: Represents a single workout session for a user
class WorkoutSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)
    
    # Foreign key to link to the user
    user_id: int | None = Field(default=None, foreign_key="user.id")
    
    # Establish relationships
    user: "User" = Relationship(back_populates="workout_sessions")
    
    sets: List["WorkoutSet"] = Relationship(back_populates="session")

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None