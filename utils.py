#
# Utility for parsing XML
#
from copy import deepcopy
import xml.etree.ElementTree as ET

class XMLUtils():

	def __init__(self):

		self.xlate  = XlateUtils()

	#
	# Public Functions
	#

	# Parse a generic xml tree into dicts/arrays
	def parse_generic(self, element):

		# dict to represent the element
		e = {}
		got_attributes = True

		# get all the attributes
		for key in element.attrib.keys():
			if element.get(key) != "":
				kv = self.xlate.xlate([key,element.get(key)])
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

			tag = self.xlate.xlate([child.tag,None])[0]

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

	# Turn a python bool into 0|1
	def parse_bool(self, b):

		if b:
			return "1"

		return "0"


#
# Utility for dealing with protocol stuff (openers, proxies, cookies)
#
import urllib, urllib2, cookielib, StringIO, gzip

from cookielib       import Cookie, CookieJar
from ConfigParser    import SafeConfigParser

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
	# url,username,password all must be supplied for http basic auth
	def _get_opener(self, url=None, username=None, password=None):

		# overload http handlers for debugging
		debug = self.config.get('app','http_debug_level')
		http  = urllib2.HTTPHandler(debuglevel=debug)
		https = urllib2.HTTPSHandler(debuglevel=debug)

		# do we want to run basic auth
		if url is not None and username is not None and password is not None:

			pm = urllib2.HTTPPasswordMgrWithDefaultRealm()
			pm.add_password(None, url, username, password)
			auth_handler = urllib2.HTTPBasicAuthHandler(pm)

		# handle cookies across 302
		cookie_jar = cookielib.CookieJar()
		cookie = urllib2.HTTPCookieProcessor(cookie_jar)

		handlers = [http, https, cookie]

		# add the proxy to the handlers we're using if necessary
		if self.proxy is not None:
			handlers.append(self.proxy)

		# add the auth to the handlers we're using if necessary
		if auth_handler is not None:
			handlers.append(auth_handler)

		opener = urllib2.build_opener(*handlers)

		return opener

	# unzip a zipped bit of data, returning the raw string
	# TODO: this may also be useful elsewhere (in another util class)?
	def _gunzip(self, data):
		data = StringIO.StringIO(data)
		gzipper = gzip.GzipFile(fileobj=data)

		try:
			string = gzipper.read()
		except IOError as e:
			# this implies the data isn't gzipped, so return the original
			if str(e) == 'Not a gzipped file':
				return data

			raise e

		return string

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
	def set_cookie(self, name, value, secure=False, expires=None, comment='None'):

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
			'comment': comment,
			'comment_url': None,
			'rest': None
		}

		cookie = Cookie(**cookie_params)

		return cookie

	# wrap urllib to sort out the openers, handle exceptions etc
	# returns {opener, response} or throws an error
	def do_req(self, url, data=None, url_encode=True, post=True, cookies=[], username=None, password=None, gzip=True):

		opener     = self._get_opener(url, username, password)
		cookie_jar = self._get_cookie_jar(opener)
		debug_req  = self.config.getboolean('app','http_debug_req')

		# encode the data
		if data is not None:
			if url_encode:
				# implies flattening
				data = urllib.urlencode(data)
			elif not post:
				# if not posting we'll need to flatten into a string for the url
				flat_data = ''
				for k,v in data.items():
					if len(flat_data) > 0:
						flat_data += '&'
					flat_data += '{0}={1}'.format(k,v)
					data = flat_data

		# set any cookies we need
		for cookie in cookies:
			cookie_jar.set_cookie(cookie)

		# if we're not POSTing, wang the data against the url
		if not post:
			url = url + '?' + data
			# null data to imply GET with opener.open
			data = None

		# debug if configured
		if debug_req:
			print 'REQ| url: {0}, data: {1}'.format(url,data)

		# create the urllib2 request object to pass through to the opener
		request = urllib2.Request(url=url, data=data)

		# add compression if configured
		if gzip:
			request.add_header('Accept-encoding', 'gzip')

		try:
			resp = opener.open(request)
		except urllib2.HTTPError, e:
			raise HTTPUtilsError('SERVER_ERROR',e.code)

		except urllib2.URLError, e:
			raise HTTPUtilsError('NO_CONNECT',e.reason)

		# get the response string, we need to do this to deal with compression, and for debug
		# note this is a one time operation, the calling code will not be able to call resp.read() now
		if gzip:
			resp_str = self._gunzip(resp.read())
		else:
			resp_str = resp.read()

		if debug_req:
			print 'RESP|',resp_str

		return {
			'cookie_jar': self._get_cookie_jar(opener),
			'response': resp,
			'response_string' :resp_str
		}

