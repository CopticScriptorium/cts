/*
 * Gulpfile for concatenating/minifying CSS/JS and running tests
 */

// Include gulp
var 	gulp      = require('gulp') 
 
// Include plug-ins
,	  jshint      = require('gulp-jshint')
,	  changed     = require('gulp-changed')
,	  concat      = require('gulp-concat')
,	  stripDebug  = require('gulp-strip-debug')
,	  compass     = require('gulp-compass')
,	  uglify      = require('gulp-uglify')
,	  autoprefix  = require('gulp-autoprefixer')
,	  minifyCSS   = require('gulp-minify-css')
,   notify      = require('gulp-notify')
,   rename      = require('gulp-rename')
,   plumber     = require('gulp-plumber')
,   livereload  = require('gulp-livereload')
,   karma       = require('karma').server
;
 
// JS hint task
gulp.task('jshint', function() {
	gulp.src(['./client/*.js', './client/**/*.js'])
    .pipe(plumber())
		.pipe(jshint())
		.pipe(jshint.reporter('default'));
});

// JS concat, strip debugging and minify
gulp.task('scripts', function() {
  gulp.src(['./client/**/*.js', './client/*.js'])

    // plumber for errors
    .pipe(plumber())

    // finally, concatenate files
    .pipe(concat('app.js'))
    // .pipe(stripDebug())
    // .pipe(uglify())
    .pipe(gulp.dest('./static/js'));

});

// Process compass scss to css
gulp.task('compass', function() {
  gulp.src('./scss/*.scss')
  .pipe(plumber())
  .pipe(compass({
    config_file: './config.rb',
    css: 'static/css_src',
    sass: 'scss'
  }))
  .pipe(gulp.dest('./static/css_src'));
});

// CSS concat, auto-prefix and minify
gulp.task('styles', function() {
  gulp.src(['./bower_components/html5-boilerplate/css/normalize.css', './bower_components/html5-boilerplate/css/main.css', './static/css_src/base.css'])
    .pipe(plumber())
    .pipe(concat('styles.css'))
    .pipe(autoprefix('last 2 versions'))
    .pipe(minifyCSS())
    .pipe(gulp.dest('./static/css'))
    .pipe(livereload());
});

// Default task
gulp.task('default', ['scripts', 'compass', 'styles'], function() {
  
  // Set livereload to listen
  livereload.listen();

  // Watch for JS changes
  gulp.watch(['./client/*.js', './client/**/*.js'], ['scripts']);
 
  // Watch for CSS changes
  gulp.watch('./scss/*.scss', ['compass']);
  gulp.watch('./static/css_src/base.css', ['styles']);

});

// Run karma tests
gulp.task('test', function (done) {
  karma.start({
    configFile: __dirname + '/karma.conf.js',
    singleRun: true
  }, done);
});

// Watch file changes, re-run tests on change
gulp.task('tdd', function (done) {
  karma.start({
    configFile: __dirname + '/karma.conf.js'
  }, done);
});