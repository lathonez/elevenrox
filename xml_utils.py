import xml.etree.ElementTree as ET

from assignment import Assignment

class XMLUtils():

	def __init__(self):
		# nothing to do yet
		pass

	#
	# Private Functions
	#

	# parse the assignments contained in a timesheet
	#
	# as ElementTree.element representing the assignments
	# returns ??
	def _parse_assignments(self, assignments):

		assignments_arr = []

		for a in assignments:

			assignment = {
				'assignment_id': a.get('ASS_UID'),
				'name': a.get('ASS_NAME'),
				'start_date': a.get('STARTDATE'),
				'end_date': a.get('ENDDATE'),
				'has_time': a.get('HASTIME'),
				'is_non_working_time': a.get('ISNONWORKINGTIME'),
				'is_default': a.get('ISDEFAULT'),
				'task_id': a.get('TASK_UID'),
				'task_name': a.get('TASK_NAME'),
				'project_id': a.get('PROJECT_UID'),
				'project_name': a.get('PROJECT_NAME'),
				'project_complete': a.get('PCOMPLETE'),
				'client_id': a.get('CLIENT_UID'),
				'client_name': a.get('CLIENT_NAME'),
				'worktype_id': a.get('WORKTYPE_UID'),
				'worktype_name': a.get('WORKTYPE_NAME'),
				'manager_id': a.get('MGRUID'),
				'manager_name': '{0} {1}'.format(a.get('PMGRFN'),a.get('PMGRLN')),
				'manager_email': a.get('PMGRE')
			}

			assignments_arr.append(assignment)

		return assignments_arr

	#
	# Public Functions
	#

	# parse a timesheet XML object as returned by
	# get_time for example. As specified by tenrox.com/TimesheetTemplate.xsd
	#
	# timesheet - string containting the timesheet xml
	# returns ??
	def parse_timesheet(self, timesheet):

		# get the root <Timesheet> element
		root = ET.fromstring(timesheet)

		assignments = None

		for child in root:

			print child.tag,child.attrib

			if child.tag == 'Assignments':
				assignments = self._parse_assignments(child)

		return assignments
