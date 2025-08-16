from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import date, datetime

# --- Base Models (for shared properties) ---

class ExerciseBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: str
    muscle_group: str = Field(index=True)

class WorkoutSessionBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now, index=True)

class WorkoutSetBase(SQLModel):
    reps: int
    weight: float
    exercise_id: int = Field(foreign_key="exercise.id")

# --- Database Models (with IDs and relationships) ---

class WorkoutSet(WorkoutSetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="workoutsession.id")
    
    session: "WorkoutSession" = Relationship(back_populates="sets")
    exercise: "Exercise" = Relationship()

class WorkoutSession(WorkoutSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    user: "User" = Relationship(back_populates="workout_sessions")
    sets: List["WorkoutSet"] = Relationship(back_populates="session")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    workout_sessions: List["WorkoutSession"] = Relationship(back_populates="user")

class Exercise(ExerciseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# --- API Input/Output Models ---

# NEW: Model for creating an exercise
class ExerciseCreate(ExerciseBase):
    pass

# NEW: Model for creating a workout session
class WorkoutSessionCreate(SQLModel):
    pass

# NEW: Model for creating a new set
class WorkoutSetCreate(WorkoutSetBase):
    pass

# NEW: Model for updating a set (all fields are optional)
class WorkoutSetUpdate(SQLModel):
    reps: Optional[int] = None
    weight: Optional[float] = None
    exercise_id: Optional[int] = None

class UserCreate(SQLModel):
    username: str
    password: str

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None

class ExcerciseRead(ExerciseBase):
    id: int

class WorkoutSetRead(WorkoutSetBase):
    id: int
    exercise: ExcerciseRead

class WorkoutSessionReadwithSets(WorkoutSessionBase):
    id: int
    user_id: int
    sets: List[WorkoutSetRead]=[]