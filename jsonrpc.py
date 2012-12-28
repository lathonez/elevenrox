# most of this code borrowed from Ian Bicking's tutorial at http://docs.webob.org/en/latest/jsonrpc-example.html
# importing webob stuff
from webob import Request, Response
from webob import exc
# json manipulation
from simplejson import loads, dumps
from elevenrox import elevenRox

# core request/response logic
# object is httplib.HTTP
class JsonRPC(object):

	# self.obj is httplib.HTTP as this gets passed through implicitly into init
	def __init__(self, obj):
		self.obj = obj
		self.content_type = 'application/json'
		self.elevenRox = elevenRox()

	# handle a request
	def __call__(self, environ, start_response):

		err_name = None
		err_msg  = None

		req = Request(environ)

		try:
			resp = self.process(req)
		except exc.HTTPMethodNotAllowed, e:
			err_name = 'HTTPMethodNotAllowed'
			err_msg  = '%s' % e
		except ValueError, e:
			err_name = 'ValueError'
			err_msg  = '%s' % e
		except exc.HTTPForbidden, e:
			err_name = 'HTTPForbidden'
			err_msg  = '%s' % e
		except Exception, e:
			err_name = 'Internal Server Error'
			err_msg  = '%s' % e

		# if we've encountered an error return it in the JSON
		if err_name is not None:

			print('Error: ' + err_name + ': ' + err_msg)

			resp = self.build_response(
				err_name = err_name,
				err_msg  = err_msg
			)

		return resp(environ, start_response)

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
			method = getattr(self.elevenRox, method)
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

	# format a response for return in the JSON
	def build_response(
		self,
		result   = None,
		err_name = None,
		err_msg  = None,
		id       = -1
	):

		if err_name is not None:
			error = dict(
				name    = err_name,
				message = err_msg
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

