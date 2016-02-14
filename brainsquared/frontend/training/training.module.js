(function () {
  'use strict';

  angular.module('cloudbrain.training', ['ngMaterial'])
    .constant('TRAINING_URL', 'http://localhost:8080/api/v0.1/modules/start')
    .constant('TRAINING_CLASSIFIER_TIMEOUT', 10000)
    .constant('COUNTER', 10)
    .constant('CONFIG', {
      host: 'localhost',
      login: 'guest',
      pwd: 'guest',
      user: 'brainsquared',
      device: 'neurosky',
      metric: 'attention',
      output: 'classification'
    })
})();