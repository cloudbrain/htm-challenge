from brainsquared.modules.classifiers.HTMClassifier import (
  HTMClassifier)
from brainsquared.modules.runners.conf.htm_conf import (TRAINING_FILE,
                                                         NUM_RECORDS,
                                                         NETWORK_CONFIG,
                                                         NETWORK_PATH,
                                                         MINVAL, MAXVAL)

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _DEVICE_TYPE = "neurosky"
  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"
  _INPUT_METRICS = {"metric_to_classify": "eeg", "label_metric": "tag"}
  _OUTPUT_METRICS = {"result_metric": "classification"}
  CATEGORIES = [0, 1]

  module = HTMClassifier(_USER_ID,
                         _DEVICE_TYPE,
                         _RMQ_ADDRESS,
                         _RMQ_USER,
                         _RMQ_PWD,
                         _INPUT_METRICS,
                         _OUTPUT_METRICS)
  module.configure(CATEGORIES,
                   NETWORK_CONFIG,
                   NETWORK_PATH,
                   MINVAL,
                   MAXVAL)

  module.connect()
  module.train(TRAINING_FILE, NUM_RECORDS)
  module.classify()
