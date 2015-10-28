import json

from flask import Flask
from os.path import dirname, join

from brainsquared.classification.htm_classifier import train, test

_API_VERSION = "v1.0"
_TRAINING_DATA = join(dirname(dirname(__file__)), "data", "motor_data.csv") 



app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True



@app.route('/api/%s/train' % _API_VERSION, methods=['POST'])
def train():
  """Train classifier"""
    
  results = train(_TRAINING_DATA)
  return json.dumps({"results": results}), 200

      
@app.route('/api/%s/test' % _API_VERSION, methods=['POST'])
def train():
  """Test classifier"""
    
  results = test()
  return json.dumps({"results": results}), 200    