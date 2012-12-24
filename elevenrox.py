# contains elevenrox logics

class elevenRox():

	def __init__(self):
		# nothing to do yet
		print 'elevenRox: initing'

	# testing
	def echo(self, msg1=None, msg2=None):

		msg = ''

		if msg1 is not None:
			msg += msg1

		if msg2 is not None:
			msg += msg2

		return msg


