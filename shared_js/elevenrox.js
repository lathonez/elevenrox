/*
 * Handles integration with ElevenRox
 */

function ElevenRox(
	_username,
	_password,
	_url,
	_token
) {
	this._init(
		_username,
		_password,
		_url,
		_token
	);
};

/*
 * Private functions
 */

/*
 * note also the public function init
 *
 * _url -
 * _username -
 * _password -
 * _token    - allows creation of an 11rx instance from an earlier session
 */
ElevenRox.prototype._init = function(
	_username,
	_password,
	_url,
	_token
) {
	this.username        = _username;
	this.password        = _password;
	this.url             = _url;
	this.token           = (typeof _token === undefined ? null : _token);
	this.timesheet_token = null;
	this.date            = null;
	this.timesheet       = null;
	this.request_id      = 0;
	this.inited          = false;
};

/*
 * Throw an exception if we're not initialised
 */
ElevenRox.prototype._check_init = function() {

	if (!this.inited) {
		throw Exception('not initialised, call ElevenRox.init()');
	}
};

/*
 * Login to 11rx
 *
 * _callabck -
 */
ElevenRox.prototype._login = function(_callback) {

	var req;

	if (this._is_logged_in()) {
		_callback();
		return;
	}

	req = this._build_login_request(this.username, this.password);

	this._send(req,_callback);
};

/*
 * Check whether or not we appear to be logged in
 * Token validity is not checked here
 */
ElevenRox.prototype._is_logged_in = function() {

	return (this.token);
};

/*
 * Build the data model from a get_time request
 *
 * _callback -
 */
ElevenRox.prototype._build_data_model = function(_callback) {

	var req = this._build_get_time_request(this.date, false);

	this._send(req,_callback);
};

/*
 * Have we built the data model yet?
 */
ElevenRox.prototype._has_data_model = function() {

	// TODO - this better
	return (this.timesheet_token);
};

/*
 * Base request functions
 */

/*
 * _username -
 * _password -
 */
ElevenRox.prototype._build_login_request = function(
	_username,
	_password
) {

	var request = {};
	
	// mandatory params
	request.method          = "login";
	request.params          = {};
	request.params.username = _username;
	request.params.password = _password;

	return request;
};

/*
 * _start_date (? - DD/MM/YYYY) -
 * _reorder_timentries (? - boolean) -
 */
ElevenRox.prototype._build_get_time_request = function(
	_start_date,
	_reorder_timeentries
) {

	var request = {};

	// mandatory params
	request.method = "get_time";
	request.params = {};

	// optional params
	if (typeof _start_date !== undefined) {
		request.params.start_date = _start_date;
	}

	if (typeof _reorder_timeentries !== undefined) {
		request.params.reorder_timeentries = _reorder_timeentries;
	}

	return request;
};

/*
 * _assignment_attribute_id (integer) -
 * _time (integer, seconds) -
 * _entry_id (? integer)
 * _entry_date (? string DD/MM/YYYY) -
 * _comment (? string) -
 */
ElevenRox.prototype._build_set_time_request = function(
	_assignment_attribute_id,
	_time,
	_entry_id,
	_entry_date,
	_comment
) {
	var request = {};

	// mandatory params
	request.method = "set_time"
	request.params = {}
	request.params.assignment_attribute_id = _assignment_attribute_id;
	request.params.time = _time;

	// optional params
	if (typeof _entry_id !== undefined) {
		request.params.entry_id = _entry_id;
	}

	if (typeof _entry_date !== undefined) {
		request.params.entry_date = _entry_date
	}

	return request;
};

/*
 * Returns true if request was succesfull (in elevenrox), else false
 */
ElevenRox.prototype._resp_landing = function (_resp,_req,_callback) {

	var fn = 'ElevenRox._resp_landing: ';

	console.log(_resp);

	if (_resp.error) {

		err_string = fn + 'request failed: '

		for (var key in _resp.error) {
			err_string += key + '- ' + eval('_resp.error.' + key) + ' ';
		}

		console.log(err_string);

		_callback();
		return;
	}

	// all successful responses from 11rx should return a token - need to keep it updated
	this.token = _resp.result.token;

	if (_resp.result.timesheet_token !== undefined) {
		this.timesheet_token = _resp.result.timesheet_token;
	}

	/*
	 * request specific handling
	 */

	// completely re-write the timesheet for get_time
	if (_req.method == 'get_time') {
		this.timesheet = new Timesheet(_resp.result.timesheet);
	}

	// update a slice for set_time
	if (_req.method == 'set_time') {
		this.timesheet.set(_resp.result.timesheet);
	}
	
	// tell the calling code we're ready
	_callback();
};

/*
 * _req      - request object to send to elevenrox
 * _callback - callback function which should be exectued after the standard handler
 */
