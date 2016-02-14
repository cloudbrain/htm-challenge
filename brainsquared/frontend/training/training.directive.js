(function () {
  'use strict';

  angular.module('cloudbrain.training')
    .directive('training', ['$mdDialog', '$mdMedia',
      function ($mdDialog, $mdMedia) {

        var link = function (scope, element) {

          scope.toggleTraining = function(ev) {
            var useFullScreen = ($mdMedia('sm') || $mdMedia('xs'))  && scope.customFullscreen;
            $mdDialog.show({
                controller: TrainingDialogCtrl,
                templateUrl: 'training/training-dialog.html',
                parent: angular.element(document.body),
                targetEvent: ev,
                clickOutsideToClose:false,
                fullscreen: useFullScreen
              })
              .then(function(answer) {
                scope.status = 'You said the information was "' + answer + '".';
              }, function() {
                scope.status = 'You cancelled the dialog.';
              });
            scope.$watch(function() {
              return $mdMedia('xs') || $mdMedia('sm');
            }, function(wantsFullScreen) {
              scope.customFullscreen = (wantsFullScreen === true);
            });
          };

        };

        return {
          replace: true,
          restrict: 'E',
          scope: {},
          link: link,
          templateUrl: 'training/training.html'
        };

      }]);

})();