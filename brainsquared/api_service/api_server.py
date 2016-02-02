import json

from threading import Thread

from flask import Flask, request

from brainsquared.modules.classifiers.HTMClassifier import HTMClassifier
from brainsquared.modules.filters.EyeBlinksFilter import EyeBlinksFilter

_RMQ_ADDRESS = "rabbitmq.cloudbrain.rocks"
_RMQ_USER = "cloudbrain"
_RMQ_PWD = "cloudbrain"
_WEBSERVER_PORT = 8080
_API_VERSION = "v0.1"

_VALID_MODULES = ["motor_imagery"]
modules = {}

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True



def _num_of_modules():
  num_modules = 0
  for value in modules.values():
    num_modules += len(value)
  return num_modules



@app.route('/api/%s/users/<string:user_id>/modules' %
           _API_VERSION, methods=['POST'])
def create_module(user_id):
  """Create a new Analytics module and initialize it"""

  module_type = request.json["module_type"]
  device_type = request.json["device_type"]

  if len(modules) == 0:
    module_id = "module0"
  else:
    module_id = "module%s" % _num_of_modules()

  if user_id not in modules:
    modules[user_id] = {}

  # if module_type == "filter":
  #   preproc_module = EyeBlinksFilter(user_id,
  #                                    module_id,
  #                                    device_type,
  #                                    _RMQ_ADDRESS,
  #                                    _RMQ_USER,
  #                                    _RMQ_PWD, 
  #                                    module_id)
  #   preproc_module.configure(...)
  #   preproc_module.connect()
  #   thread = Thread(target=preproc_module.start)
  #   thread.start()
  #   modules[user_id][module_id] = preproc_module

  # if module_type == "classifier":
  #   module_id = "module%s" % (len(modules))
  #   htm_mi_module = HTMClassifier(user_id,
  #                                 module_id,
  #                                 device_type,
  #                                 _RMQ_ADDRESS,
  #                                 _RMQ_USER,
  #                                 _RMQ_PWD,
  #                                 module_id)
  #   htm_mi_module.configure(...)
  #   htm_mi_module.connect()
  #   thread = Thread(target=htm_mi_module.start)
  #   thread.start()
  #   modules[user_id][module_id] = htm_mi_module
  # if module_type not in _VALID_MODULES:
  #   return json.dumps("Wrong module type: %s. Valid modules: %s"
  #                     % (module_type, _VALID_MODULES))

  return json.dumps({"id": module_id}), 200



@app.route('/api/%s/users/<string:user_id>/modules' % _API_VERSION,
           methods=['GET'])
def get_modules(user_id):
  """Get the IDs of all running analytics modules"""
  return json.dumps(modules[user_id].keys()), 200



@app.route('/api/%s/users/<string:user_id>/modules/<string:module_id>/tag' %
           _API_VERSION, methods=['POST'])
def create_tag(user_id, module_id):
  """Create new module tag"""
  timestamp = request.json["timestamp"]
  value = request.json['value']
  data = {"timestamp": timestamp, "value": value}

  # routing_key = "%s:%s:%s" % (user_id, module_id, "tag")
  # 
  # tag_publisher = modules[user_id][module_id].tag_publisher
  # tag_publisher.publish(routing_key, data)
  return json.dumps("Tag published: %s" % data), 200



if __name__ == "__main__":
  app.run(host="0.0.0.0", port=_WEBSERVER_PORT)
