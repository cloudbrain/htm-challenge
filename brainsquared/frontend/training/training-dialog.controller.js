function TrainingDialogCtrl($scope, $mdDialog, COUNTER, TRAINING_CLASSIFIER_TIMEOUT, TrainingService) {
  $scope.hide = function () {
    $mdDialog.hide();
  };

  $scope.cancel = function () {
    $mdDialog.cancel();
  };

  resetAll();

  $scope.startTraining = function () {
    startRecording();
    resetCounter();
    $scope.counterInterval = setInterval(countDown, 1000);
  };

  function resetAll() {
    $scope.isRecording = false;
    $scope.trainingStarted = false;
    $scope.direction = 'left';
    resetCounter();
  }

  function countDown() {
    $scope.counter = $scope.counter - 1;
    if ($scope.counter === 0) {
      clearInterval($scope.counterInterval);
      $scope.isRecording = false;
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
      $scope.trainingStarted = true;
      setTimeout(function () { // Delay hack to make sure it's finished recording
        startTraining();
      }, TRAINING_CLASSIFIER_TIMEOUT)
    }
  }

  function startRecording() {
    console.log('Stating to record for: ' + $scope.direction);
    var label = $scope.direction == 'left' ? 0 : 1;
    TrainingService.record(label).then(function () {
      $scope.isRecording = true;
    });
  }

  function startTraining() {
    console.log('Stating to train the classifier');
    TrainingService.classify(true).then(function () {
      setTimeout(function () { // Delay hack to make sure it's finished training
        endTraining();
      }, TRAINING_CLASSIFIER_TIMEOUT);
    });
  }

  function endTraining() {
    console.log('Finished training the classifier');
    TrainingService.classify(false).then(function () {
      $mdDialog.hide();
    });
  }

}
