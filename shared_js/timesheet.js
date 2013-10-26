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
 * Update a timesheet (slice) from the JSON received as a result of a set_time request
 */
Timesheet.prototype.set = function(_t) {
	this.assignments = this._build_assignments(_t.assignments);
	this.timeentries = this._build_timeentries(_t.timeentries);
};

