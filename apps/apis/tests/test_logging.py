import pytest
from apps.apis.services.logging import get_logger, log_api_call


@pytest.mark.L8
class TestLogging:
    def test_get_logger(self):
        logger = get_logger("test")
        assert logger is not None

    def test_log_api_call_context_manager(self):
        with log_api_call(symbol="BTC", provider="mock"):
            pass
