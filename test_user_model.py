"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test models for Users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "tester1@gmail.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("test2", "tester2@gmail.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)
        
        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        response = super().tearDown()
        db.session.rollback()
        return response

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the repr method work as expected?"""
        user = self.u1

        representation = User.__repr__(user)
        string = "<User #1111: test1, tester1@gmail.com>"

        self.assertEqual(representation, string)

    #####
    #
    # Following Tests
    #
    #####

    def test_user_following(self):
        """Is User 1 following User 2 detected?"""
        u1 = self.u1
        u2 = self.u2

        u1.following.append(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))
    
    def test_user_is_followed_by(self):
        """Is User 1 followed by User 2?"""

        u1 = self.u1
        u2 = self.u2

        u1.followers.append(u2)
        db.session.commit()

        self.assertTrue(u1.is_followed_by(u2))
    
    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)
    
    #####
    #
    # Signup Tests
    #
    #####

    def test_signup(self):
        """Test creating a new user"""

        new_user = User.signup("tester", "tester@gmail.com", "pass123", None)
        new_user.id = 8080
        db.session.commit()
        user_instance = User.query.get(8080)
        
        self.assertIsInstance(new_user, User)
        self.assertEqual(user_instance.username, "tester")
        self.assertEqual(user_instance.email, "tester@gmail.com")
        self.assertNotEqual(user_instance.password, "pass123")
        # Bcrypt strings should start with $2b$
        self.assertTrue(user_instance.password.startswith("$2b$"))
    
    def test_invalid_username_signup(self):
        """Test if invalid signup is handled"""
        invalid = User.signup(None, "test@test.com", "pass", None)
        invalid.id = 1234

        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError):
            User.signup("testtesttest", "email@gmail.com", "", None)
        
        with self.assertRaises(ValueError):
            User.signup("test0", "e34@gmail.com", None, None)
    
    #####
    #
    # Authentication Tests
    #
    #####

    def test_valid_authenication(self):
        user = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.uid1)
    
    def test_invalid_password_authentication(self):
        self.assertFalse(User.authenticate(self.u1.username, "Not_the_password"))

    def test_invalid_username_authentication(self):
        self.assertFalse(User.authenticate("somebodyelse", "password"))