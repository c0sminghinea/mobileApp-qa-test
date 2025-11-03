import pytest
import requests
from typing import Dict, Optional, Literal
from enum import Enum

# ===================================
# CONFIGURATION & ROUTES
# ===================================

class Config:
    """Test configuration constants"""
    BASE_URL = "http://localhost:3000"
    TIMEOUT = 10
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"
    }


class APIRoutes(Enum):
    """Centralized API endpoint routes"""
    VALIDATE_STEPS = "/steps/v2/{user_id}"
    GET_STREAKS = "/streaks"
    CHECK_STREAK = "/streaks/check"
    BUY_TOOLS = "/streaks/recovery-tools/buy"
    MONTH_HISTORY = "/streaks/month-history/{date}"


# ===================================
# API CLIENT
# ===================================

class APIClient:

    def __init__(self, base_url: str = Config.BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)

    def _make_request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        payload: Optional[Dict] = None
    ) -> requests.Response:
        """Unified request handler"""
        try:
            if method == "GET":
                return self.session.get(url, timeout=Config.TIMEOUT)
            elif method == "POST":
                return self.session.post(url, json=payload, timeout=Config.TIMEOUT)
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Request failed: {e}")

    def get(self, route: APIRoutes, **kwargs) -> requests.Response:
        """GET request with route enum"""
        url = f"{self.base_url}{route.value.format(**kwargs)}"
        return self._make_request("GET", url)

    def post(self, route: APIRoutes, payload: Dict, **kwargs) -> requests.Response:
        """POST request with route enum"""
        url = f"{self.base_url}{route.value.format(**kwargs)}"
        return self._make_request("POST", url, payload)


# ===================================
# API HELPER
# ===================================

class StreaksAPIHelper:

    def __init__(self, client: APIClient):
        self.client = client

    def validate_steps(self, user_id: str, steps: int) -> requests.Response:
        """POST /steps/v2/{uuid}"""
        return self.client.post(
            APIRoutes.VALIDATE_STEPS, payload={"steps": steps}, user_id=user_id
        )

    def get_active_streak(self) -> requests.Response:
        """GET /streaks"""
        return self.client.get(APIRoutes.GET_STREAKS)

    def check_streak_status(self) -> requests.Response:
        """GET /streaks/check"""
        return self.client.get(APIRoutes.CHECK_STREAK)

    def buy_recovery_tools(self, quantity: int) -> requests.Response:
        """POST /streaks/recovery-tools/buy"""
        return self.client.post(
            APIRoutes.BUY_TOOLS, payload={"quantity": quantity}
        )

    def get_month_history(self, year_month: str) -> requests.Response:
        """GET /streaks/month-history/{date}"""
        return self.client.get(APIRoutes.MONTH_HISTORY, date=year_month)


# ===================================
# VALIDATION HELPER
# ===================================

class ValidationHelper:

    @staticmethod
    def assert_status_code(response: requests.Response, expected_code: int):
        assert response.status_code == expected_code, \
            f"Expected {expected_code}, got {response.status_code}. Response: {response.text}"

    @staticmethod
    def assert_json_structure(data: Dict, required_keys: list):
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    @staticmethod
    def assert_streak_data(streak: Dict, expected_counter: int):
        required_keys = ["id", "counter", "startDate", "endDate"]
        ValidationHelper.assert_json_structure(streak, required_keys)
        assert streak["counter"] == expected_counter, \
            f"Expected counter {expected_counter}, got {streak['counter']}"

    @staticmethod
    def assert_successful_response(response: requests.Response):
        assert 200 <= response.status_code < 300, \
            f"Expected success status, got {response.status_code}"

    @staticmethod
    def assert_error_response(response: requests.Response, expected_message: str = None):
        assert 400 <= response.status_code < 500, \
            f"Expected error status, got {response.status_code}"
        if expected_message:
            data = response.json()
            assert data.get("message") == expected_message, \
                f"Expected message '{expected_message}', got '{data.get('message')}'"

    @staticmethod
    def assert_streak_active(streak: Dict):
        assert streak["endDate"] is None, "Streak should be active (no end date)"

    @staticmethod
    def assert_streak_lost(data: Dict, expected_last_counter: int = None):
        assert data["hasLost"] is True, "Streak should be lost"
        assert data["streak"] is None, "Streak should be null"
        if expected_last_counter:
            assert data["counterLastStreak"] == expected_last_counter, \
                f"Expected last counter {expected_last_counter}, got {data['counterLastStreak']}"


# ===================================
# PYTEST FIXTURES
# ===================================

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def api(api_client):
    return StreaksAPIHelper(api_client)

@pytest.fixture
def validator():
    return ValidationHelper()


# ===================================
# TEST SUITE 
# ===================================

@pytest.mark.priority1
class TestStreakCreationAndIncrement:

    def test_create_first_streak_for_new_user(self, api, validator):
        user_id = "test-user-new"
        steps = 10000
        response = api.validate_steps(user_id, steps)
        validator.assert_status_code(response, 201)
        data = response.json()
        validator.assert_json_structure(data, ["data"])
        validator.assert_json_structure(data["data"], ["coinsEarned", "streak"])
        streak = data["data"]["streak"]
        validator.assert_streak_data(streak, expected_counter=1)
        validator.assert_streak_active(streak)
        assert data["data"]["coinsEarned"] > 0, "User should earn coins"
        print(f"✓ First streak created successfully: {streak}")

    def test_increment_existing_streak_consecutive_day(self, api, validator):
        user_id = "test-user-active-streak"
        steps = 12000
        expected_new_counter = 6
        response = api.validate_steps(user_id, steps)
        validator.assert_status_code(response, 201)
        data = response.json()
        streak = data["data"]["streak"]
        validator.assert_streak_data(streak, expected_counter=expected_new_counter)
        print(f"✓ Streak incremented successfully to {expected_new_counter}")
        get_response = api.get_active_streak()
        validator.assert_status_code(get_response, 200)
        streak_data = get_response.json()
        assert streak_data["counter"] == expected_new_counter
        assert streak_data["hasValidatedToday"] is True
        print(f"✓ GET /streaks confirms counter = {expected_new_counter}")


