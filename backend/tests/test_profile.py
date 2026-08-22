import pytest
import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from auth.dependencies import get_current_user
from models.db_models import User, UserProfile
from config.database import engine

client = TestClient(app)

@pytest.fixture
def db():
    with Session(engine) as session:
        yield session

@pytest.fixture
def test_user(db: Session):
    # Arrange: create a user specifically for a test
    from sqlalchemy import text
    user = User(
        id=str(uuid.uuid4()),
        email=f"test-{uuid.uuid4()}@example.com",
        password_hash="fakehash"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    # Cleanup: remove profile and user
    db.exec(text("DELETE FROM user_profiles WHERE user_id = :uid").bindparams(uid=user.id))
    db.exec(text("DELETE FROM users WHERE id = :uid").bindparams(uid=user.id))
    db.commit()

@pytest.fixture
def auth_client(test_user):
    def override_get_current_user():
        return test_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()


class TestProfileRoute:
    
    def test_get_profile_missing_returns_empty(self, auth_client, test_user, db):
        # Initial GET should return empty since profile doesn't exist yet
        response = auth_client.get("/profile/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] is None
        assert data["date_of_birth"] is None
        assert data["language"] is None

        # Verify GET did NOT create a UserProfile row
        profile = db.exec(select(UserProfile).where(UserProfile.user_id == test_user.id)).first()
        assert profile is None

    def test_patch_profile_creates_profile(self, auth_client, test_user, db):
        # Update profile with just name
        response = auth_client.patch("/profile/", json={"name": "Alice Smith"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == "Alice Smith"
        assert data["date_of_birth"] is None
        assert data["language"] is None

        # Verify database has exactly one profile
        profiles = db.exec(select(UserProfile).where(UserProfile.user_id == test_user.id)).all()
        assert len(profiles) == 1
        assert profiles[0].name == "Alice Smith"

    def test_patch_profile_partial_update(self, auth_client, test_user, db):
        # Arrange: create an existing profile for this test
        profile = UserProfile(user_id=test_user.id, name="Alice Smith")
        db.add(profile)
        db.commit()

        # Act: Update only language
        response = auth_client.patch("/profile/", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Smith"
        assert data["language"] == "en"
        assert data["date_of_birth"] is None

    def test_patch_profile_date_of_birth(self, auth_client, test_user, db):
        # Arrange: create profile
        profile = UserProfile(user_id=test_user.id, name="Alice Smith", language="en")
        db.add(profile)
        db.commit()

        # Act: Update date of birth
        response = auth_client.patch("/profile/", json={"date_of_birth": "1990-05-15"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Smith"
        assert data["language"] == "en"
        assert data["date_of_birth"] == "1990-05-15"
        
    def test_get_profile_persists(self, auth_client):
        # Act: patch data
        auth_client.patch("/profile/", json={
            "name": "Alice Smith",
            "language": "en",
            "date_of_birth": "1990-05-15"
        })

        # Assert: GET should return the persisted data
        response = auth_client.get("/profile/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Smith"
        assert data["language"] == "en"
        assert data["date_of_birth"] == "1990-05-15"

    def test_patch_validation_error(self, auth_client, db, test_user):
        # Empty string for name should fail validation
        response = auth_client.patch("/profile/", json={"name": "   "})
        assert response.status_code == 422
        
        # Verify no profile was created
        profile = db.exec(select(UserProfile).where(UserProfile.user_id == test_user.id)).first()
        assert profile is None
        
    def test_user_isolation(self, auth_client, test_user, db):
        # Arrange: User A has a profile
        profile_a = UserProfile(user_id=test_user.id, name="User A")
        db.add(profile_a)
        db.commit()
        
        # Arrange: Create User B
        user_b = User(
            id=str(uuid.uuid4()),
            email=f"other-{uuid.uuid4()}@example.com",
            password_hash="fakehash"
        )
        db.add(user_b)
        db.commit()
        
        try:
            # Switch to User B
            app.dependency_overrides[get_current_user] = lambda: user_b
            
            # Act/Assert: New user should have empty profile
            response = client.get("/profile/")
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == user_b.email
            assert data["name"] is None
            
            # Act: User B updates their profile
            patch_resp = client.patch("/profile/", json={"name": "User B"})
            assert patch_resp.status_code == 200
            
            # Assert: User A's profile is untouched
            db.refresh(profile_a)
            assert profile_a.name == "User A"
        finally:
            # Cleanup User B
            from sqlalchemy import text
            db.exec(text("DELETE FROM user_profiles WHERE user_id = :uid").bindparams(uid=user_b.id))
            db.exec(text("DELETE FROM users WHERE id = :uid").bindparams(uid=user_b.id))
            db.commit()

    def test_one_to_one_primary_key_constraint(self, test_user, db):
        # Insert first profile
        profile1 = UserProfile(user_id=test_user.id, name="First")
        db.add(profile1)
        db.commit()
        
        # Attempt to insert second profile for the same user
        profile2 = UserProfile(user_id=test_user.id, name="Second")
        db.add(profile2)
        
        # Expect an IntegrityError because user_id is the Primary Key
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
