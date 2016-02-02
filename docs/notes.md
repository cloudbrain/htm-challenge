
_INPUT_METRIC_KEY = "metric_to_classify"
_TAG_METRIC_KEY = "label_metric"
_CLASSIFICATION_METRIC_KEY = "label_metric"

metric1 = Metric(_INPUT_METRIC_KEY, "eeg", 8, device_type)
metric2 = Metric(_TAG_METRIC_KEY, "tag", 1, device_type)
metric3 = Metric(_CLASSIFICATION_METRIC_KEY, "classification", 1)
input_metrics = [metric1, metric2]
output_metrics = [metric3] 

class Metric:
    def __init__(self, name, rmq_name, num_channels):
       self.name = name
       self.rmq_name = rmq_name
       self.num_channels = num_channels


classifier_module = ClassifierModule(user_id,
                                       rmq_address,
                                       rmq_user,
                                       rmq_pwd,
                                       input_metrics,
                                       output_metrics)


Metric(1, "eeg", 8, )
Metric(2, "eeg2", 8)

##TODO: we want to be able to merge data from multiple device types
we want to merge multiple metrics (ee1,ee2)

# Cloudbrain Analysis Modules

## Think about this whole thing visually
In the long run we want to have a drag-and-drop visual interface for the modules.

## Module Conventions

### Metric names: 
- `{"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>` is the pattern for all data flowing though cloudbrain
- Provide an API endpoint with the mapping of number of channels for all modules. This is heavily linked to the relational database that stores all data (modueles, devices, users, data_sessions, user_groups)

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

Signature: 2 inputs metrics & 1 output metric
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

Signature: 1 input metric & output metric
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
- MetricMerger (combine 2 metrics channels together)
- MetricSplitter ()

Signature: N input metrics & output metric
- metrics = {"input_metrics": [Metric, ..., <Metric>], 
             "output_metrics": [<string>, ..., <Metric>]}

Input metrics:
- metric_to_filter: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}

Outputs metrics: (M channels)
- filtered_metric: {"timestamp": <int>, "channel_0": <float>, ..., "channel_M": <float>"}

Sources
==========
List of modules:
- MusePublisher
- OpenBCIPublisher
- NeuroskySource (NeuroskyPublisher)
- MockSource(MockPublisher)

Signature: 0 input metrics & 1 output metric
- input_metrics = {}
- output_metrics = {"filtered_metric": <string>}

Configuration Parameters:
- mock_enabled

Outputs metrics:
- filtered_metric: {"timestamp": <int>, "channel_0": <float>, ..., "channel_N": <float>"}


Sinks
===========

List of modules:
- FileWriter
- CassandraWriter
- WebSocketServer (RTServer)


Signature: N inputs & 0 output
- input_metrics = {"input_metric_0": <string>, ..., "input_metric_N": <string>}}
- output_metrics = {}

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
- fix Threshold Classifier. We have "meditation" and 

- module_id = str(uuid.uuidv4())
