# -*- coding: utf-8 -*-

# Python 3 interface to OpenAM REST API
#
# Code borrowed and reworked from django-openam by nsb
# https://github.com/acgray/django-openam
#

import urllib, urllib.error, urllib.request
import ssl
import json
from urllib.parse import urlparse, urljoin, urlencode
from openam.error import OpenAMError

#SSL Certificate checking
SSL_PROTOCOL = ssl.PROTOCOL_SSLv23  # or other options like ssl.PROTOCOL_TLSv1
SSL_VERIFY_MODE = ssl.CERT_NONE     # CERT_REQUIRED for production, CERT_NONE when there is a self signed cert on the openam server
SSL_VERIFY_FLAGS = 0

# REST API URIs
REST_OPENAM_COOKIE_NAME_FOR_TOKEN = '/identity/getCookieNameForToken'
REST_OPENAM_COOKIE_NAMES_TO_FORWARD = '/identity/getCookieNamesToForward'
REST_OPENAM_COOKIE_DOMAINS = '/json/serverinfo/cookieDomains'
REST_OPENAM_SERVER_INFO = '/json/serverinfo/*'

# Exports
__all__ = ('Context', 'Identity','ServerInfo')



class DictObject(object):
    """
    Pass it a dict and now it's an object! Great for keeping variables!
    """

    def __init__(self, data=None):
        if data is None:
            data = {}
        self.__dict__.update(data)


class Identity(DictObject):
    """
    A dict container to make identity details keys available as attributes.
    """
    pass


class ServerInfo(DictObject):
    """
    A dict container to make server info keys available as attributes.
    """
    pass


class Context(object):

    """
    OpenAM RESTful Interface
    """

    def __init__(self, openam_url='', realm=None, timeout=5):
        """
        @param openam_url: the URL to the OpenAM server
        @param timeout: HTTP requests timeout in seconds
        """
        if not openam_url:
            raise ValueError(
                'This interface needs an OpenAM URL to work!')

        self._server_info = None
        self._cookie_name = None
        self._cookie_domains = None
        self._cookie_names_to_forward = None
        self._openam_url = openam_url
        self._realm = realm
        self.__timeout = timeout

        self.authentications = []
        
        self._ssl_ctx = None
        if self._openam_url[:5].lower() == "https":
            self._ssl_ctx = ssl.SSLContext(SSL_PROTOCOL)
            self._ssl_ctx.verify_mode = SSL_VERIFY_MODE
            self._ssl_ctx.verify_flags = SSL_VERIFY_FLAGS

        
    @property
    def URL_LOGIN(self):
        if self._realm:
            return '/json/authenticate?realm={0}'.format(self._realm)
        else:
            return '/json/authenticate'

    @property
    def URL_LOGOUT(self):
        return '/json/sessions/?_action=logout'


    @property
    def URL_USERS(self):
        return '/json/users/'
        

    @property
    def server_info(self):
        if not self._server_info:
            json_data = self.REQ(REST_OPENAM_SERVER_INFO)
            self._server_info = ServerInfo(json.loads(json_data or '{}'))
        return self._server_info


    @property
    def cookie_name(self):
        if not self._cookie_name:
            self._cookie_name = self._get_cookie_name_for_token()
        return self._cookie_name


    @property
    def cookie_domains(self):
        if not self._cookie_domains:
            self._cookie_domains = self._get_cookie_domains()
        return self._cookie_domains

        
    @property
    def cookie_names_to_forward(self):
        if not self._cookie_names_to_forward:
            self._cookie_names_to_forward = self._get_cookie_names_to_forward()
        return self._cookie_names_to_forward


    def _get_cookie_domains(self):
        """
        Returns domain of the cookies.
        """
        json_data = self.REQ(REST_OPENAM_COOKIE_DOMAINS)

        return json.loads(json_data or '{}').get("domains")


    def _get_cookie_name_for_token(self):
        """
        Returns name of the token cookie that should be set on the client.
        """
        data = self.REQ(REST_OPENAM_COOKIE_NAME_FOR_TOKEN)

        return data.replace('string=','').strip('\n')

        
    def _get_cookie_names_to_forward(self):
        """
        Returns a list of cookie names required by the server. Accepts no arguments.
        """
        data = self.REQ(REST_OPENAM_COOKIE_NAMES_TO_FORWARD)

        return data.replace('string=','').split('\n')[:-1]


    def REQ(self, urlpath, params=None, headers={}, method=None):
        """
        Wrapper around http_request() to save keystrokes.
        """
        data, content_type = http_request(_get_full_url(self._openam_url, urlpath), params, headers, self.__timeout, method, self._ssl_ctx)

        return data

        
    def get_identity( self, tokenId, username ):
        """
        Returns an Identity object containing information about the specified user.
        The supplied authentication must have authorization to access the user.
        """
        headers = { self.cookie_name:tokenId,}
        json_data = self.REQ(self.URL_USERS + username, headers=headers)
        return Identity(json.loads(json_data or '{}'))


    def create_identity( self, tokenId, username, password, mail ):
        params = {'username':username,
                  'userpassword':password,
                  'mail':mail }
        headers = { self.cookie_name:tokenId,
                    'Content-Type': 'application/json' }
        json_data = self.REQ(self.URL_USERS + "?_action=create", params, headers)
        return Identity(json.loads(json_data or '{}'))

        
    def delete_identity( self, tokenId, username ):
        """
        Returns success or exception of identity deletion.
        The supplied authentication must have authorization to delete the identity.
        """
        headers = { self.cookie_name:tokenId,}
        json_data = self.REQ(self.URL_USERS + username, headers=headers, method="DELETE")
        return json.loads(json_data or '{}').get("success") == "true" or False
    
        
    
