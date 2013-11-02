// contains logic specific to the test harness
var url = "/elevenRox",
    er = new ElevenRox(
		undefined,
		undefined,
		url
	);

	er.test_mode = true;

function clear_all() {

	var txt = $$('textarea')[0];

	$('content').innerHTML = '';
	txt.innerHTML = '';
};

function reset() {

	clear_all();

	// hide the json link
	jQuery('#json_lnk').css('display','none');
	jQuery('#reset_lnk').css('display','none');

	// show all the input param forms again
	jQuery('#login_lnk').css('display','inline');
	jQuery('#get_time_lnk').css('display','inline');
	jQuery('#set_time_lnk').css('display','inline');
	jQuery('#complete_lnk').css('display','inline');

	jQuery('#top_param_forms').css('display','block');
	jQuery('#bottom_param_forms').css('display','block');
	jQuery('#bottom_lnks').css('display','block');
};

function test_login() {

	var username = $('login.username').value,
	    password = $('login.password').value,
	    req      = er._build_login_request(username,password);

	send(req);
};

function test_get_time() {

	var start_date          = $('get_time.start_date').value,
	    reorder_timeentries = new Boolean($('get_time.reorder_timeentries').value),
	    token               = $('get_time.token').value,
	    req                 = er._build_get_time_request(start_date,reorder_timeentries);

	_check_tokens(token);

	send(req);

};

function test_set_time() {

	var assignment_attribute_id = $('set_time.assignment_attribute_id').value,
	    entry_id                = $('set_time.entry_id').value,
	    entry_date              = $('set_time.entry_date').value,
	    time                    = $('set_time.time').value,
	    comment                 = $('set_time.comment').value,
	    comment_id              = $('set_time.comment_id').value,
	    token                   = $('set_time.token').value,
	    timesheet_token         = $('set_time.timesheet_token').value,
	    req;

	// overwrite empty string with null
	if (comment_id == '') {
		comment_id = null;
	}

	// if any of these are empty string, we don't actually want to send them
	$.each(['overtime','double_ot','is_etc','enst'], function(i,v) {
		if (eval('$(\'set_time.' + v + '\').value') != '') {
			eval(v + '= v');
		}
	});

	req = er._build_set_time_request(
		assignment_attribute_id,
		time,
		entry_id,
		entry_date,
		comment
	);

	_check_tokens(token,timesheet_token);

	send(req);
};

function test_complete() {

	//TODO
};

function handle(_resp) {

	var txt = $$('textarea')[0];

	// run the html5 modeller
	var json = JSON.stringify(_resp),
		model = JSON.parse(json);

	$('content').innerHTML = val(model);
	txt.innerHTML = enc(json);

	// show stuff
	jQuery('#reset_lnk').css('display','inline');
	jQuery('#json_lnk').css('display','inline');
	jQuery("body").removeClass('loading');

	// attempt to auto fill any dynamic fields on the page
	fill(_resp);
};

// hide stuff
function set_loading() {

	jQuery('#json_lnk').css('display','none');
	jQuery('#top_param_forms').css('display','none');
	jQuery('#bottom_param_forms').css('display','none');
	jQuery('#bottom_lnks').css('display','none');
	jQuery('#login_lnk').css('display','none');
	jQuery('#get_time_lnk').css('display','none');
	jQuery('#set_time_lnk').css('display','none');
	jQuery('#complete_lnk').css('display','none');
	jQuery('body').addClass('loading');
};

function send(_req) {

	clear_all();

	set_loading();

	er._send(_req,handle)
};

