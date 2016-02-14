from brainsquared.modules.classifiers.SKLearnClassifier import SKLearnClassifier

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _DEVICE_TYPE = "neurosky"

  _RMQ_ADDRESS = "127.0.0.1"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"

  # Module configuration
  _INPUT_METRICS = {"input": "attention", "input_label": None}
  _OUTPUT_METRICS = {"classification_result": "classification"}

  _CLASSIFIER_TYPE = "svm"
  module = SKLearnClassifier(_USER_ID,
                            _DEVICE_TYPE,
                            _RMQ_ADDRESS,
                            _RMQ_USER,
                            _RMQ_PWD,
                            _INPUT_METRICS,
                            _OUTPUT_METRICS)
  module.configure(_CLASSIFIER_TYPE)
  module.connect()
  module.start()
