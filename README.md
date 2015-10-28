# htm-challenge
HTM Challenge 2015

## Setup
Install `htmresearch`. We need that to be able to use the classification 
network factory.
```
git clone https://github.com/numenta/nupic.research.git
cd nupic.research
python setup.py develop --user
```

Check that it's been installed correctly:
```
$ python
>>> from htmresearch.frameworks.classification.classification_network import createNetwork
... # success!
```

## What it does
Collect EEG data (i.e. brainwaves) and classify your mental states. One common mental state that is often classified is motor imagery, that is to say imagined motor movements (e.g moving your hand left or right). By classifying data from the motor cortex we can extract controls to interact with the physical/digital world.
