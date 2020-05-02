"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 4567
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
        
    def test_add_no_session(self):
        with self.client as client:
            resp = client.post("/messages/new", data={"text": "hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_invalid_user(self):
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = 90909

            resp = client.post("/messages/new", data={"text": "hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_show_msg(self):
        msg = Message(id=123, text="testing out", user_id=self.testuser_id)

        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(123)
            
            resp = client.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))
    
    def test_show_invalid_message(self):
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = client.get("/messages/295875356")

            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):

        msg = Message(
            id=123, text="testing out", user_id=self.testuser_id
        )

        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        resp = client.post("/messages/123/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        m = Message.query.get(123)
        self.assertIsNone(m)

    def test_unauthorized_message_delete(self):

        # A second user will try to delete the message
        user2 = User.signup(username="unauth", email="you@gmail.com", password="pass123", image_url=None)
        user2.id = 543

        #Message is written by testuser
        m = Message(
            id=15678,
            text="try to delete",
            user_id=self.testuser_id
        )

        db.session.add_all([user2, m])
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = 543
                
            resp = client.post("/messages/15678/delete", follow_redirects=True) 
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            m = Message.query.get(15678)
            self.assertIsNotNone(m)
    
    def test_no_authentication_delete_msg(self):
        m = Message(
            id=15678,
            text="try to delete",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as client:
            resp = client.post("/messages/15678/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(15678)
            self.assertIsNotNone(m)






