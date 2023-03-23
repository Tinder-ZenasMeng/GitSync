import yamlUtils
import utils
import ruamel.yaml

def testOne():
    with open("sample.yml", 'r') as stream:
        yamlData = ruamel.yaml.load(stream, Loader=ruamel.yaml.RoundTripLoader)
    
    # node = yamlUtils.navigateToYamlPath(yamlData['nav'], "Architecture Definitions/Backend/Backend Infra/Test", True)
    
    yamlMap = {} # <yamlPath, filePath>
    
    # Single New
    # yamlMap["Architecture Definitions/Backend/Backend Infra/Test"] = "someFilePath"
    
    # Existing
    yamlMap["Architecture Definitions/Backend/Backend Infra/Event Bus"] = "architecture-definitions/backend/eventbus/eventbus.md"
    
    # Directory existing
    # yamlMap["Imported Knowledge Bases"] = "... | instrumentation/**"
    
    

    yamlData = yamlData['nav']
    
    newYaml = yamlUtils.modifyYaml(yamlData, yamlMap)
    
    newYamlSerial = ruamel.yaml.dump(newYaml, Dumper=ruamel.yaml.RoundTripDumper)
    
    print(newYamlSerial)
    
    
testOne()