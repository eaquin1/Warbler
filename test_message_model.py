"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes 

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

class MessageModelTestCase(TestCase):
    """Test models for Messages"""

    def setUp(self):
        """Create test client, add sample data"""
        db.drop_all()
        db.create_all()

        self.uid = 1245
        user = User.signup("testing", "testing@email.com", "password", None)
        user.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)
        self.client = app.test_client()

    def tearDown(self):
        response = super().tearDown()
        db.session.rollback()
        return response
    
    def test_message_model(self):
        """Does the basic model work?"""

        msg = Message(text="texting", user_id=self.uid)

        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.text, "texting")

    def test_likes(self):
        """Do likes work?"""

        msg = Message(text="texting", user_id=self.uid)

        msg2 = Message(text="warbling", user_id=self.uid)

        user = User.signup("testtest", "email@email.com", "pass", None)
        uid = 9877
        user.id = uid
        db.session.add_all([msg, msg2, user])
        db.session.commit()

        user.likes.append(msg)

        db.session.commit()

        liking = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(liking), 1)
        self.assertEqual(liking[0].message_id, msg.id)
        self.assertNotEqual(liking[0].message_id, msg2.id)

       