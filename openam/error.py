# -*- coding: utf-8 -*-

import json

# Exceptions
class OpenAMError(Exception):
    def __init__(self, message, code=None, data=None, content_type=None):
        self.code = code
        self.data = data
        self.content_type = content_type

        if self.content_type:
            if 'application/json' in self.content_type:
                self.data = json.loads(self.data)
        if self.data:
            message = message + " Details: %s"%self.data

        super(OpenAMError, self).__init__(message)

        
class AuthenticationFailure(OpenAMError):
    pass
