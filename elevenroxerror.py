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
		self.code    = -32002
		self.message = 'Failed to parse server response from tenrox'
		self.data    = data

# there's been an error with the 'api' (e.g. tried to do something unsupported)
class ElevenRoxSDKError(ElevenRoxError):

	def __init__(self, data):
		self.code    = -32003
		self.message = 'Failed to interact with the tenrox SDK'
		self.data    = data

