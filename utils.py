#
# Utility for parsing XML
#
import xml.etree.ElementTree as ET

class XMLUtils():

	def __init__(self):

		self.STR = 0
		self.BOOL = 1
		self.INT = 2
		self.DATE = 3

		self.xlate = self._get_xlate()

	#
	# Private Functions
	#

	# Generate a dict of names / datatypes to use instaed of the
	# horrible ones we get from tenrox
	def _get_xlate(self):

		# ordered by tenrox id, please
		xlate = {
			'ASSCOMP': ['assignment_complete',self.BOOL],
			'ASSNATRIBUID': ['assignment_attribute_id',self.INT],
			'ASS_NAME': ['assignment_name',self.STR],
			'ASSUID': ['assignment_id',self.INT],
			'ASS_UID':  ['assignment_id',self.STR],
			'CBYUID': ['creator_user_id',self.INT],
			'CLIENT_NAME': ['client_name',self.STR],
			'CLIENT_UID': ['client_id',self.INT],
			'CON': ['cr_date',self.DATE],
			'DOT': ['double_overtime',self.BOOL],
			'ENDDATE': ['end_date',self.DATE],
			'ENTRYDATE': ['entry_date',self.DATE],
			'ENTRYUID': ['entry_id',self.INT],
			'HASPENDINGREQUEST': ['has_pending_request',self.BOOL],
			'HASNOTES': ['has_notes',self.BOOL],
			'HASTIME': ['has_time',self.BOOL],
			'ISDEFAULT': ['is_default',self.BOOL],
			'ISNONWORKINGTIME': ['is_non_working_time',self.BOOL],
			'ISNONWT': ['is_non_working_time',self.BOOL],
			'MGRUID': ['manager_id',self.INT],
			'n': ['notes',self.STR],
			'NOTEOPTION': ['note_option',self.STR],
			'OVT': ['overtime',self.BOOL],
			'PCOMPLETE': ['project_complete',self.STR],
			'PHN': ['project_status_name',self.STR],
			'PHUID': ['project_status_id',self.INT],
			'PMGRE': ['manager_email',self.STR],
			'PMGRFN': ['manager_fname',self.STR],
			'PMGRLN': ['manager_lname',self.STR],
			'PROJECT_NAME': ['project_name',self.STR],
			'PROJECT_UID': ['project_id',self.INT],
			'REG': ['regular_time',self.INT],
			'REJ': ['rejected',self.BOOL],
			'REQUESTCHANGEID': ['request_change_id',self.INT],
			'REQUESTENDDATE': ['request_end_date',self.DATE],
			'REQUESTSTARTDATE': ['request_start_date',self.DATE],
			'SN': ['site_name',self.STR],
			'SDATE': ['start_date',self.DATE],
			'SUID': ['site_id',self.INT],
			'TASK_NAME': ['task_name',self.STR],
			'TASKUID': ['task_id',self.INT],
			'TASKUID': ['task_id',self.INT],
			'TIMESHUID': ['timesheet_id',self.INT],
			'TOTT': ['time',self.INT],
			'UON': ['last_modified',self.DATE],
			'UPDBYUID': ['updater_user_id',self.INT],
			'USERID': ['user_id',self.INT],
			'USERUID': ['user_id',self.INT],
			'WORKTYPE_NAME': ['worktype_name',self.STR],
			'WORKTYPE_UID': ['worktype_id',self.INT]
		}

		return xlate

	# Returns a translated name value pair if an xlation is available
	# Will also convert the datatype of the value if necessary
	# to_xlate - [tag_name,tag_value]
	def _xlate(self, to_xlate):

		name = to_xlate[0]
		val  = to_xlate[1]

		if name not in self.xlate:
			# we can at least lowercase the name
			return [name.lower(),val]

		xlate = self.xlate[name]

		name = xlate[0]

		# sometimes we'll just want to xlate the name
		if val is not None:
			val  = self._cast(val,xlate[1])

		return [name,val]

	# attempt to cast a string value into another datatype
	def _cast(self, val, datatype):

		if datatype == self.BOOL:
			return self._parse_bool(val)

		if datatype == self.INT:
			return int(val)

		# also self.DATE, can't do much with it probably

		return val

	# Turn a string into a boolean if possible
	# Returns true/false, or the original string if we couldn't parse
	def _parse_bool(self, val):

		t = ["1","Y"]
		f = ["0","N"]

		if val in t:
			return True

		if val in f:
			return False

		return val


	
	# TODO:
	# 1 - Make a list of top level tags to bother parsing in parse_timesheet (config)
	# 2 - Move the xlate stuff to its own util class, it shouldn't be with the XML

	# Parse a generic xml tree into dicts/arrays
	def _parse_generic(self, element):

		# dict to represent the element
		e = {}
		got_attributes = True

		# get all the attributes
		for key in element.attrib.keys():
			if element.get(key) != "":
				kv = self._xlate([key,element.get(key)])
				e[kv[0]] = kv[1]

		# if the length is 0 we've only got attributes, no children
		# this marks the end of the recursion
		if not len(element):
			return e

		# mark the fact that we've got no attributes at this point
		if not len(e.keys()):
			got_attributes = False

		# recurse
		for child in element:

			# parse this child and add it to the array
			rec_child = self._parse_generic(child)

			# skip if we got {} back from the recurse
			if not len(rec_child):
				continue

			tag = self._xlate([child.tag,None])[0]

			# create an array for this tag should one not exist
			if tag not in e:
				e[tag] = []

			e[tag].append(rec_child)

		# we can return the array instead of the dict if we've only
		# got one type of child tag
		if not got_attributes and len(e.keys()) == 1:
			for key in e.keys():
				e = e[key]

		return e

	#
	# Public Functions
	#

	# parse a timesheet XML object as returned by
	# get_time for example. As specified by tenrox.com/TimesheetTemplate.xsd
	#
	# timesheet - string containting the timesheet xml
	# returns dict representing timesheet json
	def parse_timesheet(self, timesheet):

		# get the root <Timesheet> element
		root = ET.fromstring(timesheet)

		timesheet = {
		}

		for child in root:

			# print child.tag,child.attrib
			generic = self._parse_generic(child)

			if len(generic):
				timesheet[child.tag] = generic

		return timesheet

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

