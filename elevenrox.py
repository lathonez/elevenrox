# contains elevenrox logics
from ConfigParser   import SafeConfigParser
from jsonrpcerror   import *
from elevenroxerror import *
from utils          import *

#from jsonrpc import JsonRPC
class ElevenRox():

	def __init__(self):

		# read config
		self.config = self._read_config()

		self.orgname = self.config.get('app','orgname')
		self.session_cookie = self.config.get('cookie','session_name')

		self.http_utils = HTTPUtils(self.config)
		self.xml_utils  = XMLUtils(self.config)

		# define some stuff for error codes / handling
		# these are present in error strings where we've failed to authenticate
		self.err_auth_subs = ['timed','permission']

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

	# formats the url from config correctly for tenrox
	# - adds orgname
	def _format_tenrox_url(self, url):

		url += '?orgname={0}'.format(self.orgname)

		return url


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

	# returns session_id from the session coookie, or throws
	# an exception if the session cookie is missing
	def _check_session(self, cookie_jar):

		# we're after the ASP session cookie
		session_id = self.http_utils.get_cookie(cookie_jar, self.session_cookie)

		if session_id is None:
			raise ElevenRoxAuthError('Couldn\'t find ASP.NET_SessionId cookie in tenrox response')

		return session_id

	# Raise an exception from html returned by tenrox
	def _raise_err_from_html(self,html):

		print html

		html = HTMLUtils(html)
		err = html.get_error_message()

		# auth error / session
		for sub in self.err_auth_subs:
			if sub in err:
				raise ElevenRoxAuthError(err)

		# not sure what the error is?
		raise ElevenRoxTRParseError(err)

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

		resp     = self.http_utils.do_req(url, request_params)
		resp_str = resp['response'].read()

		html = HTMLUtils(resp_str)

		# search for the invalid username password message
		if not html.is_logged_in():
			raise ElevenRoxAuthError('Invalid username or password')

		# this will blow up if we're not logged in
		login_params['session_id'] = self._check_session(resp['cookie_jar'])

		# the only other intersting info we get back is the uid, may as well return it
		login_params['user_id'] = html.get_user_id()

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
		cookie = self.http_utils.set_cookie(
			self.session_cookie,
			token_dict['session_id']
		)

		resp     = self.http_utils.do_req(url, cookies=[cookie])
		resp_str = resp['response'].read()

		# we can quickly detect an error form a short response
		if len(resp_str) < self.config.getint('get_time','err_max'):
			# blow up
			self._raise_err_from_html(resp_str)

		# make sure we're still logged in
		session_id = self._check_session(resp['cookie_jar'])

		# now we need to try to get the raw XML out of the response
		# the bit we're interested in is between <Timesheet></Timesheet>
		# which is on line 240
		spl = self._split_from_config(resp_str, 'get_time_xml')

		try:
			start = spl.index('<Timesheet ')
			end   = spl.index('</Timesheet>') + 12
		except ValueError, e:
			error = 'Couldn\'t find timesheet XML'
			raise ElevenRoxTRParseError(error)

		raw_xml = spl[start:end]

#		print raw_xml

		timesheet = self.xml_utils.parse_timesheet(raw_xml)

		token = self._get_token(
			token_dict['username'],
			token_dict['password'],
			session_id
		)

		result = {
			'token': token,
			'timesheet': timesheet
		}

		return result