def _get_full_url(base_url, path):
    # Adding '/' at end if it doesn't have one
    processed_base_url = base_url if base_url[-1] == "/" else base_url + "/"
    # removing '/' from begining if there is one
    processed_path = path if path[0] != "/" else path[1:]

    return urljoin(processed_base_url, processed_path)


def http_request(url, values=None, headers={}, timeout=20, method=None, ssl_context=None):
    """
    Send an HTTP request (GET if no values, POST if values provided or method if provided) and attempt to return the response data.
    Values are encoded as utf-8. Response content is decoded based on content type in response header.
    Returns a tuple containing content, content type
    """

    if values != None:
        data = json.dumps(values)
        data = data.encode('utf-8')
    else:
        data=None
    req = urllib.request.Request(url, data, headers, method=method)
    try:
        if ssl_context:
            resp = urllib.request.urlopen(req, timeout=timeout, context=ssl_context)
        else:
            resp = urllib.request.urlopen(req, timeout=timeout)
        response_data = resp.read()

        # Check the encoding type of the content and decode
        charset = resp.headers.get_content_charset()
        if charset:
            response_data = response_data.decode(charset)
        content_type = resp.headers.get_content_type()

    # Exceptions raised for non 2XX response codes
    except urllib.error.HTTPError as error:
        response_data = error.read()
        charset = error.headers.get_content_charset()
        if charset:
            response_data = response_data.decode(charset)
        content_type = error.headers.get_content_type()
        
        if error.code == 401:           # Unauthorized
            raise OpenAMError('401 Unauthorised to access {0}'.format(url), 401, response_data, content_type) from error
        if 300 <= error.code <= 399:    # Redirection errors
            raise OpenAMError('{0} Redirection response ({1}) from {2}'.format(error.code, error.reason, url), error.code, response_data, content_type) from error
        if 400 <= error.code <= 499:    # Client errors
            raise OpenAMError('{0} Client error ({1}) from {2}.'.format(error.code, error.reason, url), error.code, response_data, content_type) from error
        if 500 <= error.code <= 599:    # Server errors
            raise OpenAMError('{0} Server error ({1}) from {2}'.format(error.code, error.reason, url), error.code, response_data, content_type) from error
    except urllib.error.URLError as error:
        # Could not contact server
        raise OpenAMError('Communication error when trying {0}. {1}'.format(url, error.reason)) from error

    return (response_data, content_type)
