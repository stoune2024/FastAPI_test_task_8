from fastapi import FastAPI
from uvicorn import run

# from apps.user.routers import user_router
from apps.user.controllers import user_router


app = FastAPI()

app.include_router(user_router)


@app.get("/")
def get_root():
    return {"message": "hello world!"}


if __name__ == "__main__":
    run(
        app="main:app",
        reload=True,
        log_level="debug",
        host="localhost",
        port=8000,
    )
