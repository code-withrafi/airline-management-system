from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """
    Handles database operations related to users.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        role,
        is_active: bool = True,
    ) -> User:
        """Create a new user. Caller commits."""

        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )

        self.session.add(user)
        self.session.flush()

        return user

    def get_by_email(self, email: str) -> User | None:
        """
        Find a user by email address.
        """

        statement = (
            select(User)
            .where(User.email == email.lower().strip())
        )

        return self.session.scalar(statement)

    def get_by_id(self, user_id: int) -> User | None:
        """
        Find a user by primary key.
        """

        statement = (
            select(User)
            .where(User.id == user_id)
        )

        return self.session.scalar(statement)