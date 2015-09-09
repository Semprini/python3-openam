Python 3 interface to OpenAM REST Services
-----------------------------------

Code borrowed and reworked from:

 - [acgray: python-openam](https://github.com/acgray/python-openam)

This is a reworked python 3 rest interface to OpenAM using the updated API. Current OpenAM version is 12.0.0.

The tutorial for setting up an OpenAM server is here: https://backstage.forgerock.com/#!/docs/openam/12.0.0/getting-started. You can skip the Apache bit (procedure 1.2) - except for the development tools/build-essential

For REST Services documentation please see [Forgerock Use OpenAM RESTful Services](http://openam.forgerock.org/openam-documentation/openam-doc-source/doc/webhelp/dev-guide/chap-rest.html)

To test once you have a running OpenAM that you can log into from your browser:
cd /path/to/python3-openam-<branch or master>
python openam/tests.py http://my_openam_server:8080/openam amadmin password

To Install to site-packages:
python setup.py install

#### Example of getting server info:

    >>> from openam.context import Context
    >>> context = Context('https://example.com/openam')
    >>> print( context.server_info.__dict__ )
	{
	'referralsEnabled': 'false',
	'successfulUserRegistrationDestination': 'default''zeroPageLogin': {
		'allowedWithoutReferer': True,
		'enabled': False,
		'refererWhitelist': ['']
	},
	'FQDN': 'example.com',
	'protectedUserAttributes': [],
	'secureCookie': False,
	'socialImplementations': [],
	'lang': 'en',
	'selfRegistration': 'false',
	'cookieName': 'iPlanetDirectoryPro',
	'domains': ['example.com'],
	'forgotPassword': 'false'
}

#### Example simple login user:

    >>> from openam.context import Context
    >>> from openam.user import User
    >>> context = Context('https://example.com/openam')
    >>> user = User(context, 'amadmin', 'password')
	>>> user.is_valid()
	True
	>>> user.tokenId
	'AQIC5wM2LY4SfcweNyLHBlLVnXX5h0R...
	>>> user.logout()
	>>> user.is_valid()
	False
	
#### Example change password:

    >>> from openam.context import Context
    >>> from openam.user import User
    >>> context = Context('https://example.com/openam')
    >>> user = User(context, 'amadmin', 'password')
	>>> user.is_valid()
	True
	>>> user.change_password('newpassword')
	>>> user.logout()
    >>> user = User(context, 'amadmin', 'newpassword')
	>>> user.is_valid()
	True
