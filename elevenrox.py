# contains elevenrox logics
import urllib, urllib2, cookielib

from cookielib import Cookie, CookieJar

from ConfigParser import SafeConfigParser

from jsonrpcerror import *

#from jsonrpc import JsonRPC
class ElevenRox():

	def __init__(self):

		# read config
		self.config = self._read_config()

		# setup proxy if necessary
		self.proxy = self._get_proxy()

		self.orgname = self.config.get('app','orgname')
		self.session_cookie = self.config.get('cookie','session_name')

	#
	# Private functions
	#

	def _read_config(self):

		defaults = {
			'proxy_enabled': 'False',
			'base_url': 'https://openbet.tenroxhosting.com',
			'orgname': 'OpenBet'
		}

		config = SafeConfigParser(defaults)
		config.read('elevenrox.cfg')

		return config

	# returns a proxy instance that is used for the lifetime of this instance
	def _get_proxy(self):

		if not self.config.getboolean('app','proxy_enabled'):
			return False

		url  = self.config.get('app','proxy_url')

		print 'Running on proxy', url

		proxy = urllib2.ProxyHandler({
			'http': url,
			'https': url,
			'debuglevel': 1
		})

		return proxy

	# helper fn returns a cookiejar from the opener's cookieprocessor
	# or None if one doesn't exist
	def _get_cookie_jar(self, opener):

		for handler in opener.handlers:
			if isinstance(handler,urllib2.HTTPCookieProcessor):
				return handler.cookiejar

		return None

	# returns an opener object that can be used for a single request
	def _get_opener(self):

		# overload http handlers for debugging
		debug = self.config.get('app','http_debug_level')
		http  = urllib2.HTTPHandler(debuglevel=debug)
		https = urllib2.HTTPSHandler(debuglevel=debug)

		# handle cookies across 302
		cookie_jar = cookielib.CookieJar()
		cookie = urllib2.HTTPCookieProcessor(cookie_jar)

		handlers = [http, https, cookie]

		# add the proxy to the handlers we're using if necessary
		if self.proxy is not None:
			handlers.append(self.proxy)

		opener = urllib2.build_opener(*handlers)

		return opener

	# formats the url from config correctly for tenrox
	# - adds orgname
	def _format_tenrox_url(self, url):

		url += '?orgname={0}'.format(self.orgname)

		return url

	# wrap urllib to sort out the openers, handle exceptions etc
	def _do_req(self, opener, url, data=None):

		try:
			resp   = opener.open(url, data)
		except urllib2.HTTPError, e:
			error = 'Tenrox failed to process the request. HTTP error code: {0}'.format(e.code)
			raise ElevenRoxHTTPError(error)
		except urllib2.URLError, e:
			error = 'Couldn\'t connect to tenrox. Reason: {0}'.format(e.reason)
			raise ElevenRoxHTTPError(error)

		return resp

	# check whether or not the user is logged in based on the response body
	def _is_logged_in(self, html):

		spl = self._split_from_config(html, 'invalid_login')

		# this is pretty hacky at the moment, but should be quick
		if 'Invalid User Id or Password' in spl:
			return False
		else:
			return True

	def _get_user_id(self, html):

		start_string = 'userUniqueID='
		end_string = '&userName'

		# the uid should be somewhere in here
		split = self._split_from_config(html, 'user_id')
		start = split.find(start_string) + start_string.__len__()
		end   = split.find(end_string)

		return split[start:end]

	# helper returns [start,end] based on the config item
	def _split_from_config(self, string, config):

		config = self.config.get('splits',config)
		spl = config.partition(':')

		start = None if spl[0] == '' else int(spl[0])
		end   = None if spl[2] == '' else int(spl[2])

		return string[start:end]

	# santiy check params coming out of a tenrox response
	def _check_tenrox_params(self, params):

		none_list = []
		for key in params.keys():
			if params[key] is None:
				none_list.append(key)

		if len(none_list):
			err_data = 'Items missing from response: '
			err_list = ', '.join(none_list)
			raise ElevenRoxTRParseError(err_data + err_list)
			return False

		return True

	# TODO: this, properly
	def _get_token(self, username, password, session_id):

		return '{0}|{1}|{2}'.format(username, password, session_id)

	# parse a token
	# return {'username': username, 'password': password, 'session_id': session_id}
	# or None if we cannot parse the token for some reason
	def _parse_token(self, token):

		spl = token.rsplit('|')

		if len(spl) != 3:
			raise JsonRPCInvalidParamsError('Failed to parse token' + token)

		username = spl[0]
		password = spl[1]
		session_id = spl[2]

		return {
			'username': username,
			'password': password,
			'session_id': session_id
		}

	# return the value of a cookie out of the given cookie jar,
	# or none if the cookie doesn't exist
	def _get_cookie(self, cookie_jar, cookie_name):

		cookie_val = None

		for cookie in cookie_jar:
			if cookie.name == cookie_name:
				cookie_val = cookie.value

		return cookie_val

	# creates a cookie object with the given n,v or updates one if passed in
	def _set_cookie(self, name, value, secure=False, expires=None):

		cookie_params = {
			'version': None,
			'name': name,
			'value': value,
			'port': '80',
			'port_specified': '80',
			'domain': self.config.get('cookie','cookie_domain'),
			'domain_specified': None,
			'domain_initial_dot': None,
			'path': '/',
			'path_specified': None,
			'secure': secure,
			'expires': expires,
			'discard': False,
			'comment': 'ElevenRox Cookie',
			'comment_url': None,
			'rest': None
		}

		cookie = Cookie(**cookie_params)

		return cookie

	#
	# Public functions - by definition these are available to the API
	#

	# test function
	def echo(self, msg1=None, msg2=None):

		msg = ''

		if msg1 is not None:
			msg += msg1

		if msg2 is not None:
			msg += msg2

		return msg

	def login(self, username=None, password=None):

		# sanity check args
		if username is None or password is None:
			raise JsonRPCInvalidParamsError('Either username or password not supplied')

		print 'Attempting login with username: {0}, password: {1}'.format(username,password)

		logged_in = False
		token     = None

		# we need all these from the response
		login_params = {
			'session_id': None,
			'user_id': None
		}

		url = self.config.get('login','url')
		url = self._format_tenrox_url(url)

		viewstate = self.config.get('login','viewstate')

		request_params = {
			'E_UserName': username,
			'E_Password': password,
			'__VIEWSTATE': viewstate
		}

		data = urllib.urlencode(request_params)

		opener   = self._get_opener()
		resp     = self._do_req(opener, url, data)
		resp_str = resp.read()

		# search for the invalid username password message
		if not self._is_logged_in(resp_str):
			raise ElevenRoxAuthError('Invalid username or password')

		cookie_jar = self._get_cookie_jar(opener)

		# we're after the ASP session cookie
		login_params['session_id'] = self._get_cookie(cookie_jar, self.session_cookie)

		if login_params['session_id'] is not None:
			logged_in = True

		# No point going on without a session_id
		if not logged_in:
			raise ElevenRoxAuthError('Couldn\'t find ASP.NET_SessionId cookie in tenrox response')

		# the only other intersting info we get back is the uid, may as well return it
		login_params['user_id'] = self._get_user_id(resp_str)

		self._check_tenrox_params(login_params)

		token = self._get_token(
			username,
			password,
			login_params['session_id']
		)

		result = {
			'user_id': login_params['user_id'],
			'username': username,
			'token': token
		}

		return result

	# get the time user's timesheet assignments
	def get_time(self, token=None):

		# sanity check args
		if token is None:
			raise JsonRPCInvalidParamsError('Token not supplied')

		token_dict = self._parse_token(token)

		url = self.config.get('get_time','url')
	#	url = self._format_tenrox_url(url)
	#	url += '?r=0.847878836490157&DotNet=1&pageKey=ff34a30b5d4820c9a000dbd95c3c17b0'

		req_key  = self.config.get('get_time','req_key')
		dot_net  = self.config.get('get_time','dot_net')
		page_key = self.config.get('get_time','page_key')

		# for some reason, though these are static, these vars have to be sent through
		# as part of the URL request string, in this exact order, or we get auth failure
		url += '?r={0}&DotNet={1}&pageKey={2}'.format(
			req_key,
			dot_net,
			page_key
		)

		# set the session cookie
		cookie = self._set_cookie(
			self.session_cookie,
			token_dict['session_id']
		)

		opener     = self._get_opener()
		cookie_jar = self._get_cookie_jar(opener)
		cookie_jar.set_cookie(cookie)

		resp     = self._do_req(opener, url)
		resp_str = resp.read()

		print resp_str

		result = {
			'status': 'OK'
		}

		return result

# base exception class for all elevenrox exceptions
# all extending classes must have a code, message and data
class ElevenRoxError(Exception):
	pass

# exception raised for any communication errors with the tenrox server
class ElevenRoxHTTPError(ElevenRoxError):

	def __init__(self, data):
		self.code    = -32000
		self.message = 'Unable to communicate with tenrox'
		self.data    = data

# problem logging in / session expiry
class ElevenRoxAuthError(ElevenRoxError):

	def __init__(self, data):
		self.code    = -32001
		self.message = 'Unable to authenticate with tenrox'
		self.data    = data

# failed to parse the response from tenrox for some reason
class ElevenRoxTRParseError(ElevenRoxError):

	def __init__(self, data):
		self.code    = -32001
		self.message = 'Failed to parse server response from tenrox'
		self.data    = data

