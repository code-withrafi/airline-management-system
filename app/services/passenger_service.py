from datetime import date

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from sqlalchemy.orm import Session

from app.models import Passenger, UserRole
from app.repositories import (
    PassengerRepository,
    UserRepository,
)
from app.utils.security import hash_password

from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class PassengerService:
    """
    Business service responsible for passenger management.
    """

    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.repository = (
            PassengerRepository(
                session
            )
        )

        self.user_repository = (
            UserRepository(
                session
            )
        )

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
    def _normalize_name(
        value: str,
        field_name: str,
    ) -> str:

        if not isinstance(value, str):

            raise ValidationError(
                f"{field_name} must be text."
            )

        value = value.strip()

        if not value:

            raise ValidationError(
                f"{field_name} is required."
            )

        if len(value) > 100:

            raise ValidationError(
                f"{field_name} must not exceed 100 characters."
            )

        return value

    @staticmethod
    def _normalize_phone(
        phone: str,
    ) -> str:

        if not isinstance(phone, str):

            raise ValidationError(
                "Phone number must be text."
            )

        value = phone.strip()

        if not value:

            raise ValidationError(
                "Phone number is required."
            )

        if len(value) > 30:

            raise ValidationError(
                "Phone number must not exceed 30 characters."
            )

        return value

    @staticmethod
    def _normalize_passport(
        passport_number: str,
    ) -> str:

        if not isinstance(
            passport_number,
            str
        ):

            raise ValidationError(
                "Passport number must be text."
            )

        value = (
            passport_number
            .strip()
            .upper()
        )

        if not value:

            raise ValidationError(
                "Passport number is required."
            )

        if len(value) > 50:

            raise ValidationError(
                "Passport number must not exceed 50 characters."
            )

        return value

    @staticmethod
    def _validate_birth_date(
        value,
    ) -> date:

        if not isinstance(
            value,
            date
        ):

            raise ValidationError(
                "Date of birth must be a valid date."
            )

        if value >= date.today():

            raise ValidationError(
                "Date of birth must be in the past."
            )

        return value

    @staticmethod
    def _normalize_address(
        address,
    ) -> str | None:

        if address is None:

            return None

        if not isinstance(address, str):

            raise ValidationError(
                "Address must be text."
            )

        value = address.strip()

        if not value:

            return None

        if len(value) > 500:

            raise ValidationError(
                "Address must not exceed 500 characters."
            )

        return value

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all_passengers(
        self,
    ) -> list[Passenger]:

        try:

            return self.repository.get_all()

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve passengers."
            ) from exc

    def get_passenger_by_id(
        self,
        passenger_id: int,
    ) -> Passenger:

        self._validate_id(
            passenger_id,
            "Passenger ID"
        )

        try:

            passenger = (
                self.repository
                .get_by_id(
                    passenger_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve passenger."
            ) from exc

        if passenger is None:

            raise ResourceNotFoundError(
                "Passenger was not found."
            )

        return passenger

    def get_passenger_by_user_id(
        self,
        user_id: int,
    ) -> Passenger:

        self._validate_id(
            user_id,
            "User ID"
        )

        try:

            passenger = (
                self.repository
                .get_by_user_id(
                    user_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve passenger."
            ) from exc

        if passenger is None:

            raise ResourceNotFoundError(
                "Passenger profile was not found."
            )

        return passenger

    def search_passengers(
        self,
        search_text: str,
    ) -> list[Passenger]:

        if not isinstance(
            search_text,
            str
        ):

            raise ValidationError(
                "Search text must be text."
            )

        try:

            return self.repository.search(
                search_text
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to search passengers."
            ) from exc

    def count_passengers(
        self,
    ) -> int:

        try:

            return self.repository.count()

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to count passengers."
            ) from exc

    # ------------------------------------------------------------------
    # Create (existing User)
    # ------------------------------------------------------------------

    def create_passenger(
        self,
        *,
        user_id: int,
        first_name: str,
        last_name: str,
        phone: str,
        date_of_birth,
        passport_number: str,
        address: str | None = None,
    ) -> Passenger:

        self._validate_id(
            user_id,
            "User ID"
        )

        first_name = self._normalize_name(
            first_name,
            "First name"
        )

        last_name = self._normalize_name(
            last_name,
            "Last name"
        )

        phone = self._normalize_phone(
            phone
        )

        date_of_birth = (
            self._validate_birth_date(
                date_of_birth
            )
        )

        passport_number = (
            self._normalize_passport(
                passport_number
            )
        )

        address = self._normalize_address(
            address
        )

        try:

            existing = (
                self.repository
                .get_by_passport_number(
                    passport_number
                )
            )

            if existing is not None:

                raise ResourceConflictError(
                    "A passenger with this passport number already exists."
                )

            passenger = (
                self.repository.create(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    date_of_birth=date_of_birth,
                    passport_number=passport_number,
                    address=address,
                )
            )

            self.session.commit()

            return passenger

        except ResourceConflictError:

            self.session.rollback()

            raise

        except IntegrityError as exc:

            self.session.rollback()

            raise ResourceConflictError(
                "Passenger already exists."
            ) from exc

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to create passenger."
            ) from exc

    # ------------------------------------------------------------------
    # Create (User + Passenger in one transaction)
    # ------------------------------------------------------------------

    def create_passenger_with_user(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str,
        date_of_birth,
        passport_number: str,
        address: str | None = None,
    ) -> Passenger:
        """
        Create a User account (role=PASSENGER) and a Passenger
        profile in one transaction.
        """

        # ---- validate email ----
        if not isinstance(email, str):

            raise ValidationError(
                "Email must be text."
            )

        normalized_email = email.strip().lower()

        if not normalized_email:

            raise ValidationError(
                "Email is required."
            )

        if "@" not in normalized_email:

            raise ValidationError(
                "Email is not valid."
            )

        # ---- validate password ----
        if not isinstance(password, str):

            raise ValidationError(
                "Password must be text."
            )

        if len(password) < 6:

            raise ValidationError(
                "Password must be at least 6 characters."
            )

        # ---- validate passenger fields ----
        first_name = self._normalize_name(
            first_name,
            "First name"
        )

        last_name = self._normalize_name(
            last_name,
            "Last name"
        )

        phone = self._normalize_phone(
            phone
        )

        date_of_birth = (
            self._validate_birth_date(
                date_of_birth
            )
        )

        passport_number = (
            self._normalize_passport(
                passport_number
            )
        )

        address = self._normalize_address(
            address
        )

        try:

            # Email must be unused
            existing_user = (
                self.user_repository
                .get_by_email(
                    normalized_email
                )
            )

            if existing_user is not None:

                raise ResourceConflictError(
                    "A user with this email already exists."
                )

            # Passport must be unused
            existing_passenger = (
                self.repository
                .get_by_passport_number(
                    passport_number
                )
            )

            if existing_passenger is not None:

                raise ResourceConflictError(
                    "A passenger with this passport number already exists."
                )

            # Create the User
            user = self.user_repository.create(
                email=normalized_email,
                password_hash=hash_password(password),
                role=UserRole.PASSENGER,
                is_active=True,
            )

            # Create the Passenger linked to the User
            passenger = self.repository.create(
                user_id=user.id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                date_of_birth=date_of_birth,
                passport_number=passport_number,
                address=address,
            )

            self.session.commit()

            return passenger

        except (
            ValidationError,
            ResourceConflictError,
        ):

            self.session.rollback()

            raise

        except IntegrityError as exc:

            self.session.rollback()

            raise ResourceConflictError(
                "Passenger account already exists."
            ) from exc

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to create passenger."
            ) from exc

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_passenger(
        self,
        passenger_id: int,
        *,
        first_name: str,
        last_name: str,
        phone: str,
        date_of_birth,
        passport_number: str,
        address: str | None = None,
    ) -> Passenger:

        self._validate_id(
            passenger_id,
            "Passenger ID"
        )

        first_name = self._normalize_name(
            first_name,
            "First name"
        )

        last_name = self._normalize_name(
            last_name,
            "Last name"
        )

        phone = self._normalize_phone(
            phone
        )

        date_of_birth = (
            self._validate_birth_date(
                date_of_birth
            )
        )

        passport_number = (
            self._normalize_passport(
                passport_number
            )
        )

        address = self._normalize_address(
            address
        )

        try:

            passenger = (
                self.repository
                .get_by_id(
                    passenger_id
                )
            )

            if passenger is None:

                raise ResourceNotFoundError(
                    "Passenger was not found."
                )

            existing = (
                self.repository
                .get_by_passport_number(
                    passport_number
                )
            )

            if (
                existing is not None
                and existing.id != passenger.id
            ):

                raise ResourceConflictError(
                    "A passenger with this passport number already exists."
                )

            passenger = (
                self.repository.update(
                    passenger,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    date_of_birth=date_of_birth,
                    passport_number=passport_number,
                    address=address,
                )
            )

            self.session.commit()

            return passenger

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            self.session.rollback()

            raise

        except IntegrityError as exc:

            self.session.rollback()

            raise ResourceConflictError(
                "The passenger could not be updated because of a database conflict."
            ) from exc

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to update passenger."
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_passenger(
        self,
        passenger_id: int,
    ) -> None:

        self._validate_id(
            passenger_id,
            "Passenger ID"
        )

        try:

            passenger = (
                self.repository
                .get_by_id(
                    passenger_id
                )
            )

            if passenger is None:

                raise ResourceNotFoundError(
                    "Passenger was not found."
                )

            self.repository.delete(
                passenger
            )

            self.session.commit()

        except ResourceNotFoundError:

            self.session.rollback()

            raise

        except IntegrityError as exc:

            self.session.rollback()

            raise ResourceConflictError(
                "This passenger cannot be deleted because they have existing bookings."
            ) from exc

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to delete passenger."
            ) from exc

    def change_password(
        self,
        user_id: int,
        *,
        old_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password after verifying the old one.
        """

        self._validate_id(
            user_id,
            "User ID"
        )

        if not isinstance(old_password, str):

            raise ValidationError(
                "Old password must be text."
            )

        if not isinstance(new_password, str):

            raise ValidationError(
                "New password must be text."
            )

        if len(new_password) < 6:

            raise ValidationError(
                "New password must be at least 6 characters."
            )

        try:

            user = (
                self.user_repository
                .get_by_id(
                    user_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve user."
            ) from exc

        if user is None:

            raise ResourceNotFoundError(
                "User was not found."
            )

        from app.utils.security import (
            hash_password,
            verify_password,
        )

        if not verify_password(
            old_password,
            user.password_hash,
        ):

            raise ValidationError(
                "Old password is incorrect."
            )

        try:

            user.password_hash = (
                hash_password(
                    new_password
                )
            )

            self.session.commit()

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to change password."
            ) from exc
