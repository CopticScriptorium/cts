/*
 * Text controller, primary application controller for single / list toggling 
 * and search tool functionality
 *
 */ 
angular.module('coptic')
	.controller('TextController', ['$scope', '$http', '$route', '$location', function($scope, $http, $route, $location) {

	// Set the environment to development or production 
	$scope.coptic_env = "development";

	// Persistent location Path
	$scope.path = location.pathname.split("/");

	// Filters for the search tools 
	$scope.filters = [];

	// Text Query based on filters and selected texts
	$scope.text_query = {};

	// The texts returned from the API
	$scope.texts = [];

	// Accepted models for the API
	$scope.models = ["ingests", "corpus", "texts"];

	// The selected text value for single text view
	$scope.selected_text = null;
	
	// If the application is in the single text view
	$scope.is_single = false;

	// The selected text HTML visualization format
	$scope.selected_text_format = "";

	// The URN entered in the header URN input field
	$scope.entered_urn = "";

	// The free text search from the search tools text search input field
	$scope.text_search = "";

	/*
	 * Run update after each location change for controller lifecycle logic
	 */
	$scope.$on('$locationChangeSuccess', function(e) {
		$scope.update();
	});

	/*
	 *  Watch the selected text to determine when Selected Text templating completes
	 */
	$scope.$watch(
			function(){return document.getElementById("selected_text").innerHTML},
			function(val){
				if ( $(".text-format").length > 0 ){

					if ( $scope.path.length < 4 ){
						$(".text-format").hide();
						$scope.hide_loading_modal();

					} else if ( $scope.path[3] !== $scope.selected_text_format ) {
						$(".text-format").hide();
						$scope.toggle_text_format( $scope.path[3] );
						$scope.hide_loading_modal();

					}else if ( $scope.selected_text_format === "" ){
						$(".text-format").hide();
						$scope.hide_loading_modal();

					}

				}
			}
		);

	/*
	 *  Watch the text search input in the search tools 
	 */
	$scope.$watch(
			function(){return $scope.text_search},
			function(val){
				/* 
				 * For now, disable the functionality of the text search until 
				 * it is resolved in the future to ANNIS
				 */
				// $scope.add_text_search();	
			}
		);

	/*
	 *  Update: manages primary lifecycle for the angular application 
	 */
	$scope.update = function() {
		$scope.path = location.pathname.split("/");

		// If the application location is index
		if( $scope.path.length == 0 || ( $scope.path.length > 1 && $scope.path[1] === "" ) ){
			// Index
			$scope.show_loading_modal();
			$scope.is_single = false;
			$scope.selected_text = null;

			// Default to displaying no texts, only show the landing page description text
			$scope.texts = [];
			$scope.hide_loading_modal();

			// Wipe Search Terms / Filters
			$scope.filters = [];
			$(".selected").removeClass("selected");
			$("meta[name=corpus_urn]").attr("content", "" );
			$("meta[name=document_urn]").attr("content", "" ); 
			$("meta[name=mss_urn]").attr("content", "" ); 


		// If the application location is /texts index
		}else if ( $scope.path.length === 2 ) {
			// /texts index
			$scope.show_loading_modal();
			$scope.is_single = false;
			$scope.selected_text = null;

			// Default to displaying no texts, only show the landing page description text
			$scope.texts = [];
			$scope.hide_loading_modal();

			// Wipe Search Terms / Filters
			$scope.filters = [];
			$(".selected").removeClass("selected");
			$("meta[name=corpus_urn]").attr("content", "" );
			$("meta[name=document_urn]").attr("content", "" ); 
			$("meta[name=mss_urn]").attr("content", "" ); 


		// If the application location is at /filters/:filters or /text/:slug
		}else if ( $scope.path.length === 3 ) {

			if ( $scope.path[1] === "filter" ){
				// Load filters
				$scope.load_filters();

			}else{
				// Single text (/text/:slug)
				$(".text-format").hide();
				$scope.show_loading_modal();
				$scope.is_single = true;
				$scope.get_corpora( {} );
			}


		// Single text html version (/text/:slug/:html_version)
		}else if ( $scope.path.length === 4 ) {
			if ( $scope.is_single === true ) {

				//$scope.selected_text_format = "";
				$scope.toggle_text_format( $scope.path[3] );

			}else {
				$scope.show_loading_modal();
				$scope.is_single = true;
				$scope.get_corpora( {} );
			}
		}

	};

	/*
	 * Corpora Query to API
	 *
	 *    -- Sends query object params
	 *    -- Receives object with array of corpus
	 *
	 */
	$scope.get_corpora = function( query ){

		if ( $scope.coptic_env === "development" ){
			console.log("Corpora Query:", query);
		}

		$scope.selected_text = null;
		$(".text-subwork").removeClass("hidden");
		$(".text-work").removeClass("hidden");
		$(".work-title-wrap").removeClass("hidden");
		$(".single-header").removeClass("single-header");

		// query the corpus
		$http({
				url : "/api/", 
				method : "GET",
				params : query 
			})
			.success(function(data, status, headers, config){

				// Log relevant data
				if ( $scope.coptic_env === "development" ){
						console.log("Corpora Response:", data);
				}

				// Update the texts with the returned data
				$scope.update_texts( data );

				// If the view is set to single text, show the single template
				if ( $scope.is_single ){
					$scope.show_single();

				// Otherwise, update the texts and hide the loading modal
				}else{
					$scope.hide_loading_modal();

				}

			})
			.error(function(error, status, headers, config){
				console.log('Error with API Query:', error);
			});

	};

	/*
	 * Text Query to API
	 *
	 *    -- Sends query object params
	 *    -- Receives object with array of texts 
	 *
	 */
	$scope.get_texts = function( query ){

		// Log relevant details (for development only)
		console.log("Texts Query", query);

		$http({
				url : "/api/", 
				method : "GET",
				params : query 
			})
			.success(function(data, status, headers, config){

				// Log the response data
				console.log( "Response", data);

				// Update texts with the response data
				$scope.update_texts( data );

			})
			.error(function(error, status, headers, config){
				console.log('Error with API Query:', error);
			});

	};

	/*
	 * Updates texts with returned data from API query
	 */
	$scope.update_texts = function( res ){
		var texts = []
		,	passage_urn
		;

		// If it is a corpus response 
		if ( typeof res.corpora !== "undefined" ){

			// Ensure that if the path is /, no texts are added (only the project
			// description text should be shown)
			if ( $scope.path.length > 0  ){
				res.corpora.forEach(function(corpus){
					texts.push( corpus );

				});

				$scope.texts = texts; 

			}else {
				$scope.texts = [];

			}


		// If it is a texts response
		}else if ( typeof res.texts !== "undefined" ) {

			// Should handle the possibility of multiple selected in future
			$scope.selected_text = res.texts[0];

			// Set pertinent metadata directly to the selected_text object
			$scope.selected_text.text_meta.forEach(function(meta){

					if ( meta.name === "document_cts_urn" ){
						$scope.selected_text.passage_urn = meta.value;
						passage_urn = meta.value.split(":");
						passage_urn = passage_urn[3].split(".");
						$scope.selected_text.textgroup_urn = passage_urn[0];
						$scope.selected_text.corpus_urn = passage_urn[1];
					}

				});

			// Toggle the specific classes and visibility on elements
			$target = $(".text-subwork[data-slug='" + $scope.text_query.slug + "']");
			$(".text-subwork").addClass("hidden");
			$(".text-work").addClass("hidden");
			$(".work-title-wrap").addClass("hidden");
			$target.parents(".text-work").removeClass("hidden");
			$target.removeClass("hidden").addClass("single-header");

			// Set the HTML document meta elements
			$("meta[name=corpus_urn]").attr("content", "urn:cts:copticLit:" + $scope.selected_text.corpus_urn );
			$("meta[name=document_urn]").attr("content", $scope.selected_text.passage_urn ); 

			// Scroll back to the top
			$('html,body').scrollTop(0);

		}

	};


	$scope.show_single = function( e ){
	// Show a selected single text
		var $target
		;

		$(".text-format").hide();
		$scope.text_query = {};
		$scope.text_query.model = "texts";
		$scope.text_query.slug = $scope.path[2];
		$scope.get_texts( $scope.text_query );

	};

	$scope.load_single_iframe = function( corpus_annis_name, selected_text_name, visualization_slug ){
	// Load an iframe src elem

		return "https://corpling.uis.georgetown.edu/annis/embeddedvis/htmldoc/" + corpus_annis_name + "/" + selected_text_name + "?config=" + visualization_slug;

	};


	$scope.toggle_tool_panel = function( e ) {
	// Toggle the search tool panels
		var $target = $(e.target)
		,	$panel
		;

		if( !$target.hasClass("tool-head") ){
			$target = $target.parents(".tool-head");
		}

		$panel = $target.parents(".tool-wrap").children(".tool-panel");
		$(".keys-shown").removeClass("keys-shown");

		if ( $panel.hasClass("hidden") ){
			$(".tool-panel").addClass("hidden");
			$(".tool-head-selected").removeClass("tool-head-selected");
			$target.addClass("tool-head-selected");
			$panel.removeClass("hidden");

		}else {
			$target.removeClass("tool-head-selected");
			$panel.addClass("hidden");

		}

	};

	$scope.toggle_advanced_search_tool_panel = function( e ) {
	// Toggle the advanced search tool panels
		var $target = $(e.target)
		,	$panel
		;

		if( !$target.hasClass("advanced-search-tool-head") ){
			$target = $target.parents(".advanced-search-tool-head");
		}

		$panel = $target.parents(".advanced-search-tool-wrap").children(".advanced-search-sub-tool-panel");

		if ( $panel.hasClass("hidden") ){
			$(".advanced-search-sub-tool-panel").addClass("hidden");
			$(".advanced-search-tool-head-selected").removeClass("advanced-search-tool-head-selected");
			$target.addClass("advanced-search-tool-head-selected");
			$panel.removeClass("hidden");

		}else {
			$target.removeClass("advanced-search-tool-head-selected");
			$panel.addClass("hidden");

		}

	};

	$scope.toggle_keyboard = function( e ) {
	// Toggle show/hide the keyboard
		var $keyboard = $(".input-tool-panel") 
		,	$toggle = $(".fa-keyboard-o")
		;
		$(".tool-head-selected").removeClass("tool-head-selected");
		if ( $keyboard.hasClass("hidden") ){
			$(".tool-panel").addClass("hidden");
			$keyboard.removeClass("hidden");
			$toggle.addClass("keys-shown");
		}else {
			$keyboard.addClass("hidden");
			$toggle.removeClass("keys-shown");
		}
	};

	$scope.press_key = function( e ){
	// Press a key on the coptic keyboard
		var $input = $(".input-tool") 
		,	$target = $(e.target)
		,	text = $target.text()
		;

		$input.val( $scope.text_search + text );
		$scope.text_search = $scope.text_search + text;

	};

	$scope.toggle_search_term = function( e ) {
	// Add or remove a search term from the query
		var $target = $(e.target)
		,	search_obj = {}
		,	filters_url = [] 
		,	filter
		,	field
		;

		$scope.show_loading_modal();
		$scope.text_query = {};

		if( !$target.hasClass("tool-search-item") ) {
			$target = $target.parents(".tool-search-item");
		}

		filter = $target.data().filter;
		id = $target.data().searchid;
		field = $target.parents(".tool-wrap").data().field;
		search_obj = {
					id : id,
					filter : filter,
					field : field
				};


		if ( !$target.hasClass("selected") ){
			$target.addClass("selected");
			$scope.filters.push( search_obj );

		}else {
			$target.removeClass("selected");
			$scope.filters = $scope.filters.filter(function(obj){
						return obj.filter !== search_obj.filter;
					});
		}

		// Update filter string
		$scope.filters.forEach(function(f){
			filters_url.push(f.field + "=" + f.id + ":" + f.filter); 
		});
		filters_url = filters_url.join("&");
		$location.path( "/filter/" + filters_url );

		// Update the text_query
		$scope.text_query = {
				model : "corpus",
				filters : $scope.filters
			};	

		$scope.selected_text = null;
		// $scope.get_corpora( $scope.text_query );


	};

	$scope.add_text_search = function(){
	// Add a textsearch to the filters
		var has_text_search = false
		,	filters_url = []
		,	removed_text_search_filter = false
		,	filters_length = $scope.filters.length
		;

		if ( $scope.text_search.length > 0 ){	

			$scope.filters.forEach(function(filter){
					if ( filter.field === "text_search" ){
						has_text_search = true;
						filter.filter = $scope.text_search;
					}
				});

			if ( !has_text_search ){
				$scope.filters.push({
						id : 0,
						field : "text_search",
						filter : $scope.text_search
					});
			}

			// Update filter string
			$scope.filters.forEach(function(f){
				filters_url.push(f.field + "=" + f.id + ":" + f.filter); 
			});
			filters_url = filters_url.join("&");

			if ( $scope.filters.length > 0 ){
				$location.path( "/filter/" + filters_url );
			}

			// Update the text_query
			$scope.text_query = {
					model : "corpus",
					filters : $scope.filters
				};	

			$scope.selected_text = null;
			$scope.get_corpora( $scope.text_query );


		}else {

			$scope.filters = $scope.filters.filter(function(obj){
						return obj.field !== "text_search" 
					});

			if ( $scope.filters.length < filters_length ){
				$location.path( "/" );

				// Update the text_query
				$scope.text_query = {
						model : "corpus",
						filters : $scope.filters
					};	

				$scope.selected_text = null;
				$scope.get_corpora( $scope.text_query );

			}

		}
	}

	$scope.load_filters = function(){
	// load the filters from the URL to the object
		var search_obj = {}
		,	filter_url = $scope.path[2].split("&")
		;

		$scope.filters = [];

		// Process filter URLs
		filter_url.forEach(function(filter){
			var filter_value;
			filter = decodeURI(filter);
			filter = filter.split("=");

			// if filter contains a key val pair demarcated by = 
			if ( filter.length > 1 ) {
				filter_value = filter[1].split(":")

				$scope.filters.push({
							id : filter_value[0],
							filter : filter_value[1],
							field : filter[0]
						});
				$(".tool-search-item[data-searchid='" + filter_value[0] + "']").addClass("selected");

				if ( filter[0] === "text_search" ){
					$(".text-search-input").val( filter_value[1] );
					$scope.text_search = filter_value[1];
				}
			}

		});

		$scope.text_query = {
				model : "corpus",
				filters : $scope.filters
			};	

		$scope.selected_text = null;
		$scope.get_corpora( $scope.text_query );

	};


	$scope.remove_search_term = function( e ){
	// Remove the search term filter 
		var $target = $(e.target)
		,	filter
		,	field
		,	filters_url = []
		;

		$scope.show_loading_modal();
		if ( !$target.hasClass("filter-item") ){
			$target = $target.parents(".filter-item");
		}

		filter = $target.data().filter;
		field = $target.data().field;

		$(".tool-search-item[data-filter='" + filter + "']").removeClass("selected");
		$scope.filters = $scope.filters.filter(function(obj){
					return obj.filter !== filter;
				});

		if ( field === "text_search" ){
			$(".text-search-input").val('');
			$scope.text_search = "";
		}

		$scope.text_query = {
				model : "corpus",
				filters : $scope.filters
			};	

		// Update filter string
		$scope.filters.forEach(function(f){
			filters_url.push(f.field + "=" + f.id + ":" + f.filter); 
		});
		filters_url = filters_url.join("&");

		if ( $scope.filters.length > 0 ){
			$location.path( "/filter/" + filters_url );
			$scope.get_corpora( $scope.text_query );

		}else{
			$location.path( "/" );
			$scope.texts = [];

		}



	};

	$scope.clear_all_search_terms = function(){
	// Clear all the search terms selected
		$location.path("/");
	};


	$scope.toggle_text_format = function ( type ){
	// Show or hide the different text formats;
		var $target
		;

		$scope.selected_text_format = type;

		$target = $(".text-item[data-type=" + type + "]");
		if ( !$target.hasClass("selected-text-type") ){	

			// Update the displayed text format if not currently selected
			$( ".selected-text-type" ).removeClass( "selected-text-type" );
			$target.addClass( "selected-text-type" );

			$( ".selected-text-format" ).fadeOut( ).removeClass("selected-text-format");
			$( "#" + type ).fadeIn(  ).addClass("selected-text-format");
		}

	};

	$scope.raise_dropdowns = function(){
	// Raise all dropdowns
		$(".tool-panel").addClass("hidden");
	};

	$scope.urn_submit = function(){
	// Navigate to entered URN
		document.location.href = "/" + $scope.entered_urn;
	};

	$scope.show_loading_modal = function(){
	// Show the loading modal
		$("#loading_modal").fadeIn(300);
	};

	$scope.hide_loading_modal = function(){
	// Hide the loading modal 
		$("#loading_modal").fadeOut(300);
	};

}]);