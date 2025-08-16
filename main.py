from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import SQLModel, Session,  select, desc
from database import engine, get_session
from typing import Annotated, List
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import get_current_user, get_password_hash, verify_password, create_access_token
from models import (
    WorkoutSession, WorkoutSet, Exercise, User, UserCreate, Token,
    ExerciseCreate, WorkoutSessionCreate, WorkoutSetCreate, WorkoutSetUpdate, WorkoutSessionReadwithSets, PersonalRecordTrack, BodyMeasurement, BodyMeasurementCreate
)
from datetime import date, datetime

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return{ "message": "Welcome to the FitTrack API!"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl= "token")

#POST 1 --> User registration

@app.post("/users/signup", response_model= User, tags=["Users"])
def create_user(user: UserCreate, session: Annotated[Session, Depends(get_session)]):
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists!")

    hashed_password = get_password_hash(user.password)
    db_user = User(username= user.username, hashed_password = hashed_password)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user

#POST 2 --> USER Login
@app.post("/token", response_model=Token,tags=["Users"])
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)]
):

    user = session.exec(select(User). where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Incorrect username or password, Try Again!",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    
    from datetime import datetime
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

#GET 1 --> Get current users details

@app.get("/users/me", response_model=User, tags=["Users"])  
def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

#GET 2 --> Get the list of all the availabe exercise

@app.get("/exercises/", response_model=List[Exercise], tags=["Exercises"])
def read_exercises(session: Annotated[Session, Depends(get_session)]):
    exercises = session.exec(select(Exercise)).all()
    return exercises

#POST 3 --> Add new Excercise
@app.post("/exercises/", response_model=Exercise, tags=["Exercises"])
def create_exercise(exercise_date: ExerciseCreate, session: Annotated[Session, Depends(get_session)]):
    db_exercise= Exercise.model_validate(exercise_date)
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise

# POST 4 --> Create new workout session for the current user
@app.post("/workouts/sessions/", response_model=WorkoutSession, tags=["Session"])
def create_workout_session(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    new_session= WorkoutSession(user_id=current_user.id)
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    return new_session

#GET 3 --> Get all the workout session for the current user
@app.get("/workouts/sessions/", response_model=List, tags=["Session"])
def get_user_workout_session(
    current_user: Annotated[User, Depends(get_current_user)],
    session : Annotated[Session, Depends(get_session)]
):
    Sessions= session.exec(
        select(WorkoutSession).where(WorkoutSession.user_id == current_user.id)
    ).all()
    return Sessions

# GET 4 --> Get details of a specific workout session
@app.get("/workouts/sessions/{session_id}", response_model=WorkoutSessionReadwithSets, tags=["Session"])
def get_workout_session_details(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    workout_session = session.get(WorkoutSession, session_id)
    if not workout_session or workout_session.user_id!= current_user.id:
        raise HTTPException(status_code=404, detail="Workout session not found")
    return workout_session

# DELETE 2 --> Delete a specific workout Session
@app.delete("/workouts/sessions/{session_id}", tags=["Session"])
def delete_workout_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    db_session = session.get(WorkoutSession, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify
    if not db_session.user_id!= current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")

    session.delete(db_session)
    session.commit()
    return {"message": "Session deleted successfully"}

# POST 5 --> Add a set to a specific workout session  
@app.post("/workouts/sessions/{session_id}/sets", response_model=WorkoutSet, tags=["workouts"])
def add_set_to_workout(
    session_id: int,
    set_data: WorkoutSetCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    workout_session = session.get(WorkoutSession, session_id)
    if not workout_session or workout_session.user_id!= current_user.id:
        raise HTTPException(status_code=404, detail="Workout session not found")
    
    new_set = WorkoutSet.model_validate(set_data, update={"session_id": session_id})
    new_set.session_id = session_id 
    
    session.add(new_set)
    session.commit()
    session.refresh(new_set)
    return new_set

# PUT 1 --> Update a specific workout set
@app.put("/workouts/sets/{set_id}", response_model=WorkoutSet, tags=["workouts"])
def update_workout_set(
    set_id: int,
    set_update: WorkoutSetUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    db_set = session.get(WorkoutSet, set_id)
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")
    
    # Verification
    workout_session = session.get(WorkoutSession, db_set.session_id)
    if not workout_session or workout_session.user_id!= current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this set")

    set_data = set_update.model_dump(exclude_unset=True)
    for key, value in set_data.items():
        setattr(db_set, key, value)
    
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return db_set

# DELETE 1 --> Delete a specific workout set
@app.delete("/workouts/sets/{set_id}", tags=["workouts"])
def delete_workout_set(
    set_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    db_set = session.get(WorkoutSet, set_id)
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")

    # Verify
    workout_session = session.get(WorkoutSession, db_set.session_id)
    if not workout_session or workout_session.user_id!= current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this set")

    session.delete(db_set)
    session.commit()
    return {"message": "Set deleted successfully"}

# GET 5--> Personal Record Track

@app.get("/exercises/{exercise_id}/p_record", response_model=PersonalRecordTrack, tags=["Personal Records"])
def get_personal_record(
    exercise_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    
    exercise= session.get(Exercise, exercise_id )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not Found")

    pr_set=session.exec(
        select(WorkoutSet).join(WorkoutSession).where(WorkoutSession.user_id == current_user.id).where(WorkoutSet.exercise_id == exercise_id).order_by(desc(WorkoutSet.weight))
    ).first()

    if not pr_set:
        raise HTTPException(status_code=404, detail="Record not Found")
    
    workout_session = session.get(WorkoutSession, pr_set.session_id)
    if not workout_session:
        raise HTTPException(status_code=404, detail="Workout session for the record not found")

    return PersonalRecordTrack(
        exercise_name= exercise.name,
        max_weight= pr_set.weight,
        reps_at_max=pr_set.reps,
        record_at=workout_session.created_at

    )

# Body Metrics

#POST 6 --> Log a new body Measurement for current user
@app.post("/metrics/", response_model=BodyMeasurement, tags=["Body Metrics"])
def log_body_measurement(
    measurement_data: BodyMeasurementCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    
    data_dict = measurement_data.model_dump()
    if data_dict.get("created_at") is None:
        pass

    new_measurement = BodyMeasurement.model_validate(data_dict, update={"user_id": current_user.id})
    
    session.add(new_measurement)
    session.commit()
    session.refresh(new_measurement)
    return new_measurement

# GET 6 --> Get History of specific body measurement for the current user
@app.get("/metrics/{metric_type}", response_model=List[BodyMeasurement], tags=["Body Metrics"])
def get_body_measurements(
    metric_type: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    measurements = session.exec(
        select(BodyMeasurement)
        .where(BodyMeasurement.user_id == current_user.id)
        .where(BodyMeasurement.metric_type == metric_type)
        .order_by(desc(BodyMeasurement.created_at))
    ).all()
    
    return measurements