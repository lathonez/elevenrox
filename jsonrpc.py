# most of this code borrowed from Ian Bicking's tutorial at http://docs.webob.org/en/latest/jsonrpc-example.html
# importing webob stuff
from webob import Request, Response
from webob import exc
# json manipulation
from simplejson import loads, dumps

# core request/response logic
# object is httplib.HTTP
class JsonRPC(object):

	# self.obj is httplib.HTTP as this gets passed through implicitly into init
	def __init__(self, obj):
		self.obj = obj
		self.content_type = 'application/json'

	# handle a request
	def __call__(self, environ, start_response):
		req = Request(environ)

		try:
			resp = self.process(req)
		except ValueError, e:
			resp = exc.HTTPBadRequest(str(e))
		except exc.HTTPException, e:
			resp = e

		return resp(environ, start_response)

	# testing
	def echo(self, msg1=None, msg2=None):

		msg = ''

		if msg1 is not None:
			msg += msg1

		if msg2 is not None:
			msg += msg2

		return msg

	# sanity check the request and return the JSON
	def check_req(self, req):

		# only allow POST
		if not req.method == 'POST':
			raise exc.HTTPMethodNotAllowed(
				"Only POST allowed",
				allowed='POST'
			)

		# check the request body is valid JSON
		try:
			json = loads(req.body)
		except ValueError, e:
			raise ValueError('Request body is not valid JSON: %s' % e)

		# check the JSON contains everything we need to process
		try:
			method = json['method']
			params = json['params']
			id     = json['id']
		except KeyError, e:
			raise ValueError(
				"JSON body missing parameter: %s" % e
			)

		# do not allow access to private methods
		if method.startswith('_'):
			raise exc.HTTPForbidden(
				"Attempted to access a private method %s:_" % method
			)

		# the params should be a list or a dict
		# flag if we've got named parameters (nParams)
		if isinstance(params,list):
			nParams = False
		elif isinstance(params,dict):
			nParams = True
		else:
			raise ValueError(
				"Bad params %r: must be list or dict" % params
			)

		# check the method exists
		try:
			method = getattr(self, method)
		except AttributeError:
			raise ValueError(
				"No such method %s" % method
			)

		# assign what we've got to the rtn dict and send it back
		rtn = dict(
			method  = method,
			params  = params,
			id      = id,
			nParams = nParams
		)

		return rtn

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

		# build up the dict to use as the body
		body = dict(
			result = result,
			error  = None,
			id     = id
		)

		# build a response based on the method return
		resp = Response(
			content_type = self.content_type,
			body = dumps(body)
		)

		return resp

