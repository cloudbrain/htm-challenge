# htm-challenge
HTM Challenge 2015

## Setup

### NuPIC Research
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

```
cd brainsquared/frontend
npm install  
gulp
```

### Websocket server
The wesocket server subscribes to RabbitMQ and open websocket(s) for the client
 UI.

```
cd brainsquared/websocket_server
python websocket_server.py
 
```


## Publish data with the Neurosky

```
python neurosky_publisher.py --server_host=localhost --server_username=guest \
--server_password=guest --publisher_user=brainsquared \
publisher_device=neurosky --publisher_metric=mindwave \
--device=/dev/tty.MindWaveMobile-DevA
```


## What it does
Collect EEG data (i.e. brainwaves) and classify your mental states. One common mental state that is often classified is motor imagery, that is to say imagined motor movements (e.g moving your hand left or right). By classifying data from the motor cortex we can extract controls to interact with the physical/digital world.
