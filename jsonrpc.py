# most of this code borrowed from Ian Bicking's tutorial at http://docs.webob.org/en/latest/jsonrpc-example.html
# importing webob stuff
from webob import Request, Response, exc

# json manipulation
from simplejson import loads, dumps

# handling elevenrox specific logic
from elevenrox      import ElevenRox
from elevenroxerror import ElevenRoxError
from jsonrpcerror   import *

import traceback, sys

# core request/response logic
# object is httplib.HTTP
class JsonRPC(object):

	# self.obj is httplib.HTTP as this gets passed through implicitly into init
	def __init__(self, obj):
		self.obj = obj
		self.content_type = 'application/json'
		self.elevenRox = ElevenRox()

	# handle a request
	def __call__(self, environ, start_response):

		err_code = None
		err_msg  = None
		err_data = None

		req = Request(environ)

		try:
			resp = self.process(req)
		except (JsonRPCError, ElevenRoxError) as e:
			err_msg  = e.message
			err_code = e.code
			err_data = '%s' % e.data
			traceback.print_exc(file=sys.stdout)
		except Exception, e:
			err_msg  = 'Internal Error'
			err_code = -32603
			err_data = '%s' % e.data
			traceback.print_exc(file=sys.stdout)

		# if we've encountered an error return it in the JSON
		if err_msg is not None:

			print 'Error: {0}: Code: {1} Data: {2}'.format(
				err_msg,
				err_code,
				err_data
			)

			resp = self.build_response(
				err_msg  = err_msg,
				err_code = err_code,
				err_data = err_data
			)

		return resp(environ, start_response)

	# sanity check the request and return the JSON
	def check_req(self, req):

		# only allow POST
		if not req.method == 'POST':
			raise JsonRPCInvalidRequestError('Only POST allowed')

		# check the request body is valid JSON
		try:
			json = loads(req.body)
		except ValueError, e:
			raise JsonRPCParseError('Request body is not valid JSON: %s' % e)

		# check the JSON contains everything we need to process
		try:
			method = json['method']
			params = json['params']
			id     = json['id']
		except KeyError, e:
			raise JsonRPCParseError('JSON body missing parameter: %s' % e)

		# do not allow access to private methods
		if method.startswith('_'):
			raise JsonRPCMethodNotFoundError(
				'Attempted to access a private method %s:_' % method
			)

		# the params should be a list or a dict
		# flag if we've got named parameters (nParams)
		if isinstance(params,list):
			nParams = False
		elif isinstance(params,dict):
			nParams = True
		else:
			raise JsonRPCInvalidParamsError(
				'Bad params %r: must be JSON array or object' % params
			)

		# check the method exists
		try:
			method = getattr(self.elevenRox, method)
		except AttributeError:
			raise JsonRPCMethodNotFoundError('No such method %s' % method)

		# assign what we've got to the rtn dict and send it back
		rtn = dict(
			method  = method,
			params  = params,
			id      = id,
			nParams = nParams
		)

		return rtn

	# format a response for return in the JSON
	def build_response(
		self,
		result   = None,
		err_msg  = None,
		err_code = None,
		err_data = None,
		id       = -1
	):
		if err_msg is not None:
			error = dict(
				code    = err_code,
				message = err_msg,
				data    = err_data
			)
		else:
			error = None

		body = dict(
			result = result,
			error  = error,
			id     = id
		)

		# build a response based on the method return
		resp = Response(
			content_type = self.content_type,
			body = dumps(body)
		)

		return resp

	# process a request
	def process(self, req):

		json = self.check_req(req)

		method  = json['method']
		params  = json['params']
		id      = json['id']
		nParams = json['nParams']

		if nParams:
			result = method(**params)
		else:
			result = method(*params)

		return self.build_response(
			result = result,
			id = id
		)

