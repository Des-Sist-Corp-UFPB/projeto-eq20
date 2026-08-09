import unittest
from unittest.mock import MagicMock, patch
import pytest
import json
from app.services.ai_moderation_service import AIModerationService
from app.config.settings import settings

def test_clean_text():
    # Test control chars removal and space normalization
    text_with_control = "Hello\u0000 \n\t World!  "
    cleaned = AIModerationService._clean_text(text_with_control, max_length=50)
    assert cleaned == "Hello World!"

    # Test max length truncation
    long_text = "a" * 200
    cleaned = AIModerationService._clean_text(long_text, max_length=50)
    assert len(cleaned) == 50

@patch("app.services.ai_moderation_service.OpenAI")
def test_moderate_success(mock_openai_class):
    # Mock successful OpenAI API call returning valid JSON
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"title": "Buraco na Via", "description": "Existe um buraco grande na rua principal."}'))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    # Force configurations for testing
    with patch.object(settings, "AI_API_KEY", "test_key"), \
         patch.object(settings, "AI_BASE_URL", "https://api.openai.com/v1"):
        
        t, d = AIModerationService.moderate("BURACO RUIM!", "tem um buraco horrivel aqui fdp")
        
        assert t == "Buraco na Via"
        assert d == "Existe um buraco grande na rua principal."

@patch("app.services.ai_moderation_service.OpenAI")
def test_moderate_invalid_json_fallback(mock_openai_class):
    # Mock OpenAI API call returning invalid JSON
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='invalid json here'))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    with patch.object(settings, "AI_API_KEY", "test_key"), \
         patch.object(settings, "AI_BASE_URL", "https://api.openai.com/v1"):
        
        orig_title = "BURACO RUIM!"
        orig_desc = "tem um buraco horrivel aqui fdp"
        t, d = AIModerationService.moderate(orig_title, orig_desc)
        
        # Should fallback to original texts
        assert t == orig_title
        assert d == orig_desc

@patch("app.services.ai_moderation_service.OpenAI")
def test_moderate_missing_keys_fallback(mock_openai_class):
    # Mock OpenAI returning JSON without required keys
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"incorrect_key": "some value"}'))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    with patch.object(settings, "AI_API_KEY", "test_key"), \
         patch.object(settings, "AI_BASE_URL", "https://api.openai.com/v1"):
        
        orig_title = "BURACO RUIM!"
        orig_desc = "tem um buraco horrivel aqui fdp"
        t, d = AIModerationService.moderate(orig_title, orig_desc)
        
        assert t == orig_title
        assert d == orig_desc

@patch("app.services.ai_moderation_service.OpenAI")
def test_moderate_exception_fallback(mock_openai_class):
    # Mock OpenAI raising an error
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API connection timed out")

    with patch.object(settings, "AI_API_KEY", "test_key"), \
         patch.object(settings, "AI_BASE_URL", "https://api.openai.com/v1"):
        
        orig_title = "BURACO RUIM!"
        orig_desc = "tem um buraco horrivel aqui fdp"
        t, d = AIModerationService.moderate(orig_title, orig_desc)
        
        assert t == orig_title
        assert d == orig_desc
