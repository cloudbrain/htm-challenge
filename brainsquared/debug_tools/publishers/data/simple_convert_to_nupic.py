import csv
csvFile = "training-sc-2016-01-27.csv"
rowLimit = 3000
rowMin = 4000
rowMax = rowMin + rowLimit
rowCount = 0
with open(csvFile, "rb") as inputFile:
  with open("out_%s" % csvFile, "wb") as outputFile:
    
    writer = csv.writer(outputFile)
    writer.writerow(["x", "y", "label"])
    writer.writerow(["float", "float", "int"])
    writer.writerow(["","","C"])

    reader = csv.reader(inputFile)
    
    headers = reader.next()
    eeg_buffer = []
    for row in reader:
      data = dict(zip(headers, row))
      x = float(data["timestamp"])
      y = float(data["lowBeta"])
      label = data["label"]
      if rowMin < rowCount < rowMax:
        writer.writerow([x,y,label])
      rowCount += 1
