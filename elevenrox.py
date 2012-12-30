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

	# test function
	def echo(self, msg1=None, msg2=None):

		msg = ''

		if msg1 is not None:
			msg += msg1

		if msg2 is not None:
			msg += msg2

		return msg

	# wrap urllib to sort out the openers, handle exceptions etc
	def _do_req(self, url, data):

		opener = self._get_opener()

		try:
			resp   = opener.open(url, data)
		except urllib2.HTTPError, e:
			error = 'Tenrox failed to process the request. HTTP error code: {0}'.format(e.code)
			raise ElevenRoxHTTPError(error)
		except urllib2.URLError, e:
			error = 'Couldn\'t connect to tenrox. Reason: {0}'.format(e.reason)
			raise ElevenRoxHTTPError(error)

		return resp

	def login(self, username=None, password=None):

		if username is None or password is None:
			raise JsonRPCInvalidParamsError('Either username or password not supplied')

		print 'Attempting login with username: {0}, password: {1}'.format(username,password)

		url = self.config.get('login','url')
		url = self._format_tenrox_url(url)

		viewstate = self.config.get('login','viewstate')

		params = {
			'E_UserName': username,
			'E_Password': password,
			'__VIEWSTATE': viewstate
		}

		data = urllib.urlencode(params)
		resp = self._do_req(url, data)

		print 'RESPONSE: ' + resp.read()

		print resp.info()
		print resp.geturl()

		return 'hit login'

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

