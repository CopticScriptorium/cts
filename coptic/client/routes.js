/*
 * Routes for client-side angular application
 */

angular.module("coptic")
  .config(function($routeProvider, $locationProvider) {
    $locationProvider.html5Mode({
        enabled : true,
        requireBase : false
      });
    $routeProvider.
      // Single text with HTML Version
      when('/texts/:corpus_slug/:text_slug/:html_version', {
        controller: 'TextController'
      }).
      // Single text
      when('/texts/:corpus_slug/:text_slug', {
        controller: 'TextController'
      }).
      // Text index
      when('/texts/', {
        controller: 'TextController'
      }).
      // Filter with search tools
      when('/filter/:filters', {
        controller: 'TextController'
      }).
      // Filter with search tools
      when('/urn*coptic_urn', {
        controller: 'TextController'
      }).
      // Otherwise, index
      otherwise({
        redirectTo: '/'
      });
  });