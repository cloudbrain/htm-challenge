## Prerequisites
* Start RabbitMQ
* Publish data to RabbitMQ. For example with `NeuroskySource.py`:
```
 python NeuroskySource.py --server_host=localhost --server_username=guest --server_password=guest --publisher_user=brainsquared --publisher_device=wildcard --publisher_metric=motor_imagery --device=/dev/tty.MindWaveMobile-DevA
```

## Collect and label CSV data

To subscribe to RabbitMQ and collect data, run:

```
python collect_and_tag_csv.py  -c <string> -t <int>
```

Where `c` is a JSON string with the list of the metrics to collect. E.g:
```
'["lowAlpha", "highAlpha", "lowBeta","highBeta"]'
```

And `t` is the tag to label the data. E.g. `10`.

So for example, collect data with the neurosky, run:
```
python collect_and_tag_csv.py  -c '["lowAlpha", "highAlpha", "lowBeta",
"highBeta"]' -t 10
```

## Labeling conventions
Neutral is always equal to the highest value. So with 2 classes 
(left and right) we have:
* Left: 0
* Right: 1 
* Neutral: 2


For meditation / attention detection, we take the following labelling 
conventions:
* Meditation = Left = 0
* Attention = Right = 1 
* Neutral = 2