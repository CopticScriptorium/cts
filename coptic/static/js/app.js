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
    .controller('TextController', ['$scope', '$http', '$location', function ($scope, $http, $location) {

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

        // The free text search from the search tools text search input field
        $scope.text_search = "";

        /*
         * Run update after each location change for controller lifecycle logic
         */
        $scope.$on('$locationChangeSuccess', function (e) {
            $scope.update();
        });

        /*
         *  Watch the selected text to determine when Selected Text templating completes
         */
        $scope.$watch(
            function () {
                return document.getElementById("selected_text").innerHTML
            },
            function (val) {
                if ($(".text-format").length > 0) {
                    if ($scope.path.length >= 4) {
                        if ($scope.path[4] !== $scope.selected_text_format) {
                            $scope.show_selected_visualization($scope.path[4]);
                        }
                    }
                }
            }
        );

        /*
         *  Update: manages primary lifecycle
         */
        $scope.update = function () {
            console.log('Update function, location path: ' + location.pathname);
            $scope.path = location.pathname.split("/");

            function wipe_search_terms_and_filters() {
                $scope.filters = [];
                $(".selected").removeClass("selected");
            }

            if ($scope.path.length == 0 || ( $scope.path.length > 1 && $scope.path[1] === "" )) { // Index
                $scope.selected_text = null;
                $scope.corpora = [];
                wipe_search_terms_and_filters();
            } else if (location.pathname.substr(0, 5) === "/urn:") {
                $http.get("/api/", {
                    params: {
                        model:      'urn',
                        urn_value:  location.pathname.substr(1)
                    }
                }).then(function (response) {
                    $scope.selected_text = null;
                    $scope.selected_text_format = null;
                    $scope.corpora = response.data.corpus;
                    console.log(response);
                }, function (response) {
                    console.log('Error with API Query:', response);
                });
            } else if ($scope.path.length === 2 && $scope.path[1] !== "404") { // texts index
                $scope.selected_text = null;
                $scope.selected_text_format = null;
                $scope.corpora = [];
                wipe_search_terms_and_filters();
            } else if ($scope.path.length === 3) { // /filter/:filters
                if ($scope.path[2].length !== 0) {
                    $scope.load_filters();
                    $scope.selected_text = null;
                    $scope.selected_text_format = null;
                } else {
                    $scope.corpora = [];
                    wipe_search_terms_and_filters();
                }
            } else if ($scope.path.length === 4) { // Single text (/texts/:corpus_slug/:text_slug)
                $(".text-format").hide();
                $scope.selected_text_format = null;
                if ($scope.corpora.length) {
                    $scope.show_single();
                } else {
                    $scope.get_corpora({
                        model:   "corpus",
                        filters: $scope.filters
                    });
                }
            } else if ($scope.path.length === 5) { // Single text html version (/texts/:corpus_slug/:text_slug/:html_version)
                if ($scope.selected_text) {
                    $scope.show_selected_visualization($scope.path[4]);
                } else {
                    $scope.show_single();
                }
            }
        };

        $scope.get_corpora = function (query) {
            $(".text-subwork")      .removeClass("hidden");
            $(".text-work")         .removeClass("hidden");
            $(".work-title-wrap")   .removeClass("hidden");
            $(".single-header")     .removeClass("single-header");

            $http.get("/api/", {params: query}).then(function (response) {
                $scope.handle_corpora_results(response.data.corpus);
                if ($scope.selected_text && $scope.path[4] !== $scope.selected_text_format) {
                    $scope.show_single();
                }
            }, function (response) {
                console.log('Error with API Query:', response);
            });
        };

        $scope.change_dom = function() {
            // Toggle the specific classes and visibility on elements
            var $target = $(".text-subwork[data-text-slug='" + $scope.text_query.text_slug + "'][data-corpus-slug='" +
                $scope.text_query.corpus_slug + "']");
            $(".text-subwork")              .addClass("hidden");
            $(".text-work")                 .addClass("hidden");
            $(".work-title-wrap")           .addClass("hidden");
            $target.parents(".text-work")   .removeClass("hidden");
            $target.removeClass("hidden")   .addClass("single-header");
        };

        $scope.handle_corpora_results = function(corpora) {
            $scope.corpora = corpora;

            if ($scope.selected_text) {
                $scope.change_dom();
            }
        };

        $scope.handle_text_results = function(text) {

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
                }
            }

            $scope.selected_text = text;
            $scope.filters = [];
            text.text_meta.forEach(add_properties_from_metadata);
            $scope.change_dom();
            $('html,body').scrollTop(0);
        };

        $scope.show_single = function () {
            $(".text-format").hide();
            $scope.text_query = {
                model:          "texts",
                corpus_slug:    $scope.path[2],
                text_slug:      $scope.path[3]
            };

            $http.get("/api/", {params: $scope.text_query}).then(
                function(response) {
                    $scope.handle_text_results(response.data.text)
                },
                function(response) {
                    console.log('Error with API Query:', response);
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
                , search_obj = {}
                , filters_url = []
                , filter
                , field
                , id
                ;

            $scope.text_query = {};

            if (!$target.hasClass("tool-search-item")) {
                $target = $target.parents(".tool-search-item");
            }

            filter = $target.data().filter;
            id = $target.data().searchid;
            field = $target.parents(".tool-wrap").data().field;
            search_obj = {
                id: id,
                filter: filter,
                field: field
            };

            if (!$target.hasClass("selected")) {
                $target.addClass("selected");
                $scope.filters.push(search_obj);
            } else {
                $target.removeClass("selected");
                $scope.filters = $scope.filters.filter(function (obj) {
                    return obj.filter !== search_obj.filter;
                });
            }

            $scope.filters.forEach(function (f) {
                filters_url.push(f.field + "=" + f.id + ":" + f.filter);
            });
            filters_url = filters_url.join("&");
            $location.path("/filter/" + filters_url);

            $scope.text_query = {
                model: "corpus",
                filters: $scope.filters
            };

            $scope.selected_text = null;
        };

        $scope.load_filters = function () {
            // load the filters from the URL to the object
            var filter_url = $scope.path[2].split("&");

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

                    if (filter[0] === "text_search") {
                        $(".text-search-input").val(filter_value[1]);
                        $scope.text_search = filter_value[1];
                    }
                }
            });

            $scope.text_query = {
                model: "corpus",
                filters: $scope.filters
            };

            $scope.selected_text = null;
            $scope.get_corpora($scope.text_query);
        };

        $scope.remove_search_term = function (e) {
            var $target = $(e.target)
                , filter
                , field
                , filters_url = []
                ;

            if (!$target.hasClass("filter-item")) {
                $target = $target.parents(".filter-item");
            }

            filter = $target.data().filter;
            field = $target.data().field;

            $(".tool-search-item[data-filter='" + filter + "']").removeClass("selected");
            $scope.filters = $scope.filters.filter(function (obj) {
                return obj.filter !== filter;
            });

            if (field === "text_search") {
                $(".text-search-input").val('');
                $scope.text_search = "";
            }

            $scope.text_query = {
                model: "corpus",
                filters: $scope.filters
            };

            $scope.filters.forEach(function (f) {
                filters_url.push(f.field + "=" + f.id + ":" + f.filter);
            });
            filters_url = filters_url.join("&");

            if ($scope.filters.length > 0) {
                $location.path("/filter/" + filters_url);
                $scope.get_corpora($scope.text_query);

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

                $(".selected-text-format").fadeOut().removeClass("selected-text-format");
                $("#" + type).fadeIn().addClass("selected-text-format");
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
