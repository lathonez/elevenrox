/*
 * Represents a timeentry returned from elevenrox
 */

/*
 * _t - raw timeentry json
 */
function Timeentry(_t) {

	this._init(
		_t.entry_id,
		_t.entry_date,
		_t.assignment_id,
		_t.assignment_attribute_id,
		_t.buid,
		_t.bun,
		_t.time,
		_t.notes,
		_t.task_id
	);
};

Timeentry.prototype._init = function(
	id,
	date,
	as_id,
	as_attribute_id,
	buid,
	bun,
	time,
	comments,
	task_id
) {
	this.id       = id;
	this.date     = date;
	this.buid     = buid;
	this.bun      = bun;
	this.time     = time;
	this.comments = (comments === undefined ? [] : comments);
	this.task_id  = task_id;

	this.assignment_id           = as_id;
	this.assignment_attribute_id = as_attribute_id;

	// we need either an id or a date
	if (!this.id && !this.date) {
		throw 'ERROR: Either an id or date must be supplied for a timeentry';
	}
};

/*
 * Currently we only support one comment
 *
 * Returns null if no comment exists
 */
Timeentry.prototype.get_comment = function() {

	if (!this.comments.length) {
		return null;
	}

	return this.comments[0];
};
