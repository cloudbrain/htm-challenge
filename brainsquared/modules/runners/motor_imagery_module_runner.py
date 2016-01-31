from brainsquared.modules.classifiers.HTMMotorImageryModule import (
  HTMClassifierModule)
from brainsquared.modules.classifiers.settings import (TRAINING_FILE,
                                                       NUM_RECORDS,
                                                       NETWORK_CONFIG,
                                                       NETWORK_PATH,
                                                       MINVAL, MAXVAL)

if __name__ == "__main__":

  _USER_ID = "brainsquared"
  _DEVICE_TYPE = "neurosky"
  _RMQ_ADDRESS = "rabbitmq.cloudbrain.rocks"
  _RMQ_USER = "cloudbrain"
  _RMQ_PWD = "cloudbrain"
  _INPUT_METRICS = {"metric_to_classify": "eeg", "label_metric": "tag"}
  _OUTPUT_METRICS = {"result_metric": "classification"}
  _CATEGORIES = [0, 1]

  module = HTMClassifierModule(_USER_ID,
                               _DEVICE_TYPE,
                               _RMQ_ADDRESS,
                               _RMQ_USER,
                               _RMQ_PWD,
                               _INPUT_METRICS,
                               _OUTPUT_METRICS)
  module.configure(_CATEGORIES,
                   NETWORK_CONFIG,
                   NETWORK_PATH,
                   MINVAL,
                   MAXVAL)
  
  module.connect()
  module.train(TRAINING_FILE, NUM_RECORDS)
  module.classify()
