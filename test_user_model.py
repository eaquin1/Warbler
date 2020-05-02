"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

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
    """Test views for messages."""

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

    def test_user_follows(self):
        """Is User 1 following User 2 detected?"""
        u1 = self.u1
        u2 = self.u2

        u1_following = Follows(user_being_followed_id = u2.id, user_following_id=u1.id)
        db.session.add(u1_following)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        