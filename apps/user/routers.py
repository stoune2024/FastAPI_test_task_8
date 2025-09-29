from fastapi import APIRouter, FastAPI, Request, HTTPException, status
import jwt
from settings.settings import settings
from apps.user.services import get_connection
from jwt.exceptions import InvalidTokenError

user_router = APIRouter(tags=["Приложение для взаимодействия с пользователем"])


middleware_protected_app = FastAPI(title="Подприложение для конечных точек с защитой на основе middleware")


@middleware_protected_app.middleware("http")
async def check_if_user_authorized(
        request: Request,
        call_next
):
    try:
        token = request.cookies.get("access-token")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен доступа не действителен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if username is not None:
        response = await call_next(request)
        return response
