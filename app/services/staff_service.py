from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from sqlalchemy.orm import Session

from app.models import Staff, UserRole
from app.repositories import (
    StaffRepository,
    UserRepository,
)
from app.utils.security import hash_password

from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class StaffService:
    """
    Business service responsible for staff management.
    """

    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.repository = StaffRepository(session)
        self.user_repository = UserRepository(session)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_id(
        value: int,
        name: str,
    ) -> None:

        if isinstance(value, bool):
            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if not isinstance(value, int):
            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if value <= 0:
            raise ValidationError(
                f"{name} must be a positive integer."
            )

    @staticmethod
    def _normalize_text(
        value: str,
        name: str,
        max_length: int = 100,
    ) -> str:

        if not isinstance(value, str):
            raise ValidationError(f"{name} must be text.")

        value = value.strip()

        if not value:
            raise ValidationError(f"{name} is required.")

        if len(value) > max_length:
            raise ValidationError(
                f"{name} must not exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _normalize_employee_id(value: str) -> str:

        if not isinstance(value, str):
            raise ValidationError("Employee ID must be text.")

        value = value.strip().upper()

        if not value:
            raise ValidationError("Employee ID is required.")

        if len(value) > 50:
            raise ValidationError(
                "Employee ID must not exceed 50 characters."
            )

        return value

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all_staff(self) -> list[Staff]:
        try:
            return self.repository.get_all()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve staff."
            ) from exc

    def get_staff_by_id(self, staff_id: int) -> Staff:

        self._validate_id(staff_id, "Staff ID")

        try:
            staff = self.repository.get_by_id(staff_id)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve staff."
            ) from exc

        if staff is None:
            raise ResourceNotFoundError("Staff member was not found.")

        return staff

    def search_staff(self, search_text: str) -> list[Staff]:

        if not isinstance(search_text, str):
            raise ValidationError("Search text must be text.")

        try:
            return self.repository.search(search_text)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to search staff."
            ) from exc

    def is_checkin_officer(self, user_id: int) -> bool:
        """
        Return True if the given user is a check-in officer.
        """

        from app.models import Staff

        staff = (
            self.session.query(Staff)
            .filter(Staff.user_id == user_id)
            .first()
        )

        if staff is None:
            return False

        return staff.position.strip().lower() == "check-in officer"

    def count_staff(self) -> int:
        try:
            return self.repository.count()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to count staff."
            ) from exc

    # ------------------------------------------------------------------
    # Create (User + Staff in one transaction)
    # ------------------------------------------------------------------

    def create_staff_with_user(
        self,
        *,
        email: str,
        password: str,
        employee_id: str,
        first_name: str,
        last_name: str,
        phone: str,
        position: str,
    ) -> Staff:

        # --- email ---
        if not isinstance(email, str):
            raise ValidationError("Email must be text.")

        normalized_email = email.strip().lower()

        if not normalized_email:
            raise ValidationError("Email is required.")

        if "@" not in normalized_email:
            raise ValidationError("Email is not valid.")

        # --- password ---
        if not isinstance(password, str):
            raise ValidationError("Password must be text.")

        if len(password) < 6:
            raise ValidationError(
                "Password must be at least 6 characters."
            )

        # --- other fields ---
        employee_id = self._normalize_employee_id(employee_id)
        first_name = self._normalize_text(first_name, "First name")
        last_name = self._normalize_text(last_name, "Last name")
        phone = self._normalize_text(phone, "Phone", max_length=30)
        position = self._normalize_text(position, "Position")

        try:
            # Email uniqueness
            existing_user = self.user_repository.get_by_email(
                normalized_email
            )

            if existing_user is not None:
                raise ResourceConflictError(
                    "A user with this email already exists."
                )

            # Employee ID uniqueness
            existing_staff = self.repository.get_by_employee_id(
                employee_id
            )

            if existing_staff is not None:
                raise ResourceConflictError(
                    "A staff member with this employee ID already exists."
                )

            user = self.user_repository.create(
                email=normalized_email,
                password_hash=hash_password(password),
                role=UserRole.STAFF,
                is_active=True,
            )

            staff = self.repository.create(
                user_id=user.id,
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                position=position,
            )

            self.session.commit()

            return staff

        except (ValidationError, ResourceConflictError):
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "Staff member already exists."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to create staff member."
            ) from exc

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_staff(
        self,
        staff_id: int,
        *,
        first_name: str,
        last_name: str,
        phone: str,
        position: str,
    ) -> Staff:

        self._validate_id(staff_id, "Staff ID")

        first_name = self._normalize_text(first_name, "First name")
        last_name = self._normalize_text(last_name, "Last name")
        phone = self._normalize_text(phone, "Phone", max_length=30)
        position = self._normalize_text(position, "Position")

        try:
            staff = self.repository.get_by_id(staff_id)

            if staff is None:
                raise ResourceNotFoundError(
                    "Staff member was not found."
                )

            staff = self.repository.update(
                staff,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                position=position,
            )

            self.session.commit()

            return staff

        except (ValidationError, ResourceNotFoundError):
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "The staff member could not be updated."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to update staff member."
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_staff(self, staff_id: int) -> None:

        self._validate_id(staff_id, "Staff ID")

        try:
            staff = self.repository.get_by_id(staff_id)

            if staff is None:
                raise ResourceNotFoundError(
                    "Staff member was not found."
                )

            self.repository.delete(staff)
            self.session.commit()

        except ResourceNotFoundError:
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "This staff member cannot be deleted because they "
                "have flight assignments or check-ins."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to delete staff member."
            ) from exc
