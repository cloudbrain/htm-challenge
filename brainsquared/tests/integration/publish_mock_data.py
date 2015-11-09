#!/usr/bin/env python
from brainsquared.publishers.PikaPublisher import PikaPublisher

USER_ID = "brainsquared"
MODULE_IDS = ["module0", "module1", "module2", "module3"]
DEVICE = "openbci"


pub = PikaPublisher("rabbitmq.cloudbrain.rocks", "cloudbrain", "cloudbrain")
pub.connect()

for module_id in MODULE_IDS:
  TAG_KEY = '%s:%s:tag' % (USER_ID, module_id)
  pub.register(TAG_KEY)
  pub.publish(TAG_KEY, {"timestamp": 1, "value": "middle"})
  #pub.publish(TAG_KEY, {"timestamp": 1, "value": "left"})
  #pub.publish(TAG_KEY, {"timestamp": 1, "value": "right"})


MU_KEY = '%s:%s:mu' % (USER_ID, DEVICE)
pub.register(MU_KEY)
pub.publish(MU_KEY, {"timestamp": 1, "left": 1, "right": 3})


