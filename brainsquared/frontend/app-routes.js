/* global angular */
(function () { 'use strict';

  var app = angular.module('cloudbrain')
  app.config(function($stateProvider, $urlRouterProvider) {
  $stateProvider
    .state('brainsquared', {
      url:'/',
      template:'<brainsquared></brainsquared>'
    })
  $urlRouterProvider.otherwise('/');
});

})();
