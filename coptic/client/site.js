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

var modiDate = new Date(document.lastModified);
var showAs = (modiDate.getMonth() + 1) + "-" + modiDate.getDate() + "-" + modiDate.getFullYear();
$("#lastupdate").html("Page last updated: " + showAs);


});
})(jQuery);
