from brainsquared.modules.classifiers.ThresholdClassifier import \
  ThresholdClassifier

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _DEVICE_TYPE = "neurosky"

  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"
  
  # Module configuration
  _INPUT_METRICS = {"metric_to_classify": "eeg", "label_metric": "NA"}
  _OUTPUT_METRICS = {"result_metric": "classification"}
  _ATTENTION_THRESHOLD = 40
  _MEDITATION_THRESHOLD = 60
  _THRESHOLDS = {
    "channel_0": _ATTENTION_THRESHOLD,
    "channel_1": _MEDITATION_THRESHOLD
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
