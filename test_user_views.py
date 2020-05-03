"""User View Tests"""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

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

class UserViewTestCase(TestCase):
    """Test views for users"""

    def setUp(self):
        """Create test client, add sample data"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1234
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("hello", "test1@gmail.com", "pass12", None)
        self.u1_id = 987
        self.u1.id = self.u1_id
        self.u2 = User.signup("bonjour", "test2@gmail.com", "pass12", None)
        self.u2_id = 456
        self.u2.id = self.u2_id
        self.u3 = User.signup("bye", "test3@gmail.com", "pass12", None)
        self.u3_id = 6745
        self.u3.id = self.u3_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_list(self):
        with self.client as client:
            resp = client.get('/users')

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@hello", str(resp.data))
            self.assertIn("@bonjour", str(resp.data))
            self.assertIn("@bye", str(resp.data))
    
    def test_user_search(self):
        with self.client as client:
            resp = client.get('/users?q=test')

            self.assertIn("@testuser", str(resp.data))
            self.assertNotIn("@hello", str(resp.data))
            self.assertNotIn("@bonjour", str(resp.data))
            self.assertNotIn("@bye", str(resp.data))

    def test_user_show(self):
        with self.client as client:
            resp = client.get(f'/users/{self.testuser_id}')

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))

    def setup_likes(self):
        # msg1 = Message(text="something here", user_id=self.testuser_id)
        # msg2 = Message(text="something else here", user_id=self.testuser_id)
        msg3 = Message(id=1357, text="something here again", user_id=self.u1_id)

        db.session.add(msg3)
        db.session.commit()

        like1 = Likes(user_id=self.testuser_id, message_id=1357)

        db.session.add(like1)
        db.session.commit()

    def test_add_like(self):
        self.setup_likes()
        with self.client as c:
            resp = c.post("/messages/1357/add_like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1357).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        self.setup_likes()
        #check if testuser already likes message 1357
        message = Message.query.get(1357)
        currently_likes = self.testuser.likes_message(message)

        self.assertTrue(currently_likes)
        # # remove like
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
        
            resp = c.post("/messages/1357/remove_like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            likes = Likes.query.filter(Likes.message_id==1357).all()
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        self.setup_likes()

        message = Message.query.get(1357)

        with self.client as c:
            resp = c.post(f"/messages/{message.id}/add_like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()
    
    def test_show_who_user_is_following(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@hello", str(resp.data))
            self.assertIn("@bonjour", str(resp.data))
            self.assertNotIn("@bye", str(resp.data))


    def test_show_who_followed_user(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get(f"/users/{self.testuser_id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            self.assertNotIn("@bonjour", str(resp.data))
            self.assertNotIn("@bye", str(resp.data))
    
    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@bonjour", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@bonjour", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))


    