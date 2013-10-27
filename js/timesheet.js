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

	var as = this._build_assignments(_t.assignments),
	    ts = this._build_timeentries(_t.timeentries),
	    a, t;

	this._splice(as);
	this._splice(ts);
};

/*
 * Replace elements of either this.assignments or this.timeentries with the given arr
 *
 * TODO - this function is important as it maintains the ER model. It wants proper testing
 */
Timesheet.prototype._splice = function(arr) {

	var o_arr, o;

	if (!arr.length) {
		return;
	}

	// dunno if there's a better way of doing this, typeof gives 'object;
	if (arr[0].__proto__.constructor.name == 'Assignment') {
		o_arr = this.assignments;
	} else if (arr[0].__proto__.constructor.name == 'Timeentry') {
		o_arr = this.timeentries;
	} else {
		throw "ERROR: called _splice with unfamiliar array";
	}

	for (var i = 0; i < o_arr.length; i++) {

		o = o_arr[i];

		// there should only be one assignment
		for (var j = 0; j < arr.length; j++) {

			// not sure if we need to match on anything else
			if (o.id == arr[j].id ) {
				o_arr = o_arr.splice(i,1,arr[j]);

				// remove the one we've just added from the array passed in
				arr = arr.splice(j,1);
			}
		}

		// no point spinning if we've done everything
		if (!arr.length) {
			return;
		}
	}

	// if we've got anything left in arr, it means we didn't find it (it's a new entry)
	for (var i = 0; i < arr.length; i++) {
		o_arr.push(arr[i]);
	}
};

