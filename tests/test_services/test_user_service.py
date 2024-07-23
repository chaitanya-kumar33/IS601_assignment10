from builtins import range
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.dependencies import get_settings
from app.models.user_model import User
from app.schemas.user_schemas import UserCreate
from app.services.user_service import UserService
from app.services.email_service import EmailService
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

pytestmark = pytest.mark.asyncio

# Test creating a user with valid data
async def test_create_user_with_valid_data(db_session, email_service):
    user_data = {
        "email": "valid_user@example.com",
        "password": "ValidPassword123!",
        "nickname": "test_nickname_123"
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test creating a user with invalid data
@pytest.mark.asyncio
async def test_user_create_validation_errors(db_session: AsyncSession, email_service: EmailService):
    invalid_user_data = {
        "email": "invalidemail",
        "password": "short",
        "nickname": ""
    }

    with pytest.raises(HTTPException) as exc_info:
        await UserService.create(db_session, invalid_user_data, email_service)
    
    assert exc_info.value.status_code == 422
    assert "Validation error" in exc_info.value.detail
    assert "email" in exc_info.value.detail
    assert "value is not a valid email address" in exc_info.value.detail
    assert "nickname" in exc_info.value.detail
    assert "String should have at least 3 characters" in exc_info.value.detail
    assert "password" in exc_info.value.detail
    assert "String should have at least 8 characters" in exc_info.value.detail

# Test fetching a user by ID when the user exists
async def test_get_by_id_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_id(db_session, user.id)
    assert retrieved_user.id == user.id

# Test fetching a user by ID when the user does not exist
async def test_get_by_id_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    retrieved_user = await UserService.get_by_id(db_session, non_existent_user_id)
    assert retrieved_user is None

# Test fetching a user by nickname when the user exists
async def test_get_by_nickname_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_nickname(db_session, user.nickname)
    assert retrieved_user.nickname == user.nickname

# Test fetching a user by nickname when the user does not exist
async def test_get_by_nickname_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_nickname(db_session, "non_existent_nickname")
    assert retrieved_user is None

# Test fetching a user by email when the user exists
async def test_get_by_email_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_email(db_session, user.email)
    assert retrieved_user.email == user.email

# Test fetching a user by email when the user does not exist
async def test_get_by_email_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_email(db_session, "non_existent_email@example.com")
    assert retrieved_user is None

# Test updating a user with valid data
async def test_update_user_valid_data(db_session, user):
    new_email = "updated_email@example.com"
    updated_user = await UserService.update(db_session, user.id, {"email": new_email})
    assert updated_user is not None
    assert updated_user.email == new_email

# Test updating a user with invalid data
async def test_update_user_invalid_data(db_session: AsyncSession, user):
    invalid_update_data = {
        "email": "invalidemail"
    }

    with pytest.raises(HTTPException) as exc_info:
        await UserService.update(db_session, user.id, invalid_update_data)
    
    assert exc_info.value.status_code == 422
    assert "Validation error" in exc_info.value.detail
    assert "email" in exc_info.value.detail
    assert "value is not a valid email address" in exc_info.value.detail

# Test deleting a user who exists
async def test_delete_user_exists(db_session, user):
    deletion_success = await UserService.delete(db_session, user.id)
    assert deletion_success is True

# Test attempting to delete a user who does not exist
async def test_delete_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    deletion_success = await UserService.delete(db_session, non_existent_user_id)
    assert deletion_success is False

# Test listing users with pagination
async def test_list_users_with_pagination(db_session, users_with_same_role_50_users):
    users_page_1 = await UserService.list_users(db_session, skip=0, limit=10)
    users_page_2 = await UserService.list_users(db_session, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id

# Test registering a user with valid data
async def test_register_user_with_valid_data(db_session, email_service):
    user_data = {
        "email": "register_valid_user@example.com",
        "password": "RegisterValid123!",
        "nickname": "valid-nickname_123"
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test attempting to register a user with invalid data
async def test_register_user_with_invalid_data(db_session: AsyncSession, email_service):
    invalid_user_data = {
        "email": "registerinvalidemail",  # Invalid email
        "password": "short",  # Invalid password
        "nickname": "contain$-ill*g@l"  # Invalid nickname
    }

    with pytest.raises(HTTPException) as exc_info:
        await UserService.register_user(db_session, invalid_user_data, email_service)
    
    assert exc_info.value.status_code == 422
    assert "Validation error" in exc_info.value.detail
    assert "email" in exc_info.value.detail
    assert "nickname" in exc_info.value.detail
    assert "password" in exc_info.value.detail

# Test successful user login
async def test_login_user_successful(db_session, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "MySuperPassword$1234",
    }
    logged_in_user = await UserService.login_user(db_session, user_data["email"], user_data["password"])
    assert logged_in_user is not None

# Test user login with incorrect email
async def test_login_user_incorrect_email(db_session):
    user = await UserService.login_user(db_session, "nonexistentuser@noway.com", "Password123!")
    assert user is None

# Test user login with incorrect password
async def test_login_user_incorrect_password(db_session, user):
    user = await UserService.login_user(db_session, user.email, "IncorrectPassword!")
    assert user is None

# Test account lock after maximum failed login attempts
async def test_account_lock_after_failed_logins(db_session, verified_user):
    max_login_attempts = get_settings().max_login_attempts
    for _ in range(max_login_attempts):
        await UserService.login_user(db_session, verified_user.email, "wrongpassword")
    
    is_locked = await UserService.is_account_locked(db_session, verified_user.email)
    assert is_locked, "The account should be locked after the maximum number of failed login attempts."

# Test resetting a user's password
async def test_reset_password(db_session, user):
    new_password = "NewPassword123!"
    reset_success = await UserService.reset_password(db_session, user.id, new_password)
    assert reset_success is True

# Test verifying a user's email
async def test_verify_email_with_token(db_session, user):
    token = "valid_token_example"  # This should be set in your user setup if it depends on a real token
    user.verification_token = token  # Simulating setting the token in the database
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, token)
    assert result is True

# Test unlocking a user's account
async def test_unlock_user_account(db_session, locked_user):
    unlocked = await UserService.unlock_user_account(db_session, locked_user.id)
    assert unlocked, "The account should be unlocked"
    refreshed_user = await UserService.get_by_id(db_session, locked_user.id)
    assert not refreshed_user.is_locked, "The user should no longer be locked"

@pytest.mark.asyncio
async def test_create_user_with_existing_email(db_session: AsyncSession, email_service: EmailService):
    # Arrange: Add a user to the session to simulate an existing user with the same email
    existing_user = User(
        nickname="existing_user",
        email="test@example.com",
        first_name="Existing",
        last_name="User",
        hashed_password="hashedpassword",
        role="AUTHENTICATED",
        is_locked=False,
        email_verified=True,
    )
    db_session.add(existing_user)
    await db_session.commit()

    # Prepare the user data with the same email
    user_data = {
        "nickname": "new_user",
        "email": "test@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "Newpassowrd123!"
    }

    # Act & Assert: Try to create a new user with the same email and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await UserService.create(db_session, user_data, email_service)
    
    # Assert: Ensure the exception is raised with the correct status code and detail
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User with given email already exists."

@pytest.mark.asyncio
async def test_create_user_with_existing_nickname(db_session: AsyncSession, email_service: EmailService):
    # Arrange: Add a user to the session to simulate an existing user with the same nickname
    existing_user = User(
        nickname="existing_nickname",
        email="existing@example.com",
        first_name="Existing",
        last_name="User",
        hashed_password="hashedpassword",
        role="AUTHENTICATED",
        is_locked=False,
        email_verified=True
    )
    db_session.add(existing_user)
    await db_session.commit()

    # Prepare the user data with the same nickname
    user_data = {
        "nickname": "existing_nickname",
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "Newpassowrd123!"
    }

    # Act & Assert: Try to create a new user with the same nickname and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await UserService.create(db_session, user_data, email_service)
    
    # Assert: Ensure the exception is raised with the correct status code and detail
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User with given nickname already exists."

    @pytest.mark.asyncio
    async def test_update_user_with_existing_email(db_session: AsyncSession):
    # Arrange: Add an existing user with the same email to the session
        existing_user = User(
            id=uuid4(),
            nickname="existing_user",
            email="existing@example.com",
            first_name="Existing",
            last_name="User",
            hashed_password="hashedpassword",
            role="AUTHENTICATED",
            is_locked=False,
            email_verified=True
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Add another user that will be updated
        user_to_update = User(
            id=uuid4(),
            nickname="user_to_update",
            email="update@example.com",
            first_name="Update",
            last_name="User",
            hashed_password="hashedpassword",
            role="AUTHENTICATED",
            is_locked=False,
            email_verified=True
        )
        db_session.add(user_to_update)
        await db_session.commit()

        # Prepare the update data with the existing email
        update_data = {
            "email": "existing@example.com"
        }

    # Act & Assert: Try to update the user with the existing email and expect an HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await UserService.update(db_session, user_to_update.id, update_data)
    
        # Assert: Ensure the exception is raised with the correct status code and detail
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == "User with given email already exists."
        