/*
 *
 * Site.js - site specific functions 
 *
 */

(function($){
angular.element(document).ready(function() {

window.__cs__ = window.__cs__ || {};
var Cs = window.__cs__;

// fix iOS font related issues 
if(navigator.userAgent.match(/iPad/i)){
	$("html").addClass("ipad");
}

// js - modernizer
$('.no-js').removeClass('no-js').addClass('js');


});
})(jQuery);
