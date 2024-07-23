import pytest
from unittest.mock import patch, MagicMock
from app.main import exception_handler
from fastapi.responses import JSONResponse
import json

# Assuming startup_event is in app/main.py
from app.main import startup_event

@patch('app.main.Database.initialize')
@patch('app.main.get_settings')
@pytest.mark.asyncio
async def test_startup_event(mock_get_settings, mock_initialize):
    # Arrange
    mock_settings = MagicMock()
    mock_settings.database_url = "postgresql://user:pass@localhost/db"
    mock_settings.debug = True
    mock_get_settings.return_value = mock_settings

    # Act
    await startup_event()

    # Assert
    # Check that get_settings was called
    mock_get_settings.assert_called_once()

    # Check that Database.initialize was called with the correct parameters
    mock_initialize.assert_called_once_with(mock_settings.database_url, mock_settings.debug)

@pytest.mark.asyncio
async def test_exception_handler():
    # Arrange
    request = None  # We can use None for the request since it's not used in the function
    exc = Exception("Test exception")

    # Act
    response = await exception_handler(request, exc)

    # Assert
    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert json.loads(response.body.decode()) == {"message": "An unexpected error occurred."}
    
