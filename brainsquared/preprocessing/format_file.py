import pandas as pd
import numpy as np
from os.path import dirname, join

MI_DATA = join(dirname(dirname(__file__)), "data", "motor_data.csv")
FORMATTED_MI_DATA = join(dirname(dirname(__file__)), "data", 
                         "formatted_motor_data.csv")
d = pd.read_csv(MI_DATA)
data = np.array(np.abs(d['channel_0']))  
data = data[np.logical_not(np.isnan(data))]  
df = pd.DataFrame(data)
df.to_csv(FORMATTED_MI_DATA)
  
# TODO: add nupic headers and use pierre's pre-processing script
# timestamp,metric,label
# float,float,int
# ,,C
