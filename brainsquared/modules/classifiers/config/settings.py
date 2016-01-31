NETWORK_PATH = "motor_imagery/models/motor_imagery"
NUM_RECORDS = 58829
TRAINING_FILE = "motor_imagery/data/raw_neurosky_converted.csv"
MINVAL = -3000
MAXVAL = 3000
NETWORK_CONFIG = {
  "sensorRegionConfig": {
    "regionEnabled": True,
    "regionName": "sensor",
    "regionType": "py.CustomRecordSensor",
    "regionParams": {
      "verbosity": 0,
      "numCategories": 3
    },
    "encoders": {
      "scalarEncoder": {
        "name": "scalarEncoder",
        "fieldname": "y",
        "type": "ScalarEncoder",
        "n": 256,
        "w": 21,
        "minval": MINVAL,
        "maxval": MAXVAL
      }
    }
  },
  "spRegionConfig": {
    "regionEnabled": True,
    "regionName": "SP",
    "regionType": "py.SPRegion",
    "regionParams": {
      "spVerbosity": 0,
      "spatialImp": "cpp",
      "globalInhibition": 1,
      "columnCount": 2048,
      "numActiveColumnsPerInhArea": 40,
      "seed": 1956,
      "potentialPct": 0.8,
      "synPermConnected": 0.1,
      "synPermActiveInc": 0.0001,
      "synPermInactiveDec": 0.0005,
      "maxBoost": 1.0
    }
  },
  "tmRegionConfig": {
    "regionEnabled": True,
    "regionName": "TM",
    "regionType": "py.TPRegion",
    "regionParams": {
      "verbosity": 0,
      "columnCount": 2048,
      "cellsPerColumn": 32,
      "seed": 1960,
      "temporalImp": "tm_py",
      "newSynapseCount": 20,
      "maxSynapsesPerSegment": 32,
      "maxSegmentsPerCell": 128,
      "initialPerm": 0.21,
      "permanenceInc": 0.1,
      "permanenceDec": 0.1,
      "globalDecay": 0.0,
      "maxAge": 0,
      "minThreshold": 9,
      "activationThreshold": 12,
      "outputType": "normal",
      "pamLength": 3
    }
  },
  "tpRegionConfig": {
    "regionEnabled": False,
    "regionName": "TP",
    "regionType": "py.TemporalPoolerRegion",
    "regionParams": {
      "poolerType": "union",
      "columnCount": 512,
      "activeOverlapWeight": 1.0,
      "predictedActiveOverlapWeight": 10.0,
      "maxUnionActivity": 0.20,
      "synPermPredActiveInc": 0.1,
      "synPermPreviousPredActiveInc": 0.1,
      "decayFunctionType": "NoDecay"
    }
  },
  "classifierRegionConfig": {
    "regionEnabled": True,
    "regionName": "classifier",
    "regionType": "py.CLAClassifierRegion",
    "regionParams": {
      "steps": "0",
      "implementation": "cpp",
      "maxCategoryCount": 3,
      "clVerbosity": 0
    }
  }
}

