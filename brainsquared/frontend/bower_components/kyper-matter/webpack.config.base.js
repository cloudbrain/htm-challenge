'use strict'
var fs = require('fs');
var path = require('path');
var webpack = require('webpack');

module.exports = {
  module: {
    loaders: [
      { test: /\.js$/, loaders: ['babel-loader'], exclude: /node_modules/ }
    ]
  },
  output: {
    library: 'Matter',
    libraryTarget: 'umd'
  },
  resolve: {
    extensions: ['', '.js']
  }
}
