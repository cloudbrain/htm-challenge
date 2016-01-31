# Cloudbrain Analysis Modules

## Think about this whole thing visually
In the long run we want to have a drag-and-drop visual interface for the modules.

## Module Conventions

### Metric names: 
- `{"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>` is the pattern for all data flowing though cloudbrain
- Provide an API endpoint with the mapping of number of channels for all modules. This is heavily linked to the relational database that stores all data (modueles, devices, users, data_sessions, user_groups)
- 

---

ModuleAbstract
=============
Params:
- host
- host_usr
- host_pwd
- device_id
- device_type
- input_metrics
- output_metrics

Internal attributes:
- module_id


Classifiers
===========
List of modules:
- HTMClassifier
- ThresholdClassifier
- RandomForestClassifier

Signature:
- input_metrics = {"metric_to_classify": <string>, "label_metric": <string>}
- output_metrics = {"result_metric": <string>}

Input metrics:
- metric_to_classify: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}
- label_metric: {"timestamp": <int>, "channel_0": <int>}

Outputs metrics:
- result_metric: {"timestamp": <int>, "channel_0": <int>}

Filters
===========
List of modules:
- EyeBlinksFilter
- NotchFilter
- BandPassFilter

Signature:
- input_metrics = {"metric_to_filter": <string>}
- output_metrics = {"filtered_metric": <string>}

Input metrics:
- metric_to_filter: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}

Outputs metrics:
- filtered_metric: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}

Transformers
===========

List of modules:
- SFFT
- SubSampler

Signature:
- input_metrics = {"metric_to_filter": <string>}
- output_metrics = {"filtered_metric": <string>}

Input metrics:
- metric_to_filter: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}

Outputs metrics:
- filtered_metric: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}

Publishers
==========
List of modules:
- MusePublisher
- OpenBCIPublisher
- NeuroskyPublisher

Signature:
- input_metrics = {}
- output_metrics = {"filtered_metric": <string>}

Configuration Parameters:
- mock_enabled

Outputs metrics:
- filtered_metric: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}


Subscribers
===========

List of modules:
- FileWriter
- CassandraWriter
- WebSocketServer


Signature:
- input_metrics = {}
- output_metrics = {"filtered_metric": <string>}

Configuration Parameters:
- mock_enabled

Input metrics:
- metric_to_filter: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}
- 
---------------------------

TODO
====
- neurosky needs to be updated (new thread)
- get rid of `old` folder when HTM maic is a bit more far along
- cleanup `debug_tools`
- make sure everything works with multiple input and output metrics
- All classes in different module types sub-directories (modules.classifiers, modules.filters, ...tranformers) need to end in the same way as the parent folder: modules.classifiers.HTMClassifier, modules.classifiers.ThresholdClassifier, modules.filters.EyeBlinksFitler, etc...
- That way when I instantiate the class (AnalysisService) i can provide the module type. It is usefule to know the module signature:
- Update the ThresholdClassifier a bit. The description is """Classify with a simple threshold.""" but that would be nice to classify with an arbitratry number of thresholds and have a wieghted sum.
- In the YAML file, the conf can say if we are goign through rabbit or not
- The conf should also say where the host lives. that is very useful to outsource the data processing.