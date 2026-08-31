"""
Comprehensive tests for Mergington High School Activities API

Uses AAA (Arrange-Act-Assert) pattern with hardcoded test data for clarity.
All tests use reset_activities fixture to ensure clean state per test.
"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirect(self, client):
        """
        Arrange: Make request to root endpoint
        Act: Call GET /
        Assert: Should redirect to static frontend
        """
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_returns_dict(self, client, reset_activities):
        """
        Arrange: Request all activities
        Act: Call GET /activities
        Assert: Returns dictionary of activities
        """
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities_data = response.json()
        assert isinstance(activities_data, dict)
        assert len(activities_data) > 0
    
    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """
        Arrange: Request all activities
        Act: Call GET /activities
        Assert: Each activity has required fields
        """
        response = client.get("/activities")
        activities_data = response.json()
        
        # Check each activity has expected fields
        for activity_name, activity_details in activities_data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_chess_club_exists(self, client, reset_activities):
        """
        Arrange: Request all activities
        Act: Call GET /activities
        Assert: Chess Club activity exists with expected data
        """
        response = client.get("/activities")
        activities_data = response.json()
        
        assert "Chess Club" in activities_data
        chess_club = activities_data["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """
        Arrange: New student email and existing activity
        Act: Call POST /activities/Chess Club/signup?email=newstudent@mergington.edu
        Assert: Student added successfully with 200 response
        """
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """
        Arrange: New student email and existing activity
        Act: Call POST signup then GET /activities
        Assert: Participant appears in the activity's participants list
        """
        # Act: Sign up student
        client.post(
            "/activities/Programming Class/signup",
            params={"email": "alice@mergington.edu"}
        )
        
        # Assert: Participant appears in list
        response = client.get("/activities")
        activities_data = response.json()
        participants = activities_data["Programming Class"]["participants"]
        assert "alice@mergington.edu" in participants
    
    def test_signup_duplicate_student_rejected(self, client, reset_activities):
        """
        Arrange: Student already signed up for an activity
        Act: Attempt to sign up same student again
        Assert: Request rejected with 400 status and error message
        """
        # Arrange: First signup (establishes initial state)
        client.post(
            "/activities/Gym Class/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        
        # Act: Try to sign up again
        response = client.post(
            "/activities/Gym Class/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        
        # Assert: Rejected
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_404(self, client, reset_activities):
        """
        Arrange: Activity name that doesn't exist
        Act: Call POST /activities/Nonexistent Club/signup
        Assert: Returns 404 Not Found
        """
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_increments_participant_count(self, client, reset_activities):
        """
        Arrange: Activity with known initial participant count
        Act: Sign up new student
        Assert: Participant count increases by 1
        """
        # Arrange: Get initial count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()["Basketball Team"]["participants"])
        
        # Act: Sign up
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newplayer@mergington.edu"}
        )
        
        # Assert: Count increased
        response_after = client.get("/activities")
        new_count = len(response_after.json()["Basketball Team"]["participants"])
        assert new_count == initial_count + 1


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """
        Arrange: Existing participant in an activity
        Act: Call POST /activities/Chess Club/unregister?email=michael@mergington.edu
        Assert: Participant removed successfully with 200 response
        """
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_removes_from_list(self, client, reset_activities):
        """
        Arrange: Existing participant
        Act: Call POST unregister then GET /activities
        Assert: Participant removed from the activity's list
        """
        # Arrange: Verify participant exists
        response = client.get("/activities")
        assert "isabella@mergington.edu" in response.json()["Art Studio"]["participants"]
        
        # Act: Unregister
        client.post(
            "/activities/Art Studio/unregister",
            params={"email": "isabella@mergington.edu"}
        )
        
        # Assert: Participant no longer in list
        response = client.get("/activities")
        participants = response.json()["Art Studio"]["participants"]
        assert "isabella@mergington.edu" not in participants
    
    def test_unregister_nonexistent_activity_404(self, client, reset_activities):
        """
        Arrange: Activity name that doesn't exist
        Act: Call POST /activities/Fake Club/unregister
        Assert: Returns 404 Not Found
        """
        response = client.post(
            "/activities/Fake Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_student_400(self, client, reset_activities):
        """
        Arrange: Student not registered for the activity
        Act: Try to unregister student not in participants list
        Assert: Returns 400 Bad Request with error message
        """
        response = client.post(
            "/activities/Tennis Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_decrements_participant_count(self, client, reset_activities):
        """
        Arrange: Activity with known initial participant count
        Act: Unregister a participant
        Assert: Participant count decreases by 1
        """
        # Arrange: Get initial count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()["Music Ensemble"]["participants"])
        
        # Act: Unregister existing participant
        client.post(
            "/activities/Music Ensemble/unregister",
            params={"email": "noah@mergington.edu"}
        )
        
        # Assert: Count decreased
        response_after = client.get("/activities")
        new_count = len(response_after.json()["Music Ensemble"]["participants"])
        assert new_count == initial_count - 1
    
    def test_unregister_then_signup_allowed(self, client, reset_activities):
        """
        Arrange: Participant already in activity
        Act: Unregister them, then sign up again
        Assert: Both operations succeed (student can re-register after unregistering)
        """
        activity = "Debate Club"
        email = "alexander@mergington.edu"
        
        # Act: Unregister
        response1 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Act: Sign up again
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Second signup succeeds
        assert response2.status_code == 200
        
        # Assert: Student appears in participants list
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestIntegrationScenarios:
    """Tests for realistic usage scenarios combining multiple endpoints"""
    
    def test_full_signup_workflow(self, client, reset_activities):
        """
        Arrange: New student joining
        Act: Get activities, view details, sign up
        Assert: Student appears in participant list
        """
        # Act: Get all activities
        response1 = client.get("/activities")
        assert response1.status_code == 200
        activities_data = response1.json()
        initial_count = len(activities_data["Science Olympiad"]["participants"])
        
        # Act: Sign up for Science Olympiad
        email = "newscientist@mergington.edu"
        response2 = client.post(
            "/activities/Science Olympiad/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Assert: Participant count increased and student in list
        response3 = client.get("/activities")
        new_data = response3.json()
        assert len(new_data["Science Olympiad"]["participants"]) == initial_count + 1
        assert email in new_data["Science Olympiad"]["participants"]
    
    def test_multiple_students_signup_same_activity(self, client, reset_activities):
        """
        Arrange: Multiple students signing up for same activity
        Act: Multiple POST requests to same activity
        Assert: All students added without conflict
        """
        activity = "Tennis Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Act: Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert: All students in participants list
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
    
    def test_signup_unregister_signup_cycle(self, client, reset_activities):
        """
        Arrange: Student registers for activity
        Act: Unregister, then re-register
        Assert: Student cycles through without errors
        """
        activity = "Programming Class"
        email = "cycling@mergington.edu"
        
        # Act & Assert: First signup
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Act & Assert: Unregister
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Act & Assert: Re-signup
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Assert: Student in list on final check
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
