import csv
import numpy as np
from sklearn import svm
from sklearn.externals import joblib


_NUM_CATEGORIES = 2
_DATA_DIR = "backup"
_CHANNEL = "attention"
_NUM_TRAIN = 3000


def train_classifier(data_dir, channel, num_categories):
  categories = range(num_categories)
  input_files = {category: "%s/training-data-%s-%s.csv"
                           % (data_dir, category, channel)
                 for category in categories}
  labels = []
  input_values = []
  test_labels = []
  test_input_values = []
  for category in range(num_categories):
    count = 0
    csvFile = open(input_files[category], "rb")
    reader = csv.reader(csvFile)
    # skip 3 header rows
    headers = reader.next()
    reader.next()
    reader.next()

    for row in reader:
      data = dict(zip(headers, row))
      if count < _NUM_TRAIN:
        input_values.append([float(data["y"])])
        labels.append(int(category))
      else: 
        test_input_values.append([float(data["y"])])
        test_labels.append(int(category))
      
      count += 1

  X = np.array(input_values)
  y = np.array(labels)
  
  clf = svm.LinearSVC()
  clf.fit(X, y)

  X_test = np.array(test_input_values)
  y_test = np.array(test_labels)  

  score = clf.score(X_test, y_test) 
  
  return clf, score

if __name__ == "__main__":
  
  
  clf, score = train_classifier(_DATA_DIR, _CHANNEL, _NUM_CATEGORIES)
  joblib.dump(clf, "models/svm-%s.pkl" % _CHANNEL)
  print "Score: %s" % score
  
  clf2 = joblib.load("models/svm-%s.pkl" % _CHANNEL)
  print clf2.predict([70])