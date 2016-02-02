(function () {
  'use strict';

  angular.module('cloudbrain.brainsquared')
    .directive('brainsquared', ['$document', '$rootScope', '$interval', 'Octopicorn', 'Rainbow', 'CollisionDetector', 'Accuracy', 'AnalysisModule',
      function($document, $rootScope, $interval, Octopicorn, Rainbow, CollisionDetector, Accuracy, AnalysisModule){

      var link = function(scope, element){
        $document.on('keypress', function(e) {
          switch(e.which) {
            case 97:
              scope.octopicorn.step(-0.3);
              Accuracy.step(-0.3);
              break;
            case 108:
              scope.octopicorn.step(0.3);
              Accuracy.step(0.3);
              break;
          }
        });

        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera( 100, window.innerWidth/window.innerHeight, 0.1, 1000 );
        var renderer = new THREE.WebGLRenderer({ alpha: true });
        renderer.setSize( window.innerWidth, window.innerHeight );
        renderer.setClearColor( 0x000000, 0);
        renderer.autoClear = false;
        element[0].appendChild( renderer.domElement );

        var generateNewRainbow = function () {
          scene.remove( scope.rainbow.sprite );
          scope.rainbow = new Rainbow(scope.rainbowPosition);
          scope.rainbow.sprite.scale.set( 2, 2, 1 );
          scene.add( scope.rainbow.sprite );
          scope.octopicornRainbowCollision = new CollisionDetector(scope.octopicorn, scope.rainbow);
        };

        scope.octopicorn = {};
        scope.rainbow = {};
        scope.rainbowPosition = 'left';
        scope.score = 0;
        scope.missed = 0;
        scope.target = '';
        scope.accuracy = {};

        scope.octopicorn = new Octopicorn();
        scene.add( scope.octopicorn.sprite );

        scope.$watch('octopicornRainbowCollision.hasCollided()', function (newValue, oldValue) {
          if(newValue) {
            console.log('Collision detected!');
            scope.rainbowPosition = scope.rainbowPosition == 'left' ? 'right' : 'left';
            generateNewRainbow();
            scope.score += 1;
            scope.octopicorn.jump();
          }
        }, true);

        scope.$watch('rainbow.sprite.position.y', function (newValue, oldValue) {
          if(newValue <= -2) {
            scope.missed += 1;
            generateNewRainbow();
          }
        });

        scope.$on('accuracyUpdated', function (event, data) {
          scope.accuracy = data;
        });

        camera.position.z = 3;

        var render = function () {
          requestAnimationFrame(render);
          renderer.clear();
          renderer.render(scene, camera);
          renderer.clearDepth();
        };

        render();

        scope.startAll = function () {
          scope.octopicorn.start();
          generateNewRainbow();
          scope.movement = $interval(function(){
            if(scope.rainbow) { scope.rainbow.drop(); }
            var target = scope.octopicornRainbowCollision.target();
            scope.accuracy = Accuracy.get();
            Accuracy.setTarget(target);
          }, 50);
        };

        scope.resetAll = function () {
          scope.octopicorn.stop();
          scope.octopicorn.reset();
          scope.rainbow.reset();
          Accuracy.reset();
          scope.score = 0;
          scope.missing = 0;
          $interval.cancel(scope.movement);
        };

        scope.togglePlay = function () {
          scope.connected === true ? scope.resetAll() : scope.startAll();
          scope.connected = !scope.connected;
        };

      };

      return {
        replace: true,
        restrict: 'E',
        scope: {},
        link: link,
        templateUrl: 'brainsquared/brainsquared-index.html'
      };

    }]);

})();
