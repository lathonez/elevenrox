#
# Utility for parsing XML
#
from copy import deepcopy
from utils import XMLUtils

import xml.etree.ElementTree as ET

class ElevenRoxXML():

	def __init__(self, config):

		self.config = config
		self.xlate  = XlateUtils()
		self.xml    = XMLUtils()

		# we don't want to parse some of the tags for perf
		self.timesheet_blacklist = self.config.get(
			'get_time_xml',
			'timesheet_tags_blacklist'
		).rsplit('|')

		self.set_time_base_xml = ET.parse(
			self.config.get('xml','time_file_name')
		)

		self.set_comment_base_xml = ET.parse(
			self.config.get('xml','comment_file_name')
		)

	#
	# Public Functions
	#

	# parse a timesheet XML object as returned by
	# get_time for example. As specified by tenrox.com/TimesheetTemplate.xsd
	#
	# timesheet - string containting the timesheet xml
	# returns dict representing timesheet json
	def parse_timesheet(self, timesheet):

		# get the root <Timesheet> element
		root = ET.fromstring(timesheet)

		timesheet = {}

		# get TL attributes before moving onto childs
		for key in root.attrib.keys():
			if root.get(key) != "":
				kv = self.xlate.xlate([key,root.get(key)])
				timesheet[kv[0]] = kv[1]

		for child in root:

			if (child.tag) in self.timesheet_blacklist:
				continue

			# print child.tag,child.attrib
			generic = self.xml.parse_generic(child)

			if len(generic):
				tag = self.xlate.xlate([child.tag,None])[0]
				timesheet[tag] = generic

		return timesheet

	# just grab the few items we need from this
	def parse_timesheet_layout(self, timesheet_layout):

		root = ET.fromstring(timesheet_layout)

		timesheet_layout = {
			'id': root.get('uid'),
			'name': root.get('name')
		}

		return timesheet_layout

	# return XML to be posted in the set_time request
	# see set_time in elevenrox.py for params
	def build_set_time_xml(
		self,
		timesheet_id,
		start_date,
		end_date,
		user_id,
		template_id,
		template_name,
		assignment_id,
		entry_id,
		entry_date,
		entry_time,
		overtime,
		double_ot,
		is_etc,
		enst
	):

		# we store a copy of the xml in memory to minimise IO
		# but we want to make a copy of it before modification
		root = deepcopy(self.set_time_base_xml).getroot()

		# set the param attributes
		# This assumes there's one <PARANS> tag
		for param in root.iter('PARAMS'):
			param.set('TIMESHEETUID',timesheet_id)
			param.set('TIMESHEET_SD',start_date)
			param.set('TIMESHEET_ED',end_date)
			param.set('LOGGEDUSERUID',user_id)
			param.set('USERUID',user_id)
			param.set('TEMPLATEUID',template_id)
			param.set('TEMPLATE_NAME',template_name)
			param.set('ASSIGNMENTATRIBUID',assignment_id)
			param.set('ENTRYUID',entry_id)
			param.set('ENTRYDATE',entry_date)
			param.set('REG',entry_time)
			param.set('OVT',self.xml.parse_bool(overtime))
			param.set('DOT',self.xml.parse_bool(double_ot))
			param.set('ISETC',self.xml.parse_bool(is_etc))
			param.set('ENST',self.xml.parse_bool(enst))

		return ET.tostring(root)

	# return XML to be posted in the set_comment request
	# see set_comment in elevenrox.py for params
	def build_set_comment_xml(
		self,
		comment,
		comment_id,
		entry_id,
		comment_type,
		is_public,
		creator_id,
		obj_type
	):

		# we store a copy of the xml in memory to minimise IO
		# but we want to make a copy of it before modification
		root = deepcopy(self.set_comment_base_xml).getroot()

		# set the param attributes
		# This assumes there's one <PARANS> tag
		for param in root.iter('PARAMS'):
			param.set('NoteUID',comment_id)
			param.set('NoteEntryUID',entry_id)
			param.set('NoteCreatorUID',creator_id)
			param.set('NoteType',comment_type)
			param.set('NoteIsPublic',self.xml.parse_bool(is_public))
			param.set('NoteDesc',comment)
			param.set('ObjType',obj_type)

		return ET.tostring(root)

	# xml_str - xml to check for an error
	# err_msg - default error message
	def get_error_message(self,xml_str,err_msg='Unknown Error'):

		try:
			root = ET.fromstring(xml_str)
		except ET.ParseError, e:
			return err_msg

		for child in root:
			if child.tag == 'status':
				return child.get('message')

		return err_msg


#
# Utility for parsing tenrox HTML
#
from bs4 import BeautifulSoup
import re

# wrapper for BeautifulSoup with some helper fns for tenrox
class ElevenRoxHTML():

	# html - html string you want to use with this instance
	#        of the parser
	def __init__(self, html):

		self.html = html
		self.soup = BeautifulSoup(html)

	# Returns a friendly (well formatted) string of the html
	# do_print - if True will also print to the console
	def prettify(self,do_print=False):

		pretty = self.soup.prettify()

		if do_print:
			print pretty

		return pretty

	# err_msg - default error message
	def get_error_message(self,err_msg='Unknown Error'):

		err_arr   = None
		err_div   = None
		err_child = None

		err_arr = self.soup.select('#TDError')

		if len(err_arr):
			err_div = err_arr[0]

		if err_div is not None and len(err_div):
			# could either be a span or a div
			err_child = err_div.contents[0]

		if err_child is not None:
			err_msg = err_child.string

		return err_msg

	# check whether or not the user is logged in based on the response body
	def is_logged_in(self):

		err_span = self.soup.select('#ErrorMessage')

		if not len(err_span):
			return True

		err_string = err_span[0].string

		# just a bit of unnecesssary checking
		if 'Invalid User Id or Password' in err_string:
			return False

		# something's gone wrong, but we don't know what
		print 'WARNING: Unknown error whilst logging in,', err_string

		return False

	def get_user_id(self):

		# get the iframe with the session info
		iframe = self.soup.select('#Iframe3')

		if not len(iframe):
			return None

		# the user_id is contained in the keepalive (src) link in the iframe
		iframe_src = iframe[0]['src']

		start_string = 'userUniqueID='
		end_string = '&userName'

		try:
			# the uid should be somewhere in here
			start = iframe_src.find(start_string) + start_string.__len__()
			end   = iframe_src.find(end_string)
		except ValueError, e:
			return None

		return iframe_src[start:end]

	# return [start_date,end_date] for the get_time request
	def get_date_range(self):

		start_elem = self.soup.select('#TInterval_SD')
		end_elem   = self.soup.select('#TInterval_ED')

		start_date = start_elem[0]['value']
		end_date   = end_elem[0]['value']

		return [start_date,end_date]