ElevenRox.prototype._send = function (_req, _callback) {

	var obj = this,
	    send_callback;

	// standard landing always hit
	send_callback = function(_resp) {

		var req = _req
		    cb = _callback,

		obj._resp_landing(_resp,req,cb);
	};

	_req.id = this.request_id++;

	// add tokens to request
	if (this.token) {
		_req.params.token = this.token;
	}

	if (this.timesheet_token) {
		_req.params.timesheet_token = this.timesheet_token;
	}

	// make the request
	// TODO - HTTP erros?
	jQuery.post(this.url, JSON.stringify(_req), send_callback, "json");
};

/*
 * Public functions
 */

/*
 * Logs in and builds the data model, must be called before any other public functions
 *
 * _date     - do we want to initialise the timesheet for a specific date?
 * _callback -
 */
ElevenRox.prototype.init = function(_date,_callback) {

	var fn = 'ElevenRox.init: ',
	    obj = this,
	    init_cb;

	if (this.inited) {
		console.log(fn + 'already inited');
		_callback();
	}

	init_cb = function() {
		var d = _date,
		    cb = _callback;
		obj.init(d,cb);
	};

	// TODO - what if either of these fail?
	// have we logged in yet?
	if (!this._is_logged_in()) {
		this._login(init_cb);
		return;
	}

	// have we built the data model yet?
	if (!this._has_data_model()) {
		this.date = _date;
		this._build_data_model(init_cb);
		return;
	};

	// if we've got this far we must have init'd
	this.inited = true;
	_callback();
};

/*
 * Allows static login before init
 */
ElevenRox.prototype.login = function(_callback) {

	this._login(_callback);
};

/*
 * Returns a timesheet object representing the current timesheet
 */
ElevenRox.prototype.get_timesheet = function(_date) {

	this._check_init();

	return this.timesheet;
};

/*
 * Reset the current timesheet (to a specific date)
 *
 * _date     -
 * _callback -
 */
ElevenRox.prototype.reset_timesheet = function(_date,_callback) {

	this._check_init();
	this.date = _date;
	this._build_data_model(_callback);
};

/*
 * Add a timeentry
 *
 * _timeentry - timeentry to add
 * _callback  -
 */
ElevenRox.prototype.add_timeentry = function(_timeentry,_callback) {

	var req;

	this._check_init();

	// TODO - validation
	//      - does aaID exist in the timesheet?
	//      - do we have an entry date?

	req = this._build_set_time_request(
		_timeentry.assignment_attribute_id,
		_timeentry.time,
		undefined,
		_timeentry.entry_date,
		_timeentry.get_comment()
	);

	this.send(req, callback);

};

/*
 * Update a timeentry
 *
 * _timeentry - timeentry to update
 * _callback  -
 */
ElevenRox.prototype.update_timeentry = function(_timeentry,_callback) {

	var req;

	this._check_init();

	// TODO - validation
	//      - does aaID exist in the timesheet?
	//      - do we have an entry id?

	req = this._build_set_time_request(
		_timeentry.assignment_attribute_id,
		_timeentry.time,
		_timeentry.entry_id,
		undefined,
		_timeentry.get_comment()
	);

	this.send(req, callback);
};

/*
 * Return assignment(s) based on a string match on the name
 */
ElevenRox.prototype.get_assignment_by_name = function(_name) {

	var as = [],
	    a;

	for (var i = 0; i < this.timesheet.assignments.length; i++) {

		a = this.timesheet.assignments[i];

		if (a.name.search(_name) > -1) {
			as.push(a);
		}
	}

	// return any matching requirements
	if (as.length) {
		return as;
	}

	return null;
};

/*
 * Returns a timeentry relating to the given assignment on the given date
 *
 * _assignment        -
 * _date (DD/MM/YYYY) -
 */
ElevenRox.prototype.get_timeentry = function(_assignment,_date) {

	var t;

	for (var i = 0; i < this.timesheet.timeentries.length; i++) {

		t = this.timesheet.timeentries[i];

		if (t.assignment_id == _assignment.id && t.date == _date) {
			return t;
		}
	}

	return null;
};

/*
 * Returns the total time recorded on the timesheet (seconds)
 */
ElevenRox.prototype.get_total_time = function() {

	var time = 0.0;

	for (var i = 0; i < this.timesheet.timeentries.length; i++) {
		time += this.timesheet.timeentries[i].time;
	}

	return time;
};

/*
 * Returns the total time recorded on the timesheet for a given day (seconds)
 */
ElevenRox.prototype.get_total_time_for_date = function(_date) {

	var time = 0.0,
	    t;

	for (var i = 0; i < this.timesheet.timeentries.length; i++) {
		t = this.timesheet.timeentries[i];
		if (t.date == _date) {
			time += this.timesheet.timeentries[i].time;
		}
	}

	return time;
};

/*
 * convert a tenrox time field (e.g. 1.5) to a number of seconds
 */
ElevenRox.prototype.convert_to_seconds = function(_tenrox_time) {

	var minutes = 60 * _tenrox_time,
	    seconds = 60 * minutes;

	return seconds;
};

/*
 * convert seconds to a tenrox time field
 */
ElevenRox.prototype.convert_to_tenrox_time = function(_seconds) {

	var minutes = _seconds / 60,
	    tenrox_time = minutes / 60;

	return tenrox_time;
};


