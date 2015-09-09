# -*- coding: utf-8 -*-

# Python 3 interface to OpenAM REST API
#


import json
from openam.error import OpenAMError, AuthenticationFailure

# REST API URIs
REST_OPENAM_IS_TOKEN_VALID = '/json/sessions/'

# Exports
__all__ = ('User')


class User(object):
    def __init__(self, openam, username=None, password=None, ):
        self.openam = openam
        self.token = None
        self.username = username
        self.password = password
        self._identity = None
        self._callback = None

        if self.password:
            # If credentials supplied then do simple login
            self.login(self.username, self.password )
        else:
            # Ask server for list of callbacks
            self._callback = self.callback
            

    @property
    def identity(self):
        # Identity information for this authenticated user
        if self._identity:
            return self._identity
        self._identity = self.openam.get_identity(self.tokenId, self.username)
        return self.identity

    @property
    def tokenId(self):
        return self.token.get("tokenId")


    @property
    def callback(self):
        if not self._callback:
            params = {}
            headers = { 'Content-Type': 'application/json' }
            self._callback = json.loads(self.openam.REQ(self.openam.URL_LOGIN, params, headers))
            
        return self._callback

        
    def login(self, username, password):
        """
        Authenticate and add to active authentications list.
        """

        params = {}
        headers = { 'X-OpenAM-Username':username,
                    'X-OpenAM-Password':password,
                    'Content-Type': 'application/json'}

        try:
            data = self.openam.REQ(self.openam.URL_LOGIN, params, headers)
        except OpenAMError as error:
            if error.code == 401:
                raise AuthenticationFailure('Invalid Credentials for user "{0}".'.format(username), error.code) from error
            raise

        self.token = json.loads(data)
        self.openam.authentications.append(self)


    def callback_login(self, **kwargs ):
        """
        Authenticates using call back types specified in the callback request. Available types:
            ChoiceCallback
            ConfirmationCallback
            HiddenValueCallback
            HttpCallback
            LanguageCallback
            NameCallback
            PasswordCallback
            RedirectCallback
            ScriptTextOutputCallback
            TextInputCallback
            TextOutputCallback
            X509CertificateCallback
        """
        for key in kwargs.keys():
            if key=="NameCallback":
                self.username=kwargs[key]
            # Find the callback
            for cb in self.callback['callbacks']:
                if cb['type'] == key:
                    cb['input'][0]['value'] = kwargs[key]
                    break

        headers = { 'Content-Type': 'application/json', }
        try:
            data = self.openam.REQ(self.openam.URL_LOGIN, self.callback, headers)
        except OpenAMError as error:
            if error.code == 401:
                raise AuthenticationFailure('Invalid Credentials for user "{0}".'.format(username), error.code) from error
            raise

        self.token = json.loads(data)
        self.openam.authentications.append(self)

    
    def is_valid(self):
        """
        Validate a token. Returns a boolean.
        """
        if not self.token:
            return False
        params = {}
        headers = { 'Content-Type': 'application/json', }
        json_data = self.openam.REQ(REST_OPENAM_IS_TOKEN_VALID + self.tokenId + "?_action=validate", params, headers)

        return json.loads(json_data or '{}').get("valid") or False


    def logout(self):
        """
        Logout by revoking the token passed and remove authentication from active list
        """
        params = {}
        headers = { self.openam.cookie_name:self.tokenId,
                    'Content-Type': 'application/json'}
        self.openam.REQ(self.openam.URL_LOGOUT, params, headers)
        self.openam.authentications.remove(self)


    def change_password(self, new_password):
        params = {'currentpassword':self.password,
                  'userpassword':new_password,}
        headers = {  self.openam.cookie_name:self.tokenId,
                    'Content-Type': 'application/json'}

        try:
            data = self.openam.REQ(self.openam.URL_USERS + self.username + "?_action=changePassword", params, headers)
            self.password = new_password
        except OpenAMError as error:
            if error.code == 401:
                raise AuthenticationFailure('Invalid Credentials for user "{0}".'.format(username), error.code) from error
            raise        
    