@pytest.mark.priority2
class TestFreezerMechanism:

    def test_automatic_freezer_consumption_saves_streak(self, api, validator):
        response = api.check_streak_status()
        validator.assert_status_code(response, 200)
        data = response.json()
        assert data["hasLost"] is False, "Streak should be saved by freezer"
        assert "toolsUsed" in data, "Response should indicate tools used"
        assert data["toolsUsed"] >= 1, f"At least 1 freezer should be used"
        streak = data["streak"]
        assert streak is not None, "Streak should still exist"
        assert streak["counter"] == 8, f"Streak counter should remain 8"
        print(f"✓ Freezer consumed successfully, streak preserved at {streak['counter']}")
        get_response = api.get_active_streak()
        validator.assert_status_code(get_response, 200)
        tools = get_response.json()["tools"]
        assert tools["available"] == 1, f"Should have 1 freezer remaining"
        print(f"✓ Remaining freezers: {tools['available']}/{tools['max']}")

    def test_streak_lost_when_no_freezers_available(self, api, validator):
        response = api.check_streak_status()
        validator.assert_status_code(response, 200)
        data = response.json()
        validator.assert_streak_lost(data, expected_last_counter=10)
        print(f"✓ Streak correctly lost. Last streak was {data['counterLastStreak']} days")
        user_id = "test-user-no-freezers"
        new_steps_response = api.validate_steps(user_id, 10000)
        validator.assert_status_code(new_steps_response, 201)
        new_streak = new_steps_response.json()["data"]["streak"]
        validator.assert_streak_data(new_streak, expected_counter=1)
        print(f"✓ New streak started with counter = 1")


@pytest.mark.priority3
class TestFreezerPurchase:

    def test_successful_freezer_purchase(self, api, validator):
        quantity = 1
        response = api.buy_recovery_tools(quantity)
        validator.assert_successful_response(response)
        data = response.json()
        assert "message" in data, "Response should contain success message"
        assert "success" in data["message"].lower()
        print(f"✓ Purchase successful: {data['message']}")
        get_response = api.get_active_streak()
        validator.assert_status_code(get_response, 200)
        tools = get_response.json()["tools"]
        assert tools["available"] >= quantity
        print(f"✓ Freezers updated: {tools['available']}/{tools['max']}")

    def test_purchase_fails_insufficient_coins(self, api, validator):
        response = api.buy_recovery_tools(quantity=1)
        validator.assert_error_response(response, expected_message="not_enough_coins")
        print(f"✓ Purchase correctly rejected: not_enough_coins")

    def test_purchase_fails_at_maximum_freezers(self, api, validator):
        response = api.buy_recovery_tools(quantity=1)
        validator.assert_status_code(response, 400)
        data = response.json()
        expected_errors = ["already_have_max_recovery_tools", "cant_buy_more_than_max"]
        assert data["message"] in expected_errors
        print(f"✓ Purchase correctly blocked: {data['message']}")


# ===================================
# TEST SUITE - EDGE CASES
# ===================================

class TestEdgeCases:

    def test_invalid_steps_above_maximum(self, api, validator):
        user_id = "test-user-new"
        invalid_steps = 200000
        response = api.validate_steps(user_id, invalid_steps)
        validator.assert_error_response(response)
        data = response.json()
        assert "message" in data
        assert "150000" in data["message"] or "maximum" in data["message"].lower()
        print(f"✓ Invalid steps correctly rejected: {data['message']}")

    def test_monthly_history_retrieval(self, api, validator):
        year_month = "2025-01"
        response = api.get_month_history(year_month)
        validator.assert_status_code(response, 200)
        data = response.json()
        validator.assert_json_structure(data, ["streaks"])
        assert isinstance(data["streaks"], list)
        if len(data["streaks"]) > 0:
            first_streak = data["streaks"][0]
            required_keys = ["date", "counter", "isActive"]
            validator.assert_json_structure(first_streak, required_keys)
        print(f"✓ Monthly history retrieved: {len(data['streaks'])} entries")

    def test_double_validation_same_day(self, api, validator):
        user_id = "test-user-active-streak"
        response1 = api.validate_steps(user_id, 10000)
        validator.assert_status_code(response1, 201)
        counter_after_first = response1.json()["data"]["streak"]["counter"]

        response2 = api.validate_steps(user_id, 15000)
        validator.assert_status_code(response2, 201)
        counter_after_second = response2.json()["data"]["streak"]["counter"]

        assert counter_after_first == counter_after_second, \
            "Counter should not increment on double validation"

       
    def test_invalid_month_format(self, api, validator):
        response = api.get_month_history("25-01")  # Invalid format
        validator.assert_status_code(response, 400)


# ===================================
# SESSION FIXTURES
# ===================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    print("\n" + "="*50)
    print("Setting up test environment...")
    print("Note: Assuming database has been initialized with db-insert.sql")
    print("="*50 + "\n")
    yield
    print("\n" + "="*50)
    print("Test suite completed")
    print("="*50 + "\n")


@pytest.fixture(autouse=True)
def log_test_execution(request):
    print(f"\n▶ Running: {request.node.name}")
    yield
    print(f"✓ Completed: {request.node.name}\n")


# ===================================
# MAIN EXECUTION
# ===================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
