import pytest
from fastapi import HTTPException, status, Request
from unittest.mock import AsyncMock, patch
from uuid import UUID
from app.services.user_service import UserService
from app.schemas.user_schemas import UserUpdate,UserResponse, UserCreate
from app.utils.link_generation import create_user_links
from sqlalchemy.ext.asyncio import AsyncSession
from types import SimpleNamespace
from app.routers.user_routes import delete_user
from fastapi.responses import Response
from app.routers.user_routes import create_user

# Function to be tested
async def get_user(user_id: UUID, request: Request, db: AsyncSession, token: str, current_user: dict):
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_construct(
        id=user.id,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        profile_picture_url=user.profile_picture_url,
        github_profile_url=user.github_profile_url,
        linkedin_profile_url=user.linkedin_profile_url,
        role=user.role,
        email=user.email,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        links=create_user_links(user.id, request)
    )

# Mock data as an object
mock_user = SimpleNamespace(
    id="12345",
    nickname="testuser",
    first_name="Test",
    last_name="User",
    bio="Test bio",
    profile_picture_url="http://example.com/pic.jpg",
    github_profile_url="http://github.com/testuser",
    linkedin_profile_url="http://linkedin.com/in/testuser",
    role="user",
    email="testuser@example.com",
    last_login_at="2022-01-01T00:00:00",
    created_at="2022-01-01T00:00:00",
    updated_at="2022-01-01T00:00:00"
)

@pytest.mark.asyncio
async def test_get_user_not_found():
    user_id = "12345"
    request = AsyncMock()  # Mock the request object
    db = AsyncMock()  # Mock the database session

    # Mock the UserService.get_by_id to return None
    with patch.object(UserService, 'get_by_id', return_value=None):
        # Call the function and assert it raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_user(user_id, request, db, "token", {"role": "ADMIN"})

        # Assert the exception details
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

@pytest.mark.asyncio
async def test_delete_user_success():
    user_id = UUID("12345678-1234-5678-1234-567812345678")
    db = AsyncMock()  # Mock the database session

    # Mock the UserService.delete to return True (user deleted successfully)
    with patch.object(UserService, 'delete', return_value=True):
        # Call the function
        result = await delete_user(user_id, db, "token", {"role": "ADMIN"})

        # Assert the result
        assert isinstance(result, Response)
        assert result.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.asyncio
async def test_delete_user_not_found():
    user_id = UUID("12345678-1234-5678-1234-567812345678")
    db = AsyncMock()  # Mock the database session

    # Mock the UserService.delete to return False (user not found)
    with patch.object(UserService, 'delete', return_value=False):
        # Call the function and assert it raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await delete_user(user_id, db, "token", {"role": "ADMIN"})

        # Assert the exception details
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_create_user_email_exists():
    user_data = {"email": "existing@example.com", "password": "Password123!", "nickname": "testuser"}
    user = UserCreate(**user_data)
    request = AsyncMock()  # Mock the request object
    db = AsyncMock()  # Mock the database session
    email_service = AsyncMock()  # Mock the email service

    # Mock the UserService.get_by_email to return an existing user
    with patch.object(UserService, 'get_by_email', return_value=True):
        # Call the function and assert it raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_user(user, request, db, email_service, "token", {"role": "ADMIN"})

        # Assert the exception details
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Email already exists"

@pytest.mark.asyncio
async def test_create_user_creation_failed():
    user_data = {"email": "newuser@example.com", "password": "Password123!", "nickname": "testuser"}
    user = UserCreate(**user_data)
    request = AsyncMock()  # Mock the request object
    db = AsyncMock()  # Mock the database session
    email_service = AsyncMock()  # Mock the email service

    # Mock the UserService.get_by_email to return None (no existing user)
    # Mock the UserService.create to return None (creation failed)
    with patch.object(UserService, 'get_by_email', return_value=None):
        with patch.object(UserService, 'create', return_value=None):
            # Call the function and assert it raises HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await create_user(user, request, db, email_service, "token", {"role": "ADMIN"})

            # Assert the exception details
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exc_info.value.detail == "Failed to create user"

