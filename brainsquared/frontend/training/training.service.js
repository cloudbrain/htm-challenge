(function () {
  'use strict';

  angular.module('cloudbrain.training')
    .factory('TrainingService', ['$http', 'TRAINING_URL', 'COUNTER', 'CONFIG',
      function ($http, TRAINING_URL, COUNTER, CONFIG) {

        var TrainingService = function () {};

        TrainingService.prototype.record = function (label) {
          var body = {
            module: "CSVWriterSink",
            user: CONFIG.user,
            device: CONFIG.device,
            inputs: {input: CONFIG.metric},
            outputs: null,
            host: CONFIG.host,
            login: CONFIG.login,
            pwd: CONFIG.pwd,
            offset: 1,
            period: COUNTER,
            label: label
          };
          console.log('TrainingService.record Request:', body);
          return $http.post(TRAINING_URL, body).then(function (response) {
            console.log('TrainingService.record Success', response);
          }, function (err) {
            console.log("TrainingService.record Error", err);
          });
        };

        TrainingService.prototype.classify = function (train) {
          var body = {
            module: "SKLearnClassifier",
            user: CONFIG.user,
            device: CONFIG.device,
            inputs: {input: CONFIG.metric, input_label: null},
            outputs: {classification_result: CONFIG.output},
            host: CONFIG.host,
            login: CONFIG.login,
            pwd: CONFIG.pwd,
            classifier: 'svm',
            num_categories: 2,
            train_classifier: train
          };
          console.log('TrainingService.classify Request:', body);
          return $http.post(TRAINING_URL, body).then(function (response) {
            console.log('TrainingService.classify Success', response);
          }, function (err) {
            console.log("TrainingService.classify Error", err);
          });
        };

        return new TrainingService;
      }]);

})();
