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
        if(this.sprite.position.x > -4.1 && this.sprite.position.x < 4.1) {
          this.sprite.position.setX(this.sprite.position.x + stepSize);
        }else if(this.sprite.position.x <= -4.1) {
          this.sprite.position.setX(-3.9);
        }else if(this.sprite.position.x >= 4.1) {
          this.sprite.position.setX(3.9);
        }
      };

      Octopicorn.prototype.start = function (callback) {
        var stream = this.stream = new RtDataStream
        ('http://localhost:31415/websocket', 'neurosky', 'brainsquared');
        self = this;
        stream.connect(
          function open(){
            console.log('Realtime Connection Open');
            stream.subscribe('classification', function(msg) {
              if(msg.channel_0 !== 2){
                var direction = msg.channel_0 === 0 ? 'left' : 'right';
                self.step(msg.channel_0/10, direction);
                Accuracy.step(msg.channel_0/10, direction);
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
