import sys
sys.path.insert(0, "./lib")
import yamlUtils
import ruamel.yaml

# NOTE: This is NOT how you do tests.

def testHelper(yamlMap):
    with open("./example/sample-mkdocs.yml", 'r') as stream:
        yamlData = ruamel.yaml.load(stream, Loader=ruamel.yaml.RoundTripLoader)
    newYaml = yamlUtils.modifyYaml(yamlData, yamlMap)
    newYamlSerial = ruamel.yaml.dump(newYaml, Dumper=ruamel.yaml.RoundTripDumper)
    
    print(newYamlSerial)
    
def singleNewTest():
    yamlMap = {}
    yamlMap["Architecture Definitions/Backend/Backend Infra/Test"] = "someFilePath"
    
def existingCollisionTest():
    yamlMap = {}
    yamlMap["Architecture Definitions/Backend/Backend Infra/Event Bus"] = "architecture-definitions/backend/eventbus/eventbus.md"

def directoryCollisionTest():
    yamlMap = {}
    yamlMap["Architecture Definitions/Backend/Backend Infra/Event Bus"] = "architecture-definitions/backend/eventbus/eventbus.md"
    testHelper(yamlMap)
    
singleNewTest()
existingCollisionTest()
directoryCollisionTest()