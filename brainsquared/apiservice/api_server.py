import simplejson as json

from flask import Flask, request

from htmresearch.frameworks.classification.utils.network_config import \
  generateNetworkPartitions

from brainsquared.analytics.htm_classifier import HTMClassifier
from brainsquared.apiservice.worker import Worker

_WEBSERVER_PORT = 8080
_API_VERSION = "v0.1"
_TRAIN_SET_SIZE = 2000
_NTWK_CONFIG = "config/network_config.json"
_TRAINING_DATA = "data/training_data.csv"
_TRAINING_SETS = {"left": _TRAINING_DATA, "right": _TRAINING_DATA}

with open(_NTWK_CONFIG, "rb") as jsonFile:
  network_config = json.load(jsonFile)
partitions = generateNetworkPartitions(network_config, _TRAIN_SET_SIZE)
models = {}

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True

worker = Worker()



def _format_user_models(user_id):
  """
  Makes the models of a user JSON serializable.
  @param user_id: (string) id of the user
  @return user_models: (dict) JSON serializable dict of models for this user
    [
      {"model_id": <model_id>, "status": "initialized"},
      ...
      {"model_id": <model_id>, "status": "initialized"},

    ]
  """
  user_models = []
  if user_id in models:
    for model_id in models[user_id]:
      user_models.append({
        "status": models[user_id][model_id]["status"],
        "model_id": model_id,
        "training_accuracy": models[user_id][model_id]["training_accuracy"],
      })
  return user_models



@app.route('/api/%s/users/<string:user_id>/models' % _API_VERSION,
           methods=['POST'])
def create_model(user_id):
  """Create a new model and initialize it."""

  model_id = "model1"  # could generate a UUID if we wanted more than 1 model

  if user_id not in models:
    initialize_model = True
  else:
    if len(models[user_id]) == 0:
      initialize_model = True
    elif len(models[user_id]) == 1:
      initialize_model = False
    else:
      raise ValueError("WARNING: Too many models are running. Number of "
                       "models: %s" % len(models))

  if initialize_model:
    classifier = HTMClassifier(_TRAINING_SETS, network_config,
                               _TRAIN_SET_SIZE, partitions)
    classifier.initialize()
    models[user_id] = {
      model_id: {
        "model": classifier,
        "status": "initialized",
        "training_accuracy": None
      }
    }

  return json.dumps([{
    "model_id": model_id,
    "status": "initialized",
    "training_accuracy": None
  }]), 200



@app.route('/api/%s/users/<string:user_id>/models' % _API_VERSION,
           methods=['GET'])
def get_models(user_id):
  """Return all models for this user"""
  return json.dumps(_format_user_models(user_id)), 200



@app.route('/api/%s/users/<string:user_id>/models/<string:model_id>'
           % _API_VERSION, methods=['GET'])
def get_model(user_id, model_id):
  """Return a model for this user"""
  user_models = _format_user_models(user_id)
  for model in user_models:
    if model["model_id"] == model_id:
      return json.dumps([model]), 200
    else:
      return json.dumps([]), 200



@app.route('/api/%s/users/<string:user_id>/models/<string:model_id>/train'
           % _API_VERSION, methods=['POST'])
def train(user_id, model_id):
  """Train a model"""

  if user_id in models:
    if model_id in models[user_id]:
      classifier = models[user_id][model_id]["model"]
      classification_accuracy = classifier.train()
      models[user_id][model_id]["status"] = "trained"
      models[user_id][model_id]["training_accuracy"] = classification_accuracy
      response = [{
        "model_id": model_id,
        "status": "trained",
        "training_accuracy": classification_accuracy
      }]
      return json.dumps(response), 200

    else:
      response = "No model to train. Create a model first."
      return json.dumps(response), 500
  else:
    response = "No model to train. Create a model first."
    return json.dumps(response), 600



@app.route('/api/%s/users/<string:user_id>/models/<string:model_id>'
           % _API_VERSION, methods=['DELETE'])
def delete_model(user_id, model_id):
  """Delete a model"""

  if user_id in models:
    if model_id in models[user_id]:
      del models[user_id][model_id]
      response = _format_user_models(user_id)
    else:
      response = "no model with ID %s for user %s" % (model_id, user_id)
  else:
    response = "no user with ID %s" % user_id

  return json.dumps(response), 200



@app.route('/api/%s/users/<string:user_id>/tags/<string:tag_id>'
           % _API_VERSION, methods=['POST'])
def create_tag(user_id, tag_id):
  """Create a new tag to label data"""
  metric_name = "tags"
  worker.publish(user_id, metric_name, tag_id)



@app.route('/api/%s/users/<string:user_id>/models/<string:model_id>/classify'
           % _API_VERSION, methods=['POST'])
def start_classification(user_id, model_id):
  """Labels a chunk of data with a set of tags and classifies it."""
  chunk_size = int(request.form['chunkSize'])
  tags = json.loads(request.form['tags'])
  if user_id in models:
    if model_id in models[user_id]:
      model = models[user_id][model_id]["model"]
      result = worker.process_chunk(user_id, model, chunk_size, tags)

      metric_name = "classification"
      # TODO / WIP: should probably be in a thread or something
      worker.publish(user_id, metric_name, result)
      
      message = "Success"
      
    else:
      message = "Model ID %s does not exists" % model_id
  else:
    message = "User ID %s does not exists" % user_id
  return json.dumps(message), 200


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=_WEBSERVER_PORT)
