from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService

from app.database.models import User
from passlib.context import CryptContext

from app.utils import generate_access_token

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService(BaseService):
    def __init__(self, model: User, session: AsyncSession):
        self.model = model
        self.session = session
        
    async def _add_user(self, data: dict) -> User:
        user = self.model(
            **data, 
            password_hash=password_context.hash(data["password"]),
        )
        return await self._add(user)
    
    async def _get_by_email(self, email) -> User | None:
        return await self.session.scalar(
            select(self.model).where(self.model.email == email)
        )
        
    async def _generate_token(self, email, password) -> str:
        # Validate the credentials
        user = await self._get_by_email(email)
        

        if user is None or not password_context.verify(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or password is incorrect",
            )
        
        token = generate_access_token(data={
            "user": {
                "name": user.name,
                "id": str(user.id),
            }        })

        return token
        