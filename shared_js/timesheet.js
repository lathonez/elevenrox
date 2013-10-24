/*
 * Represents a timesheet returned from elevenrox
 */

/*
 * _t - raw timesheet json
 */
function Timesheet(_t) {

	this._init(
		_t.uid,
		_t.start_date,
		_t.end_date,
		_t.assignments,
		_t.timeentries,
		_t.user
	);
};

Timesheet.prototype._init = function(
	id,
	start_date,
	end_date,
	assignments,
	timeentries,
	user
) {
	this.id          = id;
	this.start_date  = start_date;
	this.end_date    = end_date;
	this.assignments = this._build_assignments(assignments);
	this.timeentries = this._build_timeentries(timeentries);
	this.user        = user;
};

Timesheet.prototype._build_assignments = function(assignments) {

	var as = [];

	if (assignments === undefined) {
		return as;
	}

	$.each(assignments, function(i,a) {
		as.push(new Assignment(a));
	});

	return as;
};

Timesheet.prototype._build_timeentries = function(timeentries) {

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
 * Return an assignment based on a tenrox_code, or null
 * if one doesn't exist for this timesheet
 */
Timesheet.prototype.get_assignment = function(tenrox_code) {

	var a;

	for (var i = 0; i < this.assignments.length; i++) {

		var a = this.assignments[i];

		if (a.name.search(tenrox_code) > -1) {
			return a;
		}
	}

	return null;
};

/*
 * Update a timesheet (slice) from the JSON received as a result of a set_time request
 */
Timesheet.prototype.set = function(_t) {

};
