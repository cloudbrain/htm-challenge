(function() {
  'use strict';

  angular.module('cloudbrain.brainsquared')
    .factory('Rainbow', [function(){

      var Rainbow = function (position) {
        this.position = position;
        this.map = THREE.ImageUtils.loadTexture( "../images/rainbow.png" );
        this.material = new THREE.SpriteMaterial( { map: this.map, color: 0xffffff, fog: true } );
        this.sprite = new THREE.Sprite( this.material );
        this.bound = { x: 0.85, y: 0.5 }; //Scale 2
        this.offset = { x: 0.07, y: 0.01 }; //Scale 2
        this.reset();
      };

      Rainbow.prototype.reset = function () {
        var x = this.position == 'left' ? -3.5 : 3.5;
        this.sprite.position.set(x, 4.2, 0.1);
      };

      Rainbow.prototype.drop = function (rate) {
        rate = rate || 0.045;
        this.sprite.position.setY(this.sprite.position.y - rate);
      };

      return Rainbow;
  }]);

})();