# application specific error thrown by HTTPUtils
class HTTPUtilsError(Exception):

	ERROR_CODES = {
		'DEFAULT': 'An error has occurred with HTTPUtils',
		'NO_CONNECT': 'Couldn\'t connect to the server',
		'SERVER_ERROR': 'Server failed to process the request'
	}

	# code should be a member of ERROR_CODES
	def __init__(self, code='DEFAULT', debug=None):

		self.code  = code
		self.debug = debug
		message    = self.ERROR_CODES[code]

		Exception.__init__(self, message)


#
# Utility for translating  names / datatypes into more user friendly ones, using supplied static class
#
class XlateUtils():

	# static: a static class can be used for translating responses
	def __init__(self,static=None):

		if static is None:
			static = XlateStatic()
		else:
			self.static = static

	#
	# Private Functions
	#

	# attempt to cast a string value into another datatype
	def _cast(self, val, datatype):

		if datatype == self.static.BOOL:
			return self._parse_bool(val)

		if datatype == self.static.INT:
			return int(val)

		# also self.static.DATE, can't do much with it probably

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

	#
	# Public Functions
	#

	# Returns a translated name value pair if an xlation is available
	# Will also convert the datatype of the value if necessary
	# to_xlate - [tag_name,tag_value]
	def xlate(self, to_xlate):

		name = to_xlate[0]
		val  = to_xlate[1]

		if name not in self.static.xlate:
			# we can at least lowercase the name
			return [name.lower(),val]

		xlate = self.static.xlate[name]

		name = xlate[0]

		# sometimes we'll just want to xlate the name
		if val is not None:
			val  = self._cast(val,xlate[1])

		return [name,val]

# blank static class incase the caller hasn't passed one through
class XlateStatic():

	STR = 0
	BOOL = 1
	INT = 2
	DATE = 3

	xlate = {}

import base64
from Crypto.Cipher import Blowfish
from ConfigParser  import SafeConfigParser
from random import randrange
# Some Credit: http://code.activestate.com/recipes/496763-a-simple-pycrypto-blowfish-encryption-script/
#
# Utility for dealing with encryption / decryption
#
class SecUtils():

	def __init__(self, config):

		self.config = config
		self.key    = self.config.get('sec_utils','key')
		self.cipher = Blowfish.new(self.key)

	# encrypt a string
	def encrypt(self, string):

		padded = self._pad(string)
		ciphertext = self.cipher.encrypt(padded)
		b64 = base64.b64encode(ciphertext)

		return b64

	# descrypt a string
	def decrypt(self, b64):

		ciphertext = base64.b64decode(b64)
		padded = self.cipher.decrypt(ciphertext)
		string = self._unpad(padded)

		return string

	# pad a string to 8 bytes
	def _pad(self, string):

		bs = Blowfish.block_size
		pad_bytes = bs - (len(string) % bs)
		for i in range(pad_bytes - 1): string += chr(randrange(0, 256))
		bflag = randrange(6, 248); bflag -= bflag % bs - pad_bytes
		string += chr(bflag)

		return string

	# unpad a string from 8 bytes
	def _unpad(self, string):

		bs = Blowfish.block_size
		pad_bytes = ord(string[-1]) % bs
		if not pad_bytes: pad_bytes = bs

		return string[:-pad_bytes]

