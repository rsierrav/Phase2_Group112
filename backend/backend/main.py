from fastapi import Depends, FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}