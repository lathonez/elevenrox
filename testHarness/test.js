// contains logic specific to the test harness
var url = "http://davonez.zapto.org/elevenRox";

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

	var request = {};

	request.method = "login";
	request.params = {};
	request.params.username = $('login.username').value;
	request.params.password = $('login.password').value;

	request.id = 1;

	send(request);
};

function test_get_time() {

	var request = {};

	request.method = "get_time";
	request.params = {};
	request.params.token = $('get_time.token').value;

	request.id = 2;

	send(request);
};

function test_set_time() {

	var request = {};

	request.method = "set_time";
	request.params = {};
	request.params.assignment_id   = $('set_time.assignment_id').value;
	request.params.entry_date      = $('set_time.entry_date').value;
	request.params.time            = $('set_time.time').value;
	request.params.timesheet_token = $('set_time.timesheet_token').value;
	request.params.token           = $('set_time.token').value;

	// if any of these are empty string, we don't actually want to send them
	$.each(['overtime','double_ot','is_etc','enst'], function(i,v) {
		if (eval('$(\'set_time.' + v + '\').value') != '') {
			eval('request.params.' + v + '= v');
		}
	});

	request.id = 3;

	send(request);
};

function test_complete() {

	var request = {};

	request.method = "complete";
	request.params = {};
	request.params.timesheet_token = $('complete.timesheet_token').value;
	request.params.token           = $('complete.token').value;

	request.id = 4;

	send(request);
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

	// make the request
	jQuery.post(url, JSON.stringify(_req), handle, "json");
};

function fill(_resp) {

	var token,
	    timesheet_token,
	    assignment_id,
	    entry_date,
	    idx;

	if (_resp && _resp.result && typeof _resp.result != 'undefined') {

		// token
		if (typeof _resp.result.token != 'undefined') {
			token = _resp.result.token;
		}

		// timesheet token
		if (typeof _resp.result.timesheet_token != 'undefined') {
			token = _resp.result.token;
		}

		// assignment id, entry date
		if (
		    typeof _resp.result.timesheet != 'undefined' &&
		    typeof _resp.result.timesheet.timeentries != 'undefined'
		) {
			idx = _get_random(0,_resp.result.timesheet.timeentries.length);
			assignment_id = _resp.result.timesheet.timeentries[idx].assignment_attribute_id;
			entry_date = _format_date(_resp.result.timesheet.timeentries[idx].entry_date);
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

	if (assignment_id) {
		$('set_time.assignment_id').value = assignment_id;
	}

	if (entry_date) {
		$('set_time.entry_date').value = entry_date;
	}
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

	while (r >= end) {
		r = Math.random() * 10;
	}

	return Math.round(r);
};
