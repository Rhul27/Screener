from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import routes



# Define app for Different Routers that we will be creating
app = FastAPI()
app.include_router(routes.router)


# Define Origins from which our APIs will be accessed
origins = [
    "https://localhost.com:8000",
    "https://127.0.0.1:8000"
]

# Set Middleware to omit CORS Error for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Running the app with HTTPS support via Uivcorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)