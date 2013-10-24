/*
 * Represents an assignment returned from elevenrox
 */

/*
 * _a - raw assignment json
 */
function Assignment(_a) {

	this._init(
		_a.assignment_id,
		_a.assignment_attribute_id,
		_a.assignment_name,
		_a.has_time,
		_a.timeentries,
		_a.client_id,
		_a.client_name,
		_a.project_id,
		_a.project_name,
		_a.task_uid,
		_a.task_name,
		_a.worktype_id,
		_a.worktype_name
	);
};

Assignment.prototype._init = function(
	id,
	attribute_id,
	name,
	has_time,
	timeentries,
	client_id,
	client_name,
	project_id,
	project_name,
	task_id,
	task_name,
	worktype_id,
	worktype_name
) {
	this.id            = id;
	this.attribute_id  = attribute_id;
	this.name          = name;
	this.has_time      = has_time;
	this.timeentries   = this._build_timeentries(timeentries);
	this.client_id     = client_id;
	this.client_name   = client_name;
	this.prokect_id    = project_id;
	this.task_id       = task_id;
	this.task_name     = task_name;
	this.worktype_id   = worktype_id;
	this.worktype_name = worktype_name;
};

Assignment.prototype._build_timeentries = function(timeentries) {

	var ts = [];

	if (timeentries === undefined) {
		return ts;
	}

	$.each(timeentries, function(i,t) {
		ts.push(new Timeentry(t));
	});

	return ts;
};

/*
 * Return the timeentry for this assignment on the date specified, or null if one doesn't exist
 */
Assignment.prototype.get_timeentry = function(tenrox_date) {

	var entry;

	for (var i = 0; i < this.timeentries.length; i++) {

		entry = this.timeentries[i];

		if (entry.date == tenrox_date) {
			return entry;
		}
	}

	return null;
};

