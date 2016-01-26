from brainsquared.analytics.motor_imagery.motor_imagery_module import \
  HTMMotorImageryModule

if __name__ == "__main__":
  _USER_ID = "brainsquared"
  _MODULE_ID = "module1"
  _DEVICE_TYPE = "openbci"
  _RMQ_ADDRESS = "localhost"
  _RMQ_USER = "guest"
  _RMQ_PWD = "guest"

  module = HTMMotorImageryModule(_USER_ID,
                                 _MODULE_ID,
                                 _DEVICE_TYPE,
                                 _RMQ_ADDRESS,
                                 _RMQ_USER,
                                 _RMQ_PWD, )
  module.connect()
  module.start()
