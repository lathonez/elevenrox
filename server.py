# script to create and run the server

import optparse, httplib, sys
from wsgiref import simple_server
from jsonrpc import JsonRPC

# create the server object and return it
def get_server(host, port):

	# init http server object from httplib
	http = httplib.HTTP()

	# create an instace of JsonRpcApp using the http server
	jsonrcp = JsonRPC(http)

	# wrap the http server with the WSGI simple server
	server = simple_server.make_server(
	    host,
	    port,
	    jsonrcp
	)

	return server

# set up options for args and return the parser
def set_options():

	parser = optparse.OptionParser(usage="%prog [OPTIONS]")

	parser.add_option(
		'-p', '--port', default='36999',
		help='Port to serve on (default 36999)'
	)

	parser.add_option(
		'-H', '--host', default='0.0.0.0',
		help='Host to serve on (default public; 127.0.0.1 to restrict to localhost)'
	)

	return parser

# main method runs the server forever
def main(args=None):

	parser = set_options()

	# read the args, use options if none
	if args is None:
		args = sys.argv[1:]
		options, args = parser.parse_args()

	# create the server
	server = get_server(
		options.host,
		int(options.port)
	)

	print 'Serving on http://{0}:{1}'.format(options.host, options.port)

	# serve..
	server.serve_forever()

if __name__ == '__main__':
	main()


