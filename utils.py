#
# Utility for parsing XML
#
import xml.etree.ElementTree as ET

class XMLUtils():

	def __init__(self):
		# nothing to do yet
		pass

	#
	# Private Functions
	#

	# parse the assignments contained in a timesheet
	#
	# as ElementTree.element representing the assignments
	# returns ??
	def _parse_assignments(self, assignments):

		assignments_arr = []

		for a in assignments:

			assignment = {
				'assignment_id': a.get('ASS_UID'),
				'name': a.get('ASS_NAME'),
				'start_date': a.get('STARTDATE'),
				'end_date': a.get('ENDDATE'),
				'has_time': a.get('HASTIME'),
				'is_non_working_time': a.get('ISNONWORKINGTIME'),
				'is_default': a.get('ISDEFAULT'),
				'task_id': a.get('TASK_UID'),
				'task_name': a.get('TASK_NAME'),
				'project_id': a.get('PROJECT_UID'),
				'project_name': a.get('PROJECT_NAME'),
				'project_complete': a.get('PCOMPLETE'),
				'client_id': a.get('CLIENT_UID'),
				'client_name': a.get('CLIENT_NAME'),
				'worktype_id': a.get('WORKTYPE_UID'),
				'worktype_name': a.get('WORKTYPE_NAME'),
				'manager_id': a.get('MGRUID'),
				'manager_name': '{0} {1}'.format(a.get('PMGRFN'),a.get('PMGRLN')),
				'manager_email': a.get('PMGRE')
			}

			assignments_arr.append(assignment)

		return assignments_arr

	#
	# Public Functions
	#

	# parse a timesheet XML object as returned by
	# get_time for example. As specified by tenrox.com/TimesheetTemplate.xsd
	#
	# timesheet - string containting the timesheet xml
	# returns ??
	def parse_timesheet(self, timesheet):

		# get the root <Timesheet> element
		root = ET.fromstring(timesheet)

		assignments = None

		for child in root:

			print child.tag,child.attrib

			if child.tag == 'Assignments':
				assignments = self._parse_assignments(child)

		return assignments


#
# Utility for parsing HTML
#
from bs4 import BeautifulSoup

# wrapper for BeautifulSoup with some helper fns for tenrox
class HTMLUtils():

	# html - html string you want to use with this instance
	#        of the parser
	def __init__(self, html):

		self.html = html
		self.soup = BeautifulSoup(html)

	# Returns a friendly (well formatted) string of the html
	# do_print - if True will also print to the console
	def prettify(self,do_print=False):

		pretty = self.soup.prettify()

		if do_print:
			print pretty

		return pretty

	def get_error_message(self):

		err_msg   = 'Unknown Error'
		err_div   = self.soup.select('#TDError')[0]
		err_child = None

		if len(err_div):
			# could either be a span or a div
			err_child = err_div.contents[0]

		if err_child is not None:
			err_msg = err_child.string

		return err_msg

	# check whether or not the user is logged in based on the response body
	def is_logged_in(self):

		err_span = self.soup.select('#ErrorMessage')

		if not len(err_span):
			return True

		err_string = err_span[0].string

		# just a bit of unnecesssary checking
		if 'Invalid User Id or Password' in err_string:
			return False

		# something's gone wrong, but we don't know what
		print 'WARNING: Unknown error whilst logging in,', err_string

		return False

	def get_user_id(self):

		# get the iframe with the session info
		iframe = self.soup.select('#Iframe3')

		if not len(iframe):
			return None

		# the user_id is contained in the keepalive (src) link in the iframe
		iframe_src = iframe[0]['src']

		start_string = 'userUniqueID='
		end_string = '&userName'

		try:
			# the uid should be somewhere in here
			start = iframe_src.find(start_string) + start_string.__len__()
			end   = iframe_src.find(end_string)
		except ValueError, e:
			return None

		return iframe_src[start:end]

#
# Utility for dealing with protocol stuff (openers, proxies, cookies)
#
import urllib, urllib2, cookielib

from cookielib       import Cookie, CookieJar
from ConfigParser    import SafeConfigParser
from elevenroxerror  import ElevenRoxHTTPError

class HTTPUtils():

	# config - pre parsed ConfigParser config file
	def __init__(self, config):

		self.config = config

		# setup proxy if necessary
		self.proxy = self._get_proxy()

	#
	# Prviate Functions
	#

	# helper fn returns a cookiejar from the opener's cookieprocessor
	# or None if one doesn't exist
	def _get_cookie_jar(self, opener):

		for handler in opener.handlers:
			if isinstance(handler,urllib2.HTTPCookieProcessor):
				return handler.cookiejar

		return None

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

	#
	# Public Functions
	#

	# return the value of a cookie out of the given cookie jar,
	# or none if the cookie doesn't exist
	def get_cookie(self, cookie_jar, cookie_name):

		cookie_val = None

		for cookie in cookie_jar:
			if cookie.name == cookie_name:
				cookie_val = cookie.value

		return cookie_val

	# creates a cookie object with the given n,v or updates one if passed in
	def set_cookie(self, name, value, secure=False, expires=None):

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

	# wrap urllib to sort out the openers, handle exceptions etc
	# returns {opener, response} or throws an error
	def do_req(self, url, data=None, cookies=[]):

		opener = self._get_opener()
		cookie_jar = self._get_cookie_jar(opener)

		# encode the data
		if data is not None:
			data = urllib.urlencode(data)

		# set any cookies we need
		for cookie in cookies:
			cookie_jar.set_cookie(cookie)

		try:
			resp   = opener.open(url, data)
		except urllib2.HTTPError, e:
			error = 'Tenrox failed to process the request. HTTP error code: {0}'.format(e.code)
			raise ElevenRoxHTTPError(error)
		except urllib2.URLError, e:
			error = 'Couldn\'t connect to tenrox. Reason: {0}'.format(e.reason)
			raise ElevenRoxHTTPError(error)

		return {
			'cookie_jar': self._get_cookie_jar(opener),
			'response': resp
		}

