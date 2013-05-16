# contains elevenrox logics
from ConfigParser   import SafeConfigParser
from jsonrpcerror   import *
from elevenroxerror import *
from utils          import *
from random         import random
from hashlib        import md5
from datetime       import datetime, timedelta

#from jsonrpc import JsonRPC
class ElevenRox():

	def __init__(self):

		# read config
		self.config = self._read_config()

		self.orgname = self.config.get('app','orgname')
		self.session_cookie = self.config.get('cookie','session_name')

		self.http_utils = HTTPUtils(self.config)
		self.xml_utils  = XMLUtils(self.config)
		self.xlate      = XlateUtils()
		self.sec_utils  = SecUtils(self.config)

		# define some stuff for error codes / handling
		# these are present in error strings where we've failed to authenticate
		self.err_auth_subs = ['timed','permission','expired']
		self.err_sdk_subs  = ['Tenroxsdk']

	#
	# Private functions
	#

	def _read_config(self):

		defaults = {
			'proxy_enabled': 'False',
			'base_url': 'https://openbet.tenrox.net',
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
	# This proc will always result in an exception being raised,
	# unless raise_def is passed through as false
	#
	# At least one of the below should be supplied, if both
	# are given, soup will be used
	#
	# html_str  - html string (will be parsed by soup)
	# soup      - pre-parsed soup
	# def_err   - default error to be printed if we dont find one
	# raise_def - raise an error even if you don't know what it is
	def _raise_err_from_html(
		self,
		html_str=None,
		soup=None,
		def_err='Unknown Error',
		raise_def=True
	):

		if soup is not None:
			html = soup
		elif html_str is not None:
			html = HTMLUtils(html_str)
		else:
			raise ElevenRoxError('Need to supply either html_str or soup')

		err = html.get_error_message(def_err)

		# auth error / session
		for sub in self.err_auth_subs:
			if sub in err:
				raise ElevenRoxAuthError(err)

		if def_err != err or raise_def:

			# not sure what the error is?
			raise ElevenRoxTRParseError(err)

	# Raise an exception from xml returned by tenrox
	# This proc will always result in an exception being raised,
	# unless raise_def is passed in as false
	#
	# At least one of the below should be supplied, if both
	# are given, soup will be used
	#
	# xml_str   - html xml (will be parsed by element tree)
	# def_err   - default error to be printed if we dont find one
	# raise_def - raise an error even if you don't know what it is
	def _raise_err_from_xml(
		self,
		xml_str=None,
		def_err='Unknown Error',
		raise_def=True
	):

		err = self.xml_utils.get_error_message(xml_str,def_err)

		# auth error / session
		for sub in self.err_sdk_subs:
			if sub in err:
				raise ElevenRoxSDKError(err)

		if def_err != err or raise_def:
			# not sure what the error is?
			raise ElevenRoxTRParseError(err)

	# Encrypt a session token
	def _get_token(
		self,
		username,
		password,
		user_id,
		session_id
	):
		token = '{0}|{1}|{2}|{3}'.format(
			username,
			password,
			user_id,
			session_id
		)

		return self.sec_utils.encrypt(token)

	# parse a token
	# return {'username': username, 'password': password, 'user_id: user_id, 'session_id': session_id}
	# or None if we cannot parse the token for some reason
	def _parse_token(self, token):

		token = self.sec_utils.decrypt(token)
		spl = token.rsplit('|')

		if len(spl) != 4:
			raise JsonRPCInvalidParamsError('Failed to parse token' + token)

		username   = spl[0]
		password   = spl[1]
		user_id    = spl[2]
		session_id = spl[3]

		return {
			'username': username,
			'password': password,
			'user_id': user_id,
			'session_id': session_id
		}

	# Encrypt a timesheet token
	def _get_timesheet_token(
		self,
		timesheet_id,
		start_date,
		end_date,
		template_id,
		template_name,
	):

		token = '{0}|{1}|{2}|{3}|{4}'.format(
			timesheet_id,
			start_date,
			end_date,
			template_id,
			template_name
		)

		return self.sec_utils.encrypt(token)

	# parse a timesheet token
	# return {
	#    'timesheet_id': timesheet_id,
	#    'start_date': start_date,
	#    'end_date': end_date,
	#    'template_id': template_id,
	#    'template_name', template_name
	# }
	# or None if we cannot parse the token for some reason
	def _parse_timesheet_token(self, token):

		token = self.sec_utils.decrypt(token)
		spl = token.rsplit('|')

		if len(spl) != 5:
			raise JsonRPCInvalidParamsError('Failed to parse timesheet token' + token)

		timesheet_id = spl[0]
		start_date = spl[1]
		end_date = spl[2]
		template_uid = spl[3]
		template_name = spl[4]

		return {
			'timesheet_id': timesheet_id,
			'start_date': start_date,
			'end_date': end_date,
			'template_id': template_uid,
			'template_name': template_name
		}

	# Return the latest timesheet start date (last monday) in MM/DD/YYYY
	def _get_current_start_date(self):

		today = datetime.today()
		mon   = today - timedelta(today.weekday())

		return '{0}/{1}/{2}'.format(mon.month, mon.day, mon.year)

	# Add the random number and pageKey to a parameter string
	# based on GetPageKey from common1.js
	def _set_page_key(self, url, user_id):

		# the user_id is appended to the url params for security
		sec_append = '*{0}*'.format(user_id)

		# add random onto the URL
		url += '&r={0}'.format(str(random()))

		# need to get the params on their own
		spl = url.rsplit('?')
		params = spl[1]

		# generate the md5
		page_key = md5(params + sec_append).hexdigest()

		return url + '&pageKey={0}'.format(page_key)

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

		token = None

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

		try:
			self._check_tenrox_params(login_params)
		except(ElevenRoxTRParseError) as e:
			# has the password expired? This is a hack, but the expiry page
			# isn't valid HTML
			if resp_str.find('Your password has expired'):
				raise ElevenRoxAuthError('Password expired')

			# if we don't find anything in the html, at least we can say what was missing
			def_err = '%s' % e.data

			# try anything else, standard error? This will raise something
			self._raise_err_from_html(soup=html,def_err=def_err)

		token = self._get_token(
			username,
			password,
			login_params['user_id'],
			login_params['session_id']
		)

		result = {
			'user_id': login_params['user_id'],
			'username': username,
			'token': token
		}

		return result

	# get the time user's timesheet assignments
	#
	# start_date - if not supplied, this week's timesheet will be returned
	def get_time(self, start_date=None, token=None):

		# sanity check args
		if token is None:
			raise JsonRPCInvalidParamsError('Token not supplied')

		#
		# Looks like we may need to get the current time sheet before it'll let us get the old ones?
		#

		if start_date is None:
			start_date = self._get_current_start_date()
		else:
			start_date = self.xlate.convert_tenrox_date(start_date)

		token_dict = self._parse_token(token)

		url = self.config.get('get_time','url')

		url += '?UserUId={0}&SD={1}'.format(
			token_dict['user_id'],
			start_date,
		)

		url = self._set_page_key(url, token_dict['user_id'])

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
			self._raise_err_from_html(html_str=resp_str)

		# make sure we're still logged in
		session_id = self._check_session(resp['cookie_jar'])

		# pull the start and end date out of the response
		# split the response down for perf
		html = HTMLUtils(
			self._split_from_config(resp_str, 'get_time_date')
		)

		# grab the dates
		dates = html.get_date_range()

		# get the page key
		html = HTMLUtils(
			self._split_from_config(resp_str, 'get_time_pk')
		)

		# now we need to try to get the raw XML out of the response
		# the bit we're interested in is between <Timesheet></Timesheet>
		# which is on line 240
		spl = self._split_from_config(resp_str, 'get_time_xml')

		# Timesheet Layout
		try:
			start = spl.index('<TimesheetLayout ')
			end   = spl.index('</TimesheetLayout>') + 18
		except ValueError, e:
			error = 'Couldn\'t find timesheet layout XML'
			raise ElevenRoxTRParseError(error)

		timesheet_layout_xml = spl[start:end]

		# Timesheet:
		try:
			start = spl.index('<Timesheet ')
			end   = spl.index('</Timesheet>') + 12
		except ValueError, e:
			error = 'Couldn\'t find timesheet XML'
			raise ElevenRoxTRParseError(error)

		timesheet_xml = spl[start:end]

		timesheet_layout = self.xml_utils.parse_timesheet_layout(timesheet_layout_xml)
		timesheet        = self.xml_utils.parse_timesheet(timesheet_xml)

		# add the dates to the timesheet dict
		timesheet['start_date'] = dates[0]
		timesheet['end_date']   = dates[1]

		token = self._get_token(
			token_dict['username'],
			token_dict['password'],
			token_dict['user_id'],
			session_id
		)

		# This is a bit of a hack at the moment, but I don't understand
		# why need to pass these variables around at all really. We're
		# Just taking these from the first element in the timeentries return

		timesheet_token = self._get_timesheet_token(
			timesheet['uid'],
			timesheet['start_date'],
			timesheet['end_date'],
			timesheet_layout['id'],
			timesheet_layout['name']
		)

		result = {
			'token': token,
			'timesheet_token': timesheet_token,
			'timesheet': timesheet
		}

		return result

	# set a single timesheet entry
	#
	# assignment_id   - (ASSIGNMENTATRIBUID)
	# entry_date      - DD/MM/YYYY
	# time            - the time to set (seconds). Negative subtracts time
	# timesheet_token - a token representing the current timesheet
	# token           - session / auth
	# ?entry_id?      - 0 if there are no entries yet for this assignment on this date
	#                   or the ENTRYUID if modifying an existing entry
	# ?overtime?      - boolean (false)
	# ?double_ot?     - boolean (false)
	# ?is_etc?        - boolean (false) - dunno what this means yet
	# ?enst?          - boolean (false) - dunno what this means yet
	#
	def set_time(
		self,
		assignment_id=None,
		entry_date=None,
		time=None,
		timesheet_token=None,
		token=None,
		entry_id="0",
		overtime=False,
		double_ot=False,
		is_etc=False,
		enst=False
	):

		required = [
			'assignment_id',
			'entry_date',
			'time',
			'timesheet_token',
			'token'
		]

		# check mandatory params
		for param in required:
			if eval(param) is None or eval(param) == '':
				raise JsonRPCInvalidParamsError('{0} not supplied'.format(param))

		token_dict    = self._parse_token(token)
		ts_token_dict = self._parse_timesheet_token(timesheet_token)

		url = self.config.get('set_time','url')

		# we need the TAjax param to tell the server not to give us the entire page bsck
		t_ajax = self.config.get('set_time','t_ajax')
		url += '?TAjax={0}'.format(t_ajax)
		url = self._set_page_key(url, token_dict['user_id'])

		# set the session cookie
		cookie = self.http_utils.set_cookie(
			self.session_cookie,
			token_dict['session_id']
		)

		xml_params = {
			'timesheet_id': ts_token_dict['timesheet_id'],
			'start_date': self.xlate.to_tenrox_date(ts_token_dict['start_date']),
			'end_date': self.xlate.to_tenrox_date(ts_token_dict['end_date']),
			'user_id': token_dict['user_id'],
			'template_id': ts_token_dict['template_id'],
			'template_name': ts_token_dict['template_name'],
			'assignment_id': assignment_id,
			'entry_id': entry_id,
			'entry_date': self.xlate.to_tenrox_date(entry_date),
			'entry_time': time,
			'overtime': overtime,
			'double_ot': double_ot,
			'is_etc': is_etc,
			'enst': enst
		}

		# get the XML we're sending through in the POST
		xml = self.xml_utils.build_set_time_xml(**xml_params)

		# not sending the data through until we've got auth
		resp = self.http_utils.do_req(
			url, data=xml, url_encode=False, cookies=[cookie]
		)

		resp_str = resp['response'].read()

		# We get a timesheet back in response, parse it.
		try:
			# Note the start tag is closed here
			start = resp_str.index('<Timesheet>')
			end   = resp_str.index('</Timesheet>') + 12
		except ValueError, e:
			error = 'Couldn\'t find timesheet XML'

			# we might have got some xml back showing an error (which wasn't the timesheet xml)
			self._raise_err_from_xml(xml_str=resp_str,def_err=error,raise_def=False)

			# see if we can get anything a bit more helpful out of the response
			self._raise_err_from_html(html_str=resp_str,def_err=error)

		timesheet_xml = resp_str[start:end]
		timesheet     = self.xml_utils.parse_timesheet(timesheet_xml)

		# we pass the initial tokens back through, as we're dealing in xml
		result = {
			'token': token,
			'timesheet_token': timesheet_token,
			'timesheet': timesheet
		}

		return result

	#
	# Skeleton - TODO
	#
	def complete(
		self,
		token=None,
		timesheet_token=None
	):

		required = [
			token,
			timesheet_token
		]

		for param in required:
			if param is None:
				raise JsonRPCInvalidParamsError('{0} not supplied'.format(param))

		result = {
			'token': token
		}

		return result


