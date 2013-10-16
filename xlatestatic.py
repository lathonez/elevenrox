#
# Just contains the static xlate dict
#
class ERXlateStatic:

	STR = 0
	BOOL = 1
	INT = 2

	# DD/MM/YYYY
	DATE = 3
	# MM/DD/YYYY
	US_DATE = 4

	# ordered by tenrox id, please
	xlate = {
		'ACCSTATUS': ['account_status',BOOL],
		'ASSCOMP': ['assignment_complete',BOOL],
		'ASSNATRIBUID': ['assignment_attribute_id',INT],
		'ASS_NAME': ['assignment_name',STR],
		'ASSUID': ['assignment_id',INT],
		'ASS_UID':  ['assignment_id',STR],
		'CANCREATETASK': ['can_create_task',BOOL],
		'CANMODIFYPUNCHENTRIES': ['can_modify_punch_entries',BOOL],
		'CBYUID': ['creator_user_id',INT],
		'CLIENT_NAME': ['client_name',STR],
		'CLIENT_UID': ['client_id',INT],
		'CON': ['cr_date',US_DATE],
		'COUNTPROJECT': ['count_project',INT],
		'DEFPRJUID': ['default_project_id',INT],
		'DHIRED': ['date_hired',US_DATE],
		'DOT': ['double_overtime',BOOL],
		'EMPTYPE': ['employee_type',STR],
		'ENDDATE': ['end_date',US_DATE],
		'ENTRYDATE': ['entry_date',US_DATE],
		'ENTRYUID': ['entry_id',INT],
		'FN': ['first_name',STR],
		'GROUPUID': ['group_id',INT],
		'HASPENDINGREQUEST': ['has_pending_request',BOOL],
		'HASNOTES': ['has_notes',BOOL],
		'HASTIME': ['has_time',BOOL],
		'ISAPPROVAL': ['is_approval',BOOL],
		'ISCOMP': ['is_complete',BOOL],
		'ISDEFAULT': ['is_default',BOOL],
		'ISFINAL': ['is_final',BOOL],
		'ISMULTIMAPP': ['is_multi_map',BOOL],
		'ISRD': ['is_r_and_d',BOOL],
		'ISREADONLY': ['is_read_only',BOOL],
		'ISREJ': ['is_rejected',BOOL],
		'ISRO': ['is_read_only',BOOL],
		'ISNONWORKINGTIME': ['is_non_working_time',BOOL],
		'ISNONWT': ['is_non_working_time',BOOL],
		'ISTIMECLOSED': ['is_time_closed',BOOL],
		'LN': ['last_name',STR],
		'MGRCANCRTIMECHARGES': ['manager_can_create_time_charges',BOOL],
		'MGRCANMODIFYBILL': ['manager_can_modify_bill',BOOL],
		'MGRCANMODIFYPAY': ['manager_can_modify_pay',BOOL],
		'MGRUID': ['manager_id',INT],
		'n': ['notes',STR],
		'NOTEOPTION': ['note_option',STR],
		'OBJTYPE': ['object_type',INT],
		'OVT': ['overtime',BOOL],
		'PCOMPLETE': ['project_complete',STR],
		'PERIODTYPE': ['period_type',STR],
		'PHN': ['project_status_name',STR],
		'PHUID': ['project_status_id',INT],
		'PMASSIGNED': ['pm_assigned',BOOL],
		'PMGRE': ['manager_email',STR],
		'PMGRFN': ['manager_fname',STR],
		'PMGRLN': ['manager_lname',STR],
		'PROJECT_NAME': ['project_name',STR],
		'PROJECT_UID': ['project_id',INT],
		'REG': ['regular_time',INT],
		'REJ': ['rejected',BOOL],
		'REQUESTCHANGEID': ['request_change_id',INT],
		'REQUESTENDDATE': ['request_end_date',US_DATE],
		'REQUESTSTARTDATE': ['request_start_date',US_DATE],
		'SN': ['site_name',STR],
		'SDATE': ['start_date',US_DATE],
		'SITEUID': ['site_id',INT],
		'SUID': ['site_id',INT],
		'TASK_NAME': ['task_name',STR],
		'TASKUID': ['task_id',INT],
		'TASKUID': ['task_id',INT],
		'TERMDATE': ['term_date',STR],
		'TIMECHARGEREADONLY': ['time_charge_read_only',BOOL],
		'TIMESHUID': ['timesheet_id',INT],
		'TOTT': ['time',INT],
		'UON': ['last_modified',US_DATE],
		'UPDBYUID': ['updater_user_id',INT],
		'USERHIREDATE': ['user_hire_date',US_DATE],
		'USERID': ['user_id',INT],
		'USERTERMINATIONDATE': ['user_fired_date',US_DATE],
		'USERTYPE': ['user_type',STR],
		'USERUID': ['user_id',INT],
		'WORKTYPE_NAME': ['worktype_name',STR],
		'WORKTYPE_UID': ['worktype_id',INT]
	}

