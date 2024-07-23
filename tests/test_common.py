import os
import logging.config
import pytest
from unittest.mock import patch, MagicMock, call

from app.utils.common import setup_logging

@patch('os.path.join')
@patch('os.path.normpath')
@patch('logging.config.fileConfig')
def test_setup_logging(mock_fileConfig, mock_normpath, mock_path_join):
    # Arrange
    base_dir = os.path.dirname(__file__)
    relative_path = os.path.join(base_dir, '..', '..', 'logging.conf')
    normalized_path = os.path.normpath(relative_path)

    # Mocking the side effects to simulate the calls to os.path.join
    mock_path_join.side_effect = [
        os.path.join(base_dir, '..', '..', 'logging.conf'),
        os.path.join(base_dir, '..', '..', 'logging.conf')
    ]

    mock_normpath.return_value = normalized_path

    # Act
    setup_logging()

    # Assert
    # Ensure os.path.join was called with the correct arguments
    expected_calls = [
        call(base_dir, '..', '..', 'logging.conf'),
        call(os.path.dirname(__file__), '..', '..', 'logging.conf')
    ]

    # Check that os.path.join was called with the correct arguments
    mock_path_join.assert_has_calls(expected_calls, any_order=True)

    # Ensure os.path.normpath was called with the path returned by os.path.join
    mock_normpath.assert_called_with(relative_path)

    # Ensure logging.config.fileConfig was called with the normalized path
    mock_fileConfig.assert_called_once_with(normalized_path, disable_existing_loggers=False)
