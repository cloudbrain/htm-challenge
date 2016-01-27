from brainsquared.modules.preprocessing.preprocessing_module import \
  PreprocessingModule

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _MODULE_ID = "eye_blink_remover"
  _DEVICE_TYPE = "neurosky"
  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"

  # Module configuration
  _STEP_SIZE = 32
  _ELECTRODES_PLACEMENT = {"channel_0": {"main": "channel_0", "artifact": []}}
  _INPUT_METRIC = "eeg"
  _OUTPUT_METRIC = "mu"

  module = PreprocessingModule(_USER_ID,
                               _MODULE_ID,
                               _DEVICE_TYPE,
                               _RMQ_ADDRESS,
                               _RMQ_USER,
                               _RMQ_PWD)
  module.configure(_STEP_SIZE, 
                   _ELECTRODES_PLACEMENT, 
                   _INPUT_METRIC,
                   _OUTPUT_METRIC, )
  module.connect()
  module.start()
