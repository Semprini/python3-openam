import unittest

try:
    # Check if openam module has been added to site-packages
    import openam
except ImportError:
    # If not the parent directory to this file should have the openam package so add that to the path
    import os,sys,inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir) 

from openam.context import Context, Identity, ServerInfo
from openam.user import User
    
class OpenAMTestCase(unittest.TestCase):
    def __init__(self, testname, url, username, password):
        super(OpenAMTestCase, self).__init__(testname)
        self.url = url
        self.username = username
        self.password = password


class TestServer(OpenAMTestCase):        
    "Tests the connection to the server and tests server info/cookies"
    def setUp(self):
            self.context = Context(self.url)

    def test_connection(self):
        self.assertTrue(len(self.context.cookie_name) > 0)

    def test_info(self):
        self.assertIsInstance(self.context.server_info, ServerInfo)


class TestUser(OpenAMTestCase):
    "Tests that the admin user can login and out"
    def setUp(self):
            self.context = Context(self.url)
            self.user = None

    def tearDown(self):
        if self.user:
            if self.user.is_valid():
                self.user.logout()
        
    def test_login(self):
        self.user=User(self.context, self.username, self.password)
        self.assertTrue(self.user.is_valid())
        self.assertIsInstance( self.user.identity, Identity )
        self.user.logout()
        self.assertFalse(self.user.is_valid())
        
    def test_callback_login(self):
        self.user=User(self.context)
        self.user.callback_login(NameCallback=self.username, PasswordCallback=self.password )
        self.assertTrue(self.user.is_valid())
        self.user.logout()
        self.assertFalse(self.user.is_valid())

    def test_change_password(self):
        self.user=User(self.context, self.username, self.password)
        self.assertTrue(self.user.is_valid())

        self.user.change_password('newpassword')
        self.user.logout()

        self.user=User(self.context, self.username, 'newpassword')
        self.assertTrue(self.user.is_valid())

        self.user.change_password(self.password)
        self.user.logout()


class TestIdentityCreate(OpenAMTestCase):
    "Tests that the admin user perform create and delete operations on identities"
    def setUp(self):
            self.context = Context(self.url)
            self.user=User(self.context, self.username, self.password)

    def tearDown(self):
        if self.user:
            if self.user.is_valid():
                self.user.logout()

    def test_create_identity(self):
        self.identity = self.context.create_identity( self.user.tokenId, 'testuser', 'password', 'test@test.com' )
        self.assertIsInstance( self.identity, Identity )
        self.assertTrue( self.user.tokenId, self.context.delete_identity() )


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test OpenAM interfaces')
    parser.add_argument('url', nargs='?', type=str, help='URL of running OpenAM server (eg. http://myserver.com:8080/openam)')
    parser.add_argument('username', nargs='?', type=str, help='Username of an admin')
    parser.add_argument('password', nargs='?', type=str, help='Password of the admin user')
    args = parser.parse_args()

    if not args.url:
        args.url = input("What is the URL of your running OpenAM server?:")
    if not args.username:
        args.username = input("What is a username of an admin?:")
    if not args.password:
        args.password = input("What is the password of the admin user?:")

    suite = unittest.TestSuite()
    suite.addTest(TestServer("test_connection", args.url, args.username, args.password))
    suite.addTest(TestServer("test_info", args.url, args.username, args.password))
    suite.addTest(TestUser("test_login", args.url, args.username, args.password))
    suite.addTest(TestUser("test_callback_login", args.url, args.username, args.password))
    suite.addTest(TestUser("test_change_password", args.url, args.username, args.password))
    #suite.addTest(TestIdentityCreate("test_create_identity", args.url, args.username, args.password))

    unittest.TextTestRunner(verbosity=2).run(suite)
    
