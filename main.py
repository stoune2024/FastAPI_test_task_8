from fastapi import FastAPI
from uvicorn import run

from apps.user.controllers import user_router
from apps.auth.controllers import auth_router


app = FastAPI()

app.include_router(user_router, prefix="/user")
app.include_router(auth_router, prefix="/auth")


if __name__ == "__main__":
    run(
        app="main:app",
        reload=True,
        log_level="debug",
        host="localhost",
        port=8000,
    )
