(function() {
  'use strict';

  angular.module('cloudbrain.brainsquared')
    .factory('Octopicorn', ['$timeout', 'RtDataStream', 'Accuracy', function($timeout, RtDataStream, Accuracy){

      var Octopicorn = function () {
        this.map = THREE.ImageUtils.loadTexture( "../images/octopicorn.png" );
        this.material = new THREE.SpriteMaterial( { map: this.map, color: 0xffffff, fog: true } );
        this.sprite = new THREE.Sprite( this.material );
        this.bound = { x: 0.57, y: 0.4 };
        this.offset = { x: 0.2, y: 0.01 };
        this.stream = {};
        this.reset();
      };

      Octopicorn.prototype.reset = function () {
        this.sprite.position.set(0, -1.5, 0);
      };

      Octopicorn.prototype.step = function (magnitude, direction) {
        magnitude = magnitude || 1;
        direction = direction || 'right';
        var stepSize = direction == 'right' ? magnitude : magnitude * -1;

        if(this.sprite.position.x + stepSize < -3.8) {
          this.sprite.position.setX(-3.8);
        }else if(this.sprite.position.x + stepSize > 3.8){
          this.sprite.position.setX(3.8);
        }else{
          this.sprite.position.setX(this.sprite.position.x + stepSize);
        }
     };

      Octopicorn.prototype.start = function (callback) {
        var stream = this.stream = new RtDataStream('http://localhost:31415/rt-stream', 'module1', 'brainsquared');
        self = this;
        stream.connect(
          function open(){
            console.log('Realtime Connection Open');
            stream.subscribe('classification', function(msg) {
              if(msg.value !== 0){
                self.step(msg.value/10);
                Accuracy.step(msg.value/10);
              }
            });
          },
          function close(){
            console.log('Realtime Connection Closed');
          });
      };

      Octopicorn.prototype.stop = function () {
        this.stream.disconnect();
      };

      Octopicorn.prototype.jump = function () {
        var self = this.sprite.position;
        self.setY(-1);
        $timeout(function () {
          self.setY(-1.5);
        }, 80);
      };

      return Octopicorn;
  }]);

})();
