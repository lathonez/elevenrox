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

	# testing - TODO: fix named parameters
	def echo(self, msg1=None, msg2=None):

		msg = ''

		if msg1 is not None:
			msg += msg1

		if msg2 is not None:
			msg += msg2

		return msg

	# process a request: TODO - port and comment error handling over from tutorial
	def process(self, req):

		# load json in from the request body
		json   = loads(req.body)
		method = json['method']
		params = json['params']
		id     = json['id']

		print(params)

		# grab the requested method
		method = getattr(self, method)

		# exec the method with params from json
		if isinstance(params,list):
			result = method(*params)
		elif isinstance(params,dict):
			result = method(**params)
		else:
			raise ValueError(
				"Bad params %r: must be list or dict" % params
			)

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

