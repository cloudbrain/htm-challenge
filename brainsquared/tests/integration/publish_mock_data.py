#!/usr/bin/env python
from brainsquared.publishers.PikaPublisher import PikaPublisher
import time
import random
import json

USER_ID = "brainsquared"
MODULE_IDS = ["module0", "module1", "module2", "module3"]
DEVICE = "openbci"


pub = PikaPublisher("rabbitmq.cloudbrain.rocks", "cloudbrain", "cloudbrain")
pub.connect()

for module_id in MODULE_IDS:
  TAG_KEY = '%s:%s:tag' % (USER_ID, module_id)
  pub.register(TAG_KEY)
  #pub.publish(TAG_KEY, {"timestamp": 1, "value": "middle"})
  #pub.publish(TAG_KEY, {"timestamp": 1, "value": "left"})
  #pub.publish(TAG_KEY, {"timestamp": 1, "value": "right"})


MU_KEY = '%s:%s:mu' % (USER_ID, DEVICE)
pub.register(MU_KEY)
# pub.publish(MU_KEY, {"timestamp": 1, "value": 1})

CLASSIFICATION_KEY = '%s:%s:classification' % (USER_ID, MODULE_IDS[0])
pub.register(CLASSIFICATION_KEY)

while 1:
    random_class = random.sample([-2,-1,0,1,2], 1)[0]
    pub.publish(CLASSIFICATION_KEY, [{"timestamp": 1, "value": random_class}])
    print '%s - published: %i' % (CLASSIFICATION_KEY, random_class)
    time.sleep(0.1)
