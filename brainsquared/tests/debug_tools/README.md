# How to run debug tools

## Start local RabbitMQ


## Tag EEG data
* You can use *single character* keyboard input to tag EEG data. 
``` 
python brainsquared/analytics/debug/publishers/tag_publisher.py
```
* For example, type `1` to tag `left hand` and `2` to tag `right hand` 
movements.

## Publish mock data from a CSV file
* Publish mock EEG data with `python 
brainsquared/analytics/debug/publishers/csv_file_publisher.py` 
* The data comes from a CSV file with EEG readings from an 8-channel OpenBCI. 

## Write data to a file
* Write EEG data and tags to a file with `python 
brainsquared/analytics/debug/subscribers/file_writer_subscriber.py` `