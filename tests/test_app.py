import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
    
    def test_get_activities_contains_required_fields(self, client):
        """Test that activity objects have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Programming%20Class/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Programming%20Class/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_participants_same_activity(self, client, reset_activities):
        """Test that multiple different participants can signup"""
        response1 = client.post(
            "/activities/Tennis%20Club/signup?email=student1@mergington.edu"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Tennis%20Club/signup?email=student2@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Tennis Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        # First add a participant
        client.post(
            "/activities/Art%20Studio/signup?email=test@mergington.edu"
        )
        
        # Then unregister
        response = client.post(
            "/activities/Art%20Studio/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" not in activities_data["Art Studio"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_non_participant(self, client, reset_activities):
        """Test unregistering someone who isn't registered"""
        response = client.post(
            "/activities/Basketball%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_existing_participant_from_activity(self, client, reset_activities):
        """Test unregistering an already registered participant"""
        # Get initial participant count
        activities_response = client.get("/activities")
        initial_data = activities_response.json()
        initial_count = len(initial_data["Science Club"]["participants"])
        
        # Unregister one of the existing participants
        response = client.post(
            "/activities/Science%20Club/unregister?email=anna@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        updated_data = activities_response.json()
        updated_count = len(updated_data["Science Club"]["participants"])
        assert updated_count == initial_count - 1
        assert "anna@mergington.edu" not in updated_data["Science Club"]["participants"]


class TestRoot:
    """Tests for root redirect"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
