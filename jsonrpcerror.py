# base class for JsonRPC errors
# http://www.jsonrpc.org/specification
class JsonRPCError(Exception):
	pass

class JsonRPCInvalidRequestError(JsonRPCError):

	def __init__(self, data):
		self.code = -32600
		self.message = 'Invalid Request'
		self.data = data

class JsonRPCParseError(JsonRPCError):

	def __init__(self, data):
		self.code = -32700
		self.message = 'Parse error'
		self.data = data

class JsonRPCMethodNotFoundError(JsonRPCError):

	def __init__(self, data):
		self.code = -32601
		self.message = 'Method not found'
		self.data = data

class JsonRPCInvalidParamsError(JsonRPCError):

	def __init__(self, data):
		self.code = -32602
		self.message = 'Invalid params'
		self.data = data
