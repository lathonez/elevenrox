# contains elevenrox logics
import cookielib, urllib, urllib2

from ConfigParser import SafeConfigParser

class elevenRox():

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

		print('Running on proxy ' + url)

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

		self.test_wget()

		return msg

	def login(self, username=None, password=None):

		if username is None or password is None:
			raise ValueError('Either username or password not supplied')

		print('Attempting login with username: {0}, password: {1}'.format(username,password))

		url = self.config.get('login','url')
		url = self._format_tenrox_url(url)

		viewstate = self.config.get('login','viewstate')

		params = {
			'E_UserName': username,
			'E_Password': password,
			'__VIEWSTATE': viewstate
		}

		data = urllib.urlencode(params)

		opener = self._get_opener()
		resp   = opener.open(url, data)

		print('RESPONSE: ' + resp.read())

		print(resp.info())
		print(resp.geturl())

		return 'hit login'

