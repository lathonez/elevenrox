# most of this code borrowed from Ian Bicking's tutorial at http://docs.webob.org/en/latest/jsonrpc-example.html
# importing webob stuff
from webob import Request, Response
from webob import exc
# json manipulation
from simplejson import loads, dumps
import sys, httplib

# core request/response logic
# object is httplib.HTTP
class JsonRpcApp(object):

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
	def echo(self, msg1=None):
		return msg1

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


# TODO - I don't really understand what this is about
# The tutorial says it's so you can create servers of differnt
# types dynamically using input args (e.g. smtplib:SMTP)
# but we definitely don't need that
def make_app(expr):

	module, expression = expr.split(':', 1)

	__import__(module)
	module = sys.modules[module]
	obj = eval(expression, module.__dict__)

	return JsonRpcApp(obj)

# main method runs the server forever
def main(args=None):

	# import the parser for options and the server
	import optparse
	from wsgiref import simple_server

	# set up options
	parser = optparse.OptionParser(
	    usage="%prog [OPTIONS]")

	parser.add_option(
	    '-p', '--port', default='36999',
	    help='Port to serve on (default 36999)')

	parser.add_option(
	    '-H', '--host', default='0.0.0.0',
	    help='Host to serve on (default public; 127.0.0.1 to restrict to localhost)')

	# read the args, use options if none
	if args is None:
		args = sys.argv[1:]
		options, args = parser.parse_args()

	# init the server
	app = make_app("httplib:HTTP")

	server = simple_server.make_server(
	    options.host, int(options.port),app)

	print 'Serving on http://%s:%s' % (options.host, options.port)

	server.serve_forever()

if __name__ == '__main__':
	main()


