# contains elevenrox logics
import ConfigParser

class elevenRox():

	def __init__(self):

		# read config
		self.config = ConfigParser.ConfigParser()
		self.config.read('elevenrox.cfg')
		print('Base URL: ' + self.config.get('app','base_url'))

	# test function
	def echo(self, msg1=None, msg2=None):

		msg = ''

		if msg1 is not None:
			msg += msg1

		if msg2 is not None:
			msg += msg2

		return msg


