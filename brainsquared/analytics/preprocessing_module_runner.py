from brainsquared.analytics.preprocessing.preprocessing_module import \
  PreprocessingModule

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _MODULE_ID = "module0"
  _DEVICE_TYPE = "openbci"
  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "cloudbrain"
  _RMQ_PWD = "cloudbrain"

  _STEP_SIZE = 32

  module = PreprocessingModule(_USER_ID,
                               _MODULE_ID,
                               _DEVICE_TYPE,
                               _RMQ_ADDRESS,
                               _RMQ_USER,
                               _RMQ_PWD)
  module.configure(_STEP_SIZE)
  module.connect()
  module.start()
