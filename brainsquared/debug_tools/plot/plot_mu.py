import matplotlib.pyplot as plt
import csv

plt.figure()

filePath = "low_beta.csv"

timesteps = []
data = []
labels = []
categoriesLabelled = []
with open(filePath, 'rb') as f:
  reader = csv.reader(f)
  headers = reader.next()
  
  # skip the 2 first rows
  reader.next()
  reader.next()
  
  for i, values in enumerate(reader):
    record = dict(zip(headers, values))
    timesteps.append(i)
    data.append(float(record['y']))
    labels.append(int(record['label']))
  
  plt.plot(timesteps, data, label='signal')
  plt.plot(timesteps, labels, label='labels')

  # title
  title = filePath
  plt.title(title)
  plt.tight_layout()
  
  plt.legend()
  
  plt.show()
