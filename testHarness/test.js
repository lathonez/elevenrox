// contains logic specific to the test harness
var url = "http://davonez.zapto.org/elevenRox";

var request = {};

function test_login(username, password) {
	request.method = "login";

	request.params = {};
	request.params.username = "shazleto";
	request.params.password = "cRo8VzZK";

	request.id = 1;

	send(request);
}

function handle(_resp) {

	var txt = document.getElementsByTagName('textarea')[0];

	// run the html5 modeller
	var json = JSON.stringify(_resp),
		model = JSON.parse(json),
		isIE = /msie/i.test(navigator.userAgent) && !/opera/i.test(navigator.userAgent);

	$('content').innerHTML = val(model);
	txt.innerHTML = enc(json);

	// show stuff
	jQuery('#show_json_lnk').css('display','block');
	jQuery("body").removeClass('loading');
};

function send(_req) {

	var txt = document.getElementsByTagName('textarea')[0];

	// hide stuff
	jQuery('#show_json_lnk').css('display','none');
	$('content').innerHTML = '';
	txt.innerHTML = '';
	jQuery('body').addClass('loading');

	// make the request
	jQuery.post(url, JSON.stringify(_req), handle, "json");
};


