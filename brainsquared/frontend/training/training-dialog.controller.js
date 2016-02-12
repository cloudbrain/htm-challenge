function TrainingDialogCtrl($scope, $mdDialog, COUNTER, TRAINING_CLASSIFIER_TIMEOUT) {
  $scope.hide = function () {
    $mdDialog.hide();
  };

  $scope.cancel = function () {
    $mdDialog.cancel();
  };

  resetAll();

  $scope.startTraining = function () {
    callApi();
    $scope.isTraining = true;
    resetCounter();
    $scope.counterInterval = setInterval(countDown, 1000);
  };

  function resetAll() {
    $scope.isTraining = false;
    $scope.trainingFinished = false;
    $scope.direction = 'left';
    resetCounter();
  }

  function countDown() {
    $scope.counter = $scope.counter - 1;
    if ($scope.counter === 0) {
      clearInterval($scope.counterInterval);
      $scope.isTraining = false;
      resetCounter();
      nextScreen();
    }
    $scope.$apply();
  }

  function resetCounter() {
    $scope.counter = COUNTER;
  }

  function nextScreen() {
    if ($scope.direction === 'left') {
      $scope.direction = 'right';
    } else {
      $scope.trainingFinished = true;
      setTimeout(function () {
        $mdDialog.hide();
      }, TRAINING_CLASSIFIER_TIMEOUT)
    }
  }

  function callApi() {

  }
}
