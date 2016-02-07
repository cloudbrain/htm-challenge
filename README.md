# htm-challenge
HTM Challenge 2015

## What it does
Collect EEG data (i.e. brainwaves) and classify your mental states. One common mental state that is often classified is motor imagery, that is to say imagined motor movements (e.g moving your hand left or right). By classifying data from the motor cortex we can extract controls to interact with the physical/digital world.

## Setup

### NuPIC Research (OPTIONAL - Only required for the HTM classifier)
Install `htmresearch`. We need that to be able to use the classification 
network factory.
```
git clone https://github.com/marionleborgne/nupic.research.git
cd nupic.research
python setup.py install --user
```

Check that it's been installed correctly:
```
$ python
>>> from htmresearch.frameworks.classification.classification_network import createNetwork
... # success!
```

### RabbitMQ
On OSX, install with `brew`:
```
brew install rabbitmq
```

### BrainSquared
```
git clone https://github.com/cloudbrainlabs/htm-challenge.git
cd htm-challenge
python setup.py install --user  
```

If you want to be able to frequently edit the code and not have to 
re-install the `brainsquared` package after every modification, use `develop` 
instead of `install`.
```
cd htm-challenge
python setup.py develop --user  
```

### Frontend

Make sure you have node, npm, and gulp installed. 
```
cd brainsquared/frontend
npm install  
```


## Run the app


## Frontend
```
cd brainsquared/frontend
gulp
```

### Start RabbitMQ

```
rabbitmq-server start
```

### Start the websocket server
The websocket server subscribes to RabbitMQ and open websocket(s) for the client
 UI.
 
```
cd brainsquared/module_runners
python websocket_sink_runner.py 
```


### Publish data with the Neurosky

```
cd brainsquared/module_runners
python neurosky_source_runner.py  --server_host=localhost --server_username=guest --server_password=guest --publisher_user=brainsquared --publisher_device=neurosky --publisher_metric=mindwave --device=/dev/tty.MindWaveMobile-DevA
```

### Train a model

#### Collect and tag data
```
cd brainsquared/module_runners
python csv_writer_sink_runner.py
```
> NOTE: you might need to update the `_TAG` value in `csv_writer_sink_runner.py`

#### Train a model
```
cd brainsquared/module_runners
python sklearn_trainer_runner.py
```

### Start the classifier
This reads from the serialized model and classify the incoming data stream.
```
cd brainsquared/module_runners
python sklearn_classifier_runner.py
```
