angular.module('csFilters', [])

	// Captialize filter
	.filter('capitalize', function() {
		return function(input, all) {
			return (!!input) ? input.replace(/([^\W_]+[^\s-]*) */g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();}) : '';
		}
	})

	// Turn input string into slug
	.filter('slugify', function() {
		return function(input, all) {
			return (!!input) ? input 
				    .toLowerCase()
				    .replace(/[^\w ]+/g,'')
				    .replace(/ +/g,'-')
						 : '';
		}
	})


	// Trust HTML for ng-bind
	.filter('unsafe', function($sce) { 
		return $sce.trustAsHtml; 
	});

 
