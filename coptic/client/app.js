/*
 * Initialize the angular application 
 * 
 */

angular.module('coptic', ['csFilters', 'ngSanitize', 'ngRoute', 'headroom']).config(function($sceDelegateProvider){

	$sceDelegateProvider.resourceUrlWhitelist([
		'self',
		'https://corpling.uis.georgetown.edu/**']);

});

