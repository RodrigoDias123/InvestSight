import pytest
from unittest.mock import patch

from apps.apis.services.retry import with_retry
from apps.apis.exceptions import ProviderUnavailable


@pytest.mark.L7
class TestRetry:
    @patch("apps.apis.services.retry.RETRY_MAX_ATTEMPTS", 3)
    def test_retry_decorator(self):
        call_count = 0

        @with_retry
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ProviderUnavailable("Service unavailable")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 2
