import json
import threading
from flask import Flask, request
from flask.ext.cors import CORS
from threading import Thread
import os
import imp
import re

_WEBSERVER_PORT = 8080
_API_VERSION = "v0.1"
_MODULES_DIR = os.path.realpath(os.path.join(os.getcwd(),
                                             os.path.pardir, "modules"))

app = Flask(__name__)
CORS(app)
app.config['PROPAGATE_EXCEPTIONS'] = True

# keep track of module threads
modules = {}



class StoppableThread(threading.Thread):
  """Thread class with a stop() method. The thread itself has to check
  regularly for the stopped() condition."""


  def __init__(self):
    super(StoppableThread, self).__init__()
    self._stop = threading.Event()


  def stop(self):
    self._stop.set()


  def stopped(self):
    return self._stop.isSet()



@app.route('/api/%s/modules/start' % _API_VERSION, methods=['POST'])
def start():
  """Start Module"""

  module_name = request.json["module"]
  module_type = "{}s".format(re.findall('[A-Z][^A-Z]*',
                                        module_name)[-1].lower())

  # for call modules
  host = request.json["host"]
  login = request.json["login"]
  pwd = request.json["pwd"]
  user = request.json["user"]
  device = request.json["device"]
  input_metrics = request.json["inputs"]
  output_metrics = request.json["outputs"]

  # dynamically import the module
  module_filepath = os.path.join(_MODULES_DIR, module_type,
                                 '%s.py' % module_name)
  py_mod = imp.load_source(module_name, module_filepath)
  Module = getattr(py_mod, module_name)

  module = Module(user,
                  device,
                  host,
                  login,
                  pwd,
                  input_metrics,
                  output_metrics)

  if module_name == "CSVWriterSink":
    offset = request.json["offset"]
    period = request.json["period"]
    label = request.json["label"]
    module.configure(offset, period, label)
    module_name = "%s (tag: %s)" % (module_name, label)

  elif module_name == "SKLearnClassifier":
    classifier = request.json["classifier"]
    num_categories = request.json["num_categories"]
    train_classifier = request.json["train_classifier"]

    module.configure(classifier, num_categories)
    if train_classifier:
      clf_path, score = module.train()
  else:
    print " => Modules: %s" % modules
    return json.dumps("Invalid module name: %s" % module_name), 400

  module.connect()
  t = Thread(target=module.start)
  t.start()
  if module_name in modules:
    print " => Modules: %s" % modules
    return json.dumps("%s module already running with configuration %s" % (
      module.__class__.__name__, request.json)), 400
  else:
    modules[module_name] = t
    print " => Modules: %s" % modules
    return json.dumps("%s module started with configuration %s" % (
      module.__class__.__name__, request.json)), 200



if __name__ == "__main__":
  print " => Modules: %s" % modules
  app.run(host="0.0.0.0", port=_WEBSERVER_PORT)

