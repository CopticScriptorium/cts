angular.module('coptic', ['csFilters', 'ngSanitize', 'ngRoute', 'headroom']).config(function ($sceDelegateProvider) {
    $sceDelegateProvider.resourceUrlWhitelist([
        'self',
        'https://corpling.uis.georgetown.edu/**']);
});

angular.module('csFilters', [])

    .filter('capitalize', function () {
        return function (input, all) {
            return (!!input) ? input.replace(/([^\W_]+[^\s-]*) */g, function (txt) {
                return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
            }) : '';
        }
    })

    .filter('slugify', function () {
        return function (input, all) {
            return (!!input) ? input
                .toLowerCase()
                .replace(/[^\w ]+/g, '')
                .replace(/ +/g, '-')
                : '';
        }
    })

    // Trust HTML for ng-bind
    .filter('unsafe', function ($sce) {
        return $sce.trustAsHtml;
    });

angular.module("coptic")
    .config(function ($routeProvider, $locationProvider) {
        $locationProvider.html5Mode({
            enabled: true,
            requireBase: false
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

/*
 * Site-specific functions
 */

(function ($) {
    angular.element(document).ready(function () {

        window.__cs__ = window.__cs__ || {};
        var Cs = window.__cs__;

// fix iOS font related issues 
        if (navigator.userAgent.match(/iPad/i)) {
            $("html").addClass("ipad");
        }

// js - modernizer
        $('.no-js').removeClass('no-js').addClass('js');

        var modiDate = new Date(document.lastModified);
        var showAs = (modiDate.getMonth() + 1) + "-" + modiDate.getDate() + "-" + modiDate.getFullYear();
        $("#lastupdate").html("Page last updated: " + showAs);
    });
})(jQuery);

/*
 * Text controller, primary application controller for single / list toggling 
 * and search tool functionality
 */
angular.module('coptic')
    .controller('TextController', ['$scope', '$http', '$location', '$interval', '$log',
        function ($scope, $http, $location, $interval, $log) {

        // Persistent location Path
        $scope.path = location.pathname.split("/");

        // Filters for the search tools
        $scope.filters = [];

        // Text Query based on filters and selected texts
        $scope.text_query = {};

        // The corpora returned from the API
        $scope.corpora = [];

        // The selected text value for single text view
        $scope.selected_text = null;

        // The selected text HTML visualization format
        $scope.selected_text_format = "";

        // The URN entered in the header URN input field
        $scope.entered_urn = "";

        /*
         * Run update after each location change for controller lifecycle logic
         */
        $scope.$on('$locationChangeSuccess', function (e) {
            $scope.path = location.pathname.split("/");
            var elems = $scope.path.length;
            $log.debug('$locationChangeSuccess, location path: ' + location.pathname);
            $log.debug('Corpora:', $scope.corpora);
            $log.debug('selected text:', $scope.selected_text);

            function wipe_search_terms_and_filters() {
                $scope.filters = [];
                $(".selected").removeClass("selected");
            }

            if (elems == 0 || ( elems > 1 && $scope.path[1] === "" )) { // Index
                $scope.selected_text = null;
                $scope.corpora = [];
                wipe_search_terms_and_filters();
            } else if ($scope.is_urn_request()) {
                $http.get("/api/", {
                    params: {
                        model:      'urn',
                        urn_value:  location.pathname.substr(1)
                    }
                }).then(function (response) {
                    $scope.corpora = response.data.corpus;
                    $log.debug(response);
                    $scope.selected_text_format = null;
                    if ($scope.corpora.length == 1 && $scope.corpora[0].texts.length == 1) {
                        $scope.selected_text = $scope.corpora[0].texts[0];
                        $scope.show_single($scope.corpora[0].slug, $scope.selected_text.slug);
                    } else {
                        $scope.selected_text = null;
                    }
                }, function (response) {
                    $log.debug('Error with API Query:', response);
                });
            } else if (elems === 2 && $scope.path[1] !== "404") { // texts index
                $scope.selected_text = null;
                $scope.selected_text_format = null;
                $scope.corpora = [];
                wipe_search_terms_and_filters();
            } else if (elems === 3) { // /filter/:filters
                if ($scope.path[2].length !== 0) {
                    $scope.load_filters();
                    $scope.selected_text = null;
                    $scope.selected_text_format = null;
                } else {
                    $scope.corpora = [];
                    wipe_search_terms_and_filters();
                }
            } else if (elems === 4) { // Single text (/texts/:corpus_slug/:text_slug)
                $log.debug('Single text (/texts/:corpus_slug/:text_slug');
                $scope.selected_text_format = null;
                $scope.show_single($scope.path[2], $scope.path[3]);
            } else if (elems === 5) { // Single text html version (/texts/:corpus_slug/:text_slug/:html_version)
                $log.debug('Single text html version (/texts/:corpus_slug/:text_slug/:html_version');
                if ($scope.selected_text) {
                    $scope.show_selected_visualization($scope.path[4]);
                } else {
                    $scope.show_single($scope.path[2], $scope.path[3]);
                }
            }
        });

        $scope.is_urn_request = function() {
            return location.pathname.substr(0, 5) === "/urn:"
        };

        $scope.are_no_expected_results = function() {
            return ($scope.filters.length || $scope.is_urn_request()) && ! $scope.corpora.length;
        };

        $scope.should_show_description = function() {
            return ! ($scope.are_no_expected_results() || $scope.filters.length ||
                $scope.corpora.length || $scope.selected_text)
        };

        $scope.get_corpora = function() {
            $log.debug('get_corpora', $scope.text_query);
            $http.get("/api/", {params: $scope.text_query}).then(function (response) {
                $scope.corpora = response.data.corpus;
                if ($scope.selected_text && $scope.path[4] !== $scope.selected_text_format) {
                    $scope.show_single($scope.path[2], $scope.path[3]);
                }
            }, function (response) {
                $log.debug('Error with API Query:', response);
            });
        };

        $scope.show_single = function(corpus_slug, text_slug) {
            $scope.text_query = {
                model:          "texts",
                corpus_slug:    corpus_slug,
                text_slug:      text_slug
            };
            $log.debug('show_single', $scope.text_query);

            $http.get("/api/", {params: $scope.text_query}).then(
                function(response) {
                    var text = response.data.text;

                    function add_properties_from_metadata(textmeta) {
                        var urn_parts;
                        var urn_dot_parts;
                        if (textmeta.name === "document_cts_urn") {
                            urn_parts       = textmeta.value.split(":");
                            urn_dot_parts   = urn_parts[3].split(".");

                            text.urn_cts_work   = urn_parts.slice(0, 3).join(":"); // e.g., "urn:cts:copticLit"
                            text.edition_urn    = textmeta.value;
                            text.textgroup_urn  = urn_dot_parts[0];
                            text.corpus_urn     = urn_dot_parts[1];
                            text.text_url       = "texts/" + text.corpus.slug + "/" + text.slug
                        } else if (textmeta.name === "endnote") {
                            text.endnote = textmeta.value;
                        } else if (textmeta.name === "next") {
                            text.next = textmeta.value;
                        } else if (textmeta.name === "previous") {
                            text.previous = textmeta.value;
                        }
                    }

                    if (! text) {
                        $location.path("/");
                    } else {
                        $scope.selected_text = text;
                        $scope.filters = [];
                        text.text_meta.forEach(add_properties_from_metadata);
                        if ($scope.path.length === 5) {
                            // This is a kludge coming from my Angular ignorance. Calling show_selected_visualization
                            // synchronously doesn’t work, I presume because the DOM isn’t yet set up as expected. -- dcb
                            // todo Find a better way.
                            $interval(function () {
                                $scope.show_selected_visualization($scope.path[4]);
                            }, 1, 1);
                        }
                        $('html,body').scrollTop(0);
                    }
                },
                function(response) {
                    $log.debug('Error with API Query:', response);
                });
        };

        $scope.toggle_tool_panel = function (e) {
            // Toggle the search tool panels
            var $target = $(e.target)
                , $panel
                ;

            if (!$target.hasClass("tool-head")) {
                $target = $target.parents(".tool-head");
            }

            $panel = $target.parents(".tool-wrap").children(".tool-panel");
            $(".keys-shown").removeClass("keys-shown");

            if ($panel.hasClass("hidden")) {
                $(".tool-panel").addClass("hidden");
                $(".tool-head-selected").removeClass("tool-head-selected");
                $target.addClass("tool-head-selected");
                $panel.removeClass("hidden");
            } else {
                $target.removeClass("tool-head-selected");
                $panel.addClass("hidden");
            }
        };

        $scope.toggle_search_term = function (e) {
            var $target = $(e.target)
                , filters_url_parts = []
                , filter
                ;

            $scope.text_query = {};

            if (!$target.hasClass("tool-search-item")) {
                $target = $target.parents(".tool-search-item");
            }

            filter = $target.data().filter;

            if (!$target.hasClass("selected")) {
                $target.addClass("selected");
                $scope.filters.push({
                    id:     $target.data().searchid,
                    filter: filter,
                    field:  $target.parents(".tool-wrap").data().field
                });
            } else {
                $target.removeClass("selected");
                $scope.filters = $scope.filters.filter(function (obj) {
                    return obj.filter !== filter;
                });
            }

            $scope.filters.forEach(function (f) {
                filters_url_parts.push(f.field + "=" + f.id + ":" + f.filter);
            });
            $location.path("/filter/" + filters_url_parts.join("&"));
        };

        $scope.load_filters = function () {
            // load the filters from the URL to the object
            var filter_url = $scope.path[2].split("&");
            $log.debug('load_filters', filter_url);

            $scope.filters = [];

            // Process filter URLs
            filter_url.forEach(function (filter) {
                var filter_value;
                filter = decodeURI(filter);
                filter = filter.split("=");

                // if filter contains a key val pair demarcated by =
                if (filter.length > 1) {
                    filter_value = filter[1].split(":");

                    $scope.filters.push({
                        id: filter_value[0],
                        filter: filter_value[1],
                        field: filter[0]
                    });
                    $(".tool-search-item[data-searchid='" + filter_value[0] + "']").addClass("selected");
                }
            });

            $scope.text_query = {
                model: "corpus",
                filters: $scope.filters
            };

            $scope.selected_text = null;
            $scope.get_corpora();
        };

        $scope.remove_search_term = function (e) {
            var $target = $(e.target)
                , filter
                , filters_url = []
                ;

            if (!$target.hasClass("filter-item")) {
                $target = $target.parents(".filter-item");
            }

            filter = $target.data().filter;

            $(".tool-search-item[data-filter='" + filter + "']").removeClass("selected");
            $scope.filters = $scope.filters.filter(function (obj) {
                return obj.filter !== filter;
            });

            $scope.filters.forEach(function (f) {
                filters_url.push(f.field + "=" + f.id + ":" + f.filter);
            });
            filters_url = filters_url.join("&");

            if ($scope.filters.length > 0) {
                $location.path("/filter/" + filters_url);
            } else {
                $location.path("/");
                $scope.corpora = [];
            }
        };

        $scope.clear_all_search_terms = function () {
            $location.path("/");
        };

        $scope.show_selected_visualization = function (type) {
            var $target = $(".single-header .text-item[data-type=" + type + "]");
            $scope.selected_text_format = type;
            if (!$target.hasClass("selected-text-type")) {
                $(".selected-text-type").removeClass("selected-text-type");
                $target.addClass("selected-text-type");

                $(".selected-text-format").hide().removeClass("selected-text-format");
                $("#" + type).show().addClass("selected-text-format");
            }
        };

        $scope.raise_dropdowns = function () {
            $(".tool-panel").addClass("hidden");
        };

        $scope.urn_submit = function () {
            var urn = $scope.entered_urn;
            var urn_prefix = "urn:";
            if (urn.substr(0, urn_prefix.length) !== urn_prefix) {
                urn = urn_prefix + urn;
            }
            document.location.href = "/" + urn;
        };
    }]);
