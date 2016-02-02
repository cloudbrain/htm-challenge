from brainsquared.modules.classifiers.ThresholdClassifier import \
  ThresholdClassifier

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _DEVICE_TYPE = "neurosky"

  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"

  # Module configuration
  _INPUT_METRICS = {"input": "mindwave", "input_label": "NA"}
  _OUTPUT_METRICS = {"classification_result": "classification"}
  _ATTENTION_THRESHOLD = 70
  _MEDITATION_THRESHOLD = 30
  _THRESHOLDS = {
    "channel_0": _MEDITATION_THRESHOLD,
    "channel_1": _ATTENTION_THRESHOLD
  }

  module = ThresholdClassifier(_USER_ID,
                               _DEVICE_TYPE,
                               _RMQ_ADDRESS,
                               _RMQ_USER,
                               _RMQ_PWD,
                               _INPUT_METRICS,
                               _OUTPUT_METRICS)
  module.configure(_THRESHOLDS)
  module.connect()
  module.start()
