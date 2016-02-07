from brainsquared.modules.sinks.CSVWriterSink import CSVWriterSink

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _DEVICE_TYPE = "neurosky"

  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"

  # Module configuration
  _INPUT_METRICS = {"input": "attention"}
  _OUTPUT_METRICS = None  # It's a sink module. So not output metrics allowed.

  _TIME_OFFSET = 2000  # 2s
  _RECORDING_TIME = 10000  # 10s. Set it to None if you want to record forever.
  _TAG = 1  # Set it to None if you don't want to tag the data.

  module = CSVWriterSink(_USER_ID,
                         _DEVICE_TYPE,
                         _RMQ_ADDRESS,
                         _RMQ_USER,
                         _RMQ_PWD,
                         _INPUT_METRICS,
                         _OUTPUT_METRICS)
  module.configure(_TIME_OFFSET, _RECORDING_TIME, _TAG)
  module.connect()
  module.start()
