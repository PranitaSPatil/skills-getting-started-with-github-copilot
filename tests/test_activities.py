"""
Unit tests for FastAPI activity management endpoints.
"""
import pytest


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_activities_success(self, client):
        """Test successful retrieval of all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Check that activities dict is returned
        assert isinstance(activities, dict)
        # Check known activities exist
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Team" in activities

    def test_activity_structure(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        # Check structure of an activity
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        # Verify types
        assert isinstance(chess_club["description"], str)
        assert isinstance(chess_club["schedule"], str)
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["participants"], list)

    def test_activities_have_initial_participants(self, client):
        """Test that some activities have initial participants."""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants initially
        assert len(activities["Chess Club"]["participants"]) > 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, sample_email):
        """Test successful signup for an activity."""
        response = client.post(
            f"/activities/Art%20Studio/signup?email={sample_email}"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Signed up" in result["message"]
        assert sample_email in result["message"]

    def test_signup_adds_participant(self, client, sample_email):
        """Test that signup actually adds participant to the activity."""
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Drama Club"]["participants"].copy()
        initial_count = len(initial_participants)

        # Sign up
        client.post(f"/activities/Drama%20Club/signup?email={sample_email}")

        # Get updated participant count
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()["Drama Club"]["participants"]
        updated_count = len(updated_participants)

        assert updated_count == initial_count + 1
        assert sample_email in updated_participants

    def test_signup_already_registered(self, client):
        """Test that signup fails if participant already registered."""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity(self, client, sample_email):
        """Test that signup fails for nonexistent activity."""
        response = client.post(
            f"/activities/Nonexistent%20Activity/signup?email={sample_email}"
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_various_activities(self, client):
        """Test signing up for multiple different activities."""
        emails = ["alice@test.edu", "bob@test.edu", "charlie@test.edu"]
        activities = ["Tennis Club", "Science Club", "Robotics Team"]
        
        for email, activity in zip(emails, activities):
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
            )
            assert response.status_code == 200


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant."""
        email = "michael@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Removed" in result["message"]
        assert email in result["message"]

    def test_remove_participant_verification(self, client):
        """Test that removed participant is actually removed."""
        email = "daniel@mergington.edu"  # Initially in Chess Club
        
        # Verify participant is there
        initial = client.get("/activities")
        assert email in initial.json()["Chess Club"]["participants"]
        
        # Remove participant
        client.delete(f"/activities/Chess%20Club/participants?email={email}")
        
        # Verify participant is gone
        updated = client.get("/activities")
        assert email not in updated.json()["Chess Club"]["participants"]

    def test_remove_nonexistent_participant(self, client):
        """Test that removing non-existent participant fails."""
        response = client.delete(
            f"/activities/Chess%20Club/participants?email=doesnotexist@test.edu"
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Participant not found" in result["detail"]

    def test_remove_from_nonexistent_activity(self, client):
        """Test that removing from non-existent activity fails."""
        response = client.delete(
            f"/activities/Fake%20Activity/participants?email=test@test.edu"
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_remove_and_readd_participant(self, client):
        """Test that a removed participant can be re-added."""
        email = "rachel@mergington.edu"
        activity = "Tennis%20Club"
        
        # Remove
        client.delete(f"/activities/{activity}/participants?email={email}")
        check = client.get("/activities")
        assert email not in check.json()["Tennis Club"]["participants"]
        
        # Re-add
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify re-added
        final = client.get("/activities")
        assert email in final.json()["Tennis Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_full_signup_and_removal_flow(self, client):
        """Test complete flow: signup, verify, remove, verify removal."""
        email = "integration@test.edu"
        activity = "Gym%20Class"
        
        # Initial state
        initial = client.get("/activities").json()
        initial_count = len(initial["Gym Class"]["participants"])
        
        # Sign up
        signup_resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_resp.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities").json()
        assert email in after_signup["Gym Class"]["participants"]
        assert len(after_signup["Gym Class"]["participants"]) == initial_count + 1
        
        # Remove
        remove_resp = client.delete(f"/activities/{activity}/participants?email={email}")
        assert remove_resp.status_code == 200
        
        # Verify removal
        after_removal = client.get("/activities").json()
        assert email not in after_removal["Gym Class"]["participants"]
        assert len(after_removal["Gym Class"]["participants"]) == initial_count

    def test_multiple_participants_in_activity(self, client):
        """Test adding multiple participants to an activity."""
        emails = ["user1@test.edu", "user2@test.edu", "user3@test.edu"]
        activity = "Art%20Studio"
        
        initial = client.get("/activities").json()
        initial_count = len(initial["Art Studio"]["participants"])
        
        # Add multiple participants
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added
        final = client.get("/activities").json()
        final_count = len(final["Art Studio"]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in final["Art Studio"]["participants"]
