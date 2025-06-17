from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, db

models.Base.metadata.create_all(bind=db.engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "321 Vegan API is running"}
