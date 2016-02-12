(function () {
  'use strict';

  angular.module('cloudbrain.training', ['ngMaterial'])
    .constant('MODULE_URL', 'http://brainsquared.apiserver.cloudbrain.rocks/api/v0.1/users/brainsquared/modules')
    .constant('TRAINING_CLASSIFIER_TIMEOUT', 4000)
    .constant('COUNTER', 10)
})();
