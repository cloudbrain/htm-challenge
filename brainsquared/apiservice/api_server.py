import json
import logging

from threading import Thread

from flask import Flask, request

from brainsquared.apiservice.motor_imagery import HTMMotorImageryModule


_RMQ_ADDRESS = "rabbitmq.cloudbrain.rocks"
_RMQ_USER = "cloudbrain"
_RMQ_PWD = "cloudbrain"
_WEBSERVER_PORT = 8080
_API_VERSION = "v0.1"

_LOGGER = logging.getLogger(__name__)
modules = {}

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True


def _num_of_modules():
  num_modules = 0
  for value in modules.values():
    num_modules +=len(value)
  return num_modules

@app.route('/api/%s/users/<string:user_id>/modules' %
           _API_VERSION, methods=['POST'])
def create_module(user_id):
  module_type = request.json["module_type"]
  device_type = request.json["device_type"]

  if len(modules) == 0:
    module_id = "module0"
  else:
    module_id = "module%s" % _num_of_modules()
  
  print "NUM OF MODULES: %s" % _num_of_modules()

  if user_id not in modules:
    modules[user_id] = {}
  if module_type == "motor_imagery":
    # Here you could imagine having multiple motor imagery modules in 
    # addition to the HTM motor imagery module. Like a SVM classifier 
    # for example.
    htm_mi_module = HTMMotorImageryModule(user_id, 
                                   module_id, 
                                   device_type,
                                   _RMQ_ADDRESS,
                                   _RMQ_USER,
                                   _RMQ_PWD)
    htm_mi_module.initialize()
    thread = Thread(target=htm_mi_module.start , args = (_LOGGER,))
    thread.start()
    modules[user_id][module_id] = htm_mi_module

  return json.dumps(module_id), 200



@app.route('/api/%s/users/<string:user_id>/modules' % _API_VERSION,
           methods=['GET'])
def get_modules(user_id):
  return json.dumps(modules[user_id].keys()), 200



@app.route('/api/%s/users/<string:user_id>/modules/<string:module_id>/tag' %
           _API_VERSION, methods=['POST'])
def create_tag(user_id, module_id):
  """Create new module and register it."""
  timestamp = request.json["timestamp"]
  value = request.json['value']
  data = {"timestamp": timestamp, "value": value}
  
  routing_key = "%s:%s:%s" % (user_id, module_id, "tag")
  
  tag_publisher = modules[user_id][module_id].tag_publisher
  tag_publisher.publish(routing_key, data)
  return json.dumps("Tag published: %s" % data), 200
  


# 
# @app.route('/api/%s/users/<string:user_id>/models' % _API_VERSION,
#            methods=['GET'])
# def get_models(user_id):
#   """Return all models for this user"""
#   return json.dumps(_format_user_models(user_id)), 200
# 

# 
# @app.route('/api/%s/users/<string:user_id>/models/<string:model_id>'
#            % _API_VERSION, methods=['GET'])
# def get_model(user_id, model_id):
#   """Return a model for this user"""
#   user_models = _format_user_models(user_id)
#   for model in user_models:
#     if model["model_id"] == model_id:
#       return json.dumps([model]), 200
#     else:
#       return json.dumps([]), 200
# 
# 

# 
# 
# @app.route('/api/%s/users/<string:user_id>/models/<string:model_id>/train'
#            % _API_VERSION, methods=['POST'])
# def train(user_id, model_id):
#   """Pre-train a model"""
# 
#   if user_id in models:
#     if model_id in models[user_id]:
#       classifier = models[user_id][model_id]["model"]
#       classification_accuracy = classifier.train()
#       models[user_id][model_id]["status"] = "trained"
#       models[user_id][model_id]["training_accuracy"] = classification_accuracy
#       response = [{
#         "model_id": model_id,
#         "status": "trained",
#         "training_accuracy": classification_accuracy
#       }]
#       return json.dumps(response), 200
# 
#     else:
#       response = "No model to train. Create a model first."
#       return json.dumps(response), 500
#   else:
#     response = "No model to train. Create a model first."
#     return json.dumps(response), 600
# 
# 
# 
# @app.route('/api/%s/users/<string:user_id>/models/<string:model_id>'
#            % _API_VERSION, methods=['DELETE'])
# def delete_model(user_id, model_id):
#   """Delete a model"""
# 
#   if user_id in models:
#     if model_id in models[user_id]:
#       del models[user_id][model_id]
#       response = _format_user_models(user_id)
#     else:
#       response = "no model with ID %s for user %s" % (model_id, user_id)
#   else:
#     response = "no user with ID %s" % user_id
# 
#   return json.dumps(response), 200
# 
# 
# @app.route('/api/%s/users/<string:user_id>/models/<string:model_id>/classify'
#            % _API_VERSION, methods=['POST'])
# def start_classification(user_id, model_id):
#   """Labels a chunk of data with tag and classifies it."""
#   tag = request.form['tag']
#   if user_id in models:
#     if model_id in models[user_id]:
#       model = models[user_id][model_id]["model"]
#       worker = models[user_id][model_id]["worker"]
#       worker.do_job(model, tag)
#       message = "Success"
#     else:
#       message = "Model ID %s does not exists" % model_id
#   else:
#     message = "User ID %s does not exists" % user_id
#   return json.dumps(message), 200
# 
# 
# 
# def _format_user_models(user_id):
#   """
#   Makes the models of a user JSON serializable.
#   @param user_id: (string) id of the user
#   @return user_models: (dict) JSON serializable dict of models for this user
#     [
#       {"model_id": <model_id>, "status": "initialized"},
#       ...
#       {"model_id": <model_id>, "status": "initialized"},
# 
#     ]
#   """
#   user_models = []
#   if user_id in models:
#     for model_id in models[user_id]:
#       user_models.append({
#         "status": models[user_id][model_id]["status"],
#         "model_id": model_id,
#         "training_accuracy": models[user_id][model_id]["training_accuracy"],
#       })
#   return user_models



if __name__ == "__main__":
  app.run(host="0.0.0.0", port=_WEBSERVER_PORT)
