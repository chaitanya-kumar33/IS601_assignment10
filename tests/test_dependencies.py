import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch, MagicMock
from app.dependencies import get_db
from app.dependencies import get_current_user
from app.services.jwt_service import decode_token
from jwt import PyJWTError

@pytest.mark.asyncio
async def test_get_db_session_success():
    # Mocking the AsyncSession and the session factory
    mock_session_factory = MagicMock()
    mock_session = AsyncMock()

    # Ensure the factory returns the mock session when called
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = False

    # Patching the Database.get_session_factory to return our mock session factory
    with patch('app.dependencies.Database.get_session_factory', return_value=mock_session_factory):
        # Simulate dependency injection behavior
        async for session in get_db():
            assert session == mock_session  # Check if the session returned is our mock session

@pytest.mark.asyncio
async def test_failed_token_decoding():
    # Mock the token and the expected exception
    token = "invalid_token"
    credentials_exception = HTTPException(
        status_code=401, 
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    # Patch decode_token to return None
    with patch('app.dependencies.decode_token', return_value=None) as mock_decode_token:
        # Patch logger to monitor log calls
        with patch('app.dependencies.logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)

            # Check that the exception raised is the credentials_exception
            assert exc_info.value.status_code == credentials_exception.status_code
            assert exc_info.value.detail == credentials_exception.detail

            # Check that decode_token was called with the correct token
            mock_decode_token.assert_called_once_with(token)

            # Check that the logger's error method was called with the expected message
            mock_logger.error.assert_called_once_with("Failed to decode token")

@pytest.mark.asyncio
async def test_no_user_found():
    # Mock the token and the expected exception
    token = "valid_token"
    email = "user@example.com"
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    # Mock the payload and user lookup to return None
    payload = {"sub": email, "role": "USER"}
    mock_session = AsyncMock(spec=AsyncSession)

    with patch('app.dependencies.decode_token', return_value=payload):
        with patch('app.dependencies.get_db', return_value=mock_session):
            with patch('app.services.user_service.UserService.get_by_email', return_value=None) as mock_get_by_email:
                with patch('app.dependencies.logger') as mock_logger:
                    with pytest.raises(HTTPException) as exc_info:
                        await get_current_user(token, db=mock_session)

                    # Check that the exception raised is the credentials_exception
                    assert exc_info.value.status_code == credentials_exception.status_code
                    assert exc_info.value.detail == credentials_exception.detail

                    # Check that get_by_email was called with the correct email
                    mock_get_by_email.assert_called_once_with(mock_session, email)

                    # Check that the logger's error method was called with the expected message
                    mock_logger.error.assert_any_call(f"No user found with email: {email}")

@pytest.mark.asyncio
async def test_user_found():
    # Mock the token and the user data
    token = "valid_token"
    email = "user@example.com"
    user = MagicMock(email=email, role=MagicMock(name="USER"))
    payload = {"sub": email, "role": "USER"}
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock the decode_token and user lookup to return a user object
    with patch('app.dependencies.decode_token', return_value=payload):
        with patch('app.dependencies.get_db', return_value=mock_session):
            with patch('app.services.user_service.UserService.get_by_email', return_value=user) as mock_get_by_email:
                with patch('app.dependencies.logger') as mock_logger:
                    result = await get_current_user(token, db=mock_session)

                    # Check that get_by_email was called with the correct email
                    mock_get_by_email.assert_called_once_with(mock_session, email)

                    # Check that the logger's info method was called with the expected message
                    mock_logger.info.assert_any_call(f"User found: {user.email}, role: {user.role}")

                    # Check the result
                    assert result == {"email": user.email, "role": user.role.name}

@pytest.mark.asyncio
async def test_jwt_error():
    # Mock the token and the expected exception
    token = "invalid_token"
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    # Mock decode_token to raise PyJWTError
    with patch('app.dependencies.decode_token', side_effect=PyJWTError("Invalid token")):
        with patch('app.dependencies.logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)

            # Check that the exception raised is the credentials_exception
            assert exc_info.value.status_code == credentials_exception.status_code
            assert exc_info.value.detail == credentials_exception.detail

            # Check that the logger's error method was called with the expected message
            mock_logger.error.assert_any_call("JWTError occurred: Invalid token")