function fill(_resp) {

	var token,
	    timesheet_token,
	    assignment_attribute_id,
	    entry_id,
	    entry_date,
	    idx,
	    timeentry,
	    timeentries,
	    note;

	if (_resp && _resp.result && _resp.result !== undefined) {

		// token
		if (_resp.result.token !== undefined) {
			token = _resp.result.token;
		}

		// timesheet token
		if (_resp.result.timesheet_token !== undefined) {
			timesheet_token = _resp.result.timesheet_token;
		}

		// if we've not got anything yet, pick an assignment at random, this will be a new entry
		if (!assignment_attribute_id &&
			_resp.result.timesheet !== undefined &&
			_resp.result.timesheet.assignments !== undefined
		) {

			timeentries = [];

			// find an assignment with a timeentry
			$.each(_resp.result.timesheet.assignments, function(i,a) {
				if (a.timeentries !== undefined) {
					$.each(a.timeentries, function(i,t) {
						timeentries.push(t);
					});
				}
			});

			// try to find an assignment with a timeentry and a comment
			// let's try to find something with a comment
			$.each(timeentries, function(i,t) {
				if (t.notes !== undefined && t.notes.length) {
					timeentry = t;
					note = timeentry.notes[0];
					return;
				}
			});

			// if we didn't find a timeentry with a comment, pick a random
			if (!timeentry) {
				idx = _get_random(0,timeentries.length);
				timeentry = timeentries[idx];
			}

			if (timeentry) {
				assignment_attribute_id = timeentry.assignment_attribute_id;
				entry_id = timeentry.entry_id;
				entry_date = _format_date(timeentry.entry_date);
			} else {
				idx = _get_random(0,_resp.result.timesheet.assignments.length);
				assignment_attribute_id = _resp.result.timesheet.assignments[idx].assignment_attribute_id;
				entry_date = _current();
			}
		}
	}

	if (token) {
		$('get_time.token').value = token;
		$('set_time.token').value = token;
		$('complete.token').value = token;
	}

	if (timesheet_token) {
		$('set_time.timesheet_token').value = timesheet_token;
		$('complete.timesheet_token').value = timesheet_token;
	}

	if (entry_id) {
		$('set_time.entry_id').value = entry_id;
	}

	if (assignment_attribute_id) {
		$('set_time.assignment_attribute_id').value = assignment_attribute_id;
	}

	if (entry_date) {
		$('set_time.entry_date').value = entry_date;
	}

	if (note) {
		$('set_time.comment').value = note.d;
		$('set_time.comment_id').value = note.uid;
	}
};

// return today DD/MM/YYYY
function _current() {

	var current = new Date()
	    d = current.getDate(),
	    m = current.getMonth() + 1,
	    y = current.getFullYear();

	// format with leading 0
	if (d < 10) {
		d = '0' + d;
	}

	if (m < 10) {
		m = '0' + m;
	}

	formatted = d + '/' + m + '/' + y;

	return formatted;
};

// turn MM/DD/YYYY into DD/MM/YYYY
function _format_date(date) {

	var fn = '_format_date: ',
	    date_arr = date.split('/'),
	    formatted;

	if (date_arr.length != 3) {
		console.log(fn + 'invalid date - ' + date);
		return date;
	}

	formatted = date_arr[1] + '/' + date_arr[0] + '/' +  date_arr[2];

	return formatted;
};

// return a random integer between start and end
function _get_random(start,end) {

	var r = end;

	if (start == end) {
		return end;
	}

	while (r >= end) {
		r = Math.random() * 10;
	}

	return Math.floor(r);
};

// using elevenrox_js, the session management is internal
// this lets us override the internal tokens for testing purposes
function _check_tokens(_token,_timesheet_token) {

	var fn = '_check_tokens: ',
	    token           = (typeof _token === undefined ? null : _token),
	    timesheet_token = (typeof _timesheet_token === undefined ? null : _timesheet_token);

	if (token && token != er.token) {
		console.log(fn + 'overwriting token ' + er.token + ' with ' + token);
		er.token = token;
	}

	if (timesheet_token && timesheet_token != er.timesheet_token) {
		console.log(fn + 'overwriting timesheet token ' + er.timesheet_token + ' with ' + timesheet_token);
		er.timesheet_token = timesheet_token;
	}
};
