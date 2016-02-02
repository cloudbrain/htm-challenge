import csv

from brainsquared.modules.filters.eeg_preprocessing import \
  preprocess_stft

_ELECTRODES_PLACEMENT = {"channel_0": {"main": "channel_0", "artifact": []}}
_BUFFER_SIZE = 128

with open("neurosky.csv", "rb") as inputFile:
  with open("mu_neurosky_converted.csv", "wb") as outputFile:
    
    writer = csv.writer(outputFile)
    writer.writerow(["x", "y", "label"])
    writer.writerow(["float", "float", "int"])
    writer.writerow(["","","C"])

    reader = csv.reader(inputFile)
    
    headers = reader.next()
    eeg_buffer = []
    for row in reader:
      x = row[0]
      raw_eeg = row[4]
      label = row[5]
      eeg = {"timestamp": x, "channel_0": raw_eeg}
        
      if len(eeg_buffer) > _BUFFER_SIZE:
        processed_data = preprocess_stft(eeg_buffer, _ELECTRODES_PLACEMENT)
        eeg_buffer = []
        y = processed_data["channel_0"][-1]
        writer.writerow([x,y,label])
      else:
        eeg_buffer.append(eeg)
      

    