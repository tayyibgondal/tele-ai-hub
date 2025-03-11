import os
import pytest
from src.config import Config

def test_config_initialization(monkeypatch):
    """
    Test that Config reads environment variables and sets class attributes correctly.
    """

    config = Config()
    assert config.SECRET_KEY == None
    assert config.SQLALCHEMY_DATABASE_URI == 'sqlite:///site.db'
    assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False
