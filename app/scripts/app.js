'use strict';

/**
 * @ngdoc overview
 * @name ballAnalysisApp
 * @description
 * # ballAnalysisApp
 *
 * Main module of the application.
 */
var app = angular.module('ballAnalysisApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngTouch'
  ]);

app.config(function ($routeProvider) {
  $routeProvider
    .when('/', {
      templateUrl: 'views/main.html',
      controller: 'MainCtrl',
      controllerAs: 'main'
    })
    .when('/fantasy', {
      templateUrl: 'views/fantasy.html',
      controller: 'FantasyCtrl',
      controllerAs: 'fantasy'
    })
    .otherwise({
      redirectTo: '/'
    });
});
