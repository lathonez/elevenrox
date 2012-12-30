# contains elevenrox logics
import cookielib, urllib, urllib2

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
	def _do_req(self, opener, url, data):

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

	# TODO: this
	def _get_token(self, username, password, session_id):

		return '{0}|{1}|{2}'.format(username, password, session_id)

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
		for cookie in cookie_jar:
			if cookie.name == 'ASP.NET_SessionId':
				login_params['session_id'] = cookie.value
				logged_in = True

		# No point going on without a session_id
		if not logged_in:
			raise ElevenRoxAuthError('Couldn\'t find ASP.NET_SessionId cookie tenrox response')

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

