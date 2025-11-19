from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, user, interview, payment
from app.db.mongo import connect_to_mongo, close_mongo

app = FastAPI()

origins = ["http://localhost:5173", "http://localhost:5175", "https://my-ai-interview-frontend.onrender.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo()

app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/user")
app.include_router(interview.router, prefix="/api/interview")
app.include_router(payment.router, prefix="/api/payment")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=6000, reload=True)
