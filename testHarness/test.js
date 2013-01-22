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
	jQuery('#param_forms').css('display','block');
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

	// attempt to auto fill any token fields on the page
	fill_tokens(_resp);
};

function send(_req) {

	// hide stuff
	jQuery('#json_lnk').css('display','none');
	jQuery('#param_forms').css('display','none');
	jQuery('#login_lnk').css('display','none');
	jQuery('#get_time_lnk').css('display','none');
	jQuery('body').addClass('loading');

	clear_all();

	// make the request
	jQuery.post(url, JSON.stringify(_req), handle, "json");
};

function fill_tokens(_resp) {

	var token = null;

	if (
		typeof _resp.result != 'undefined' &&
		typeof _resp.result.token != 'undefined'
	) {
		token = _resp.result.token;
	}

	if (token) {
		$('get_time.token').value = token;
	}
};
