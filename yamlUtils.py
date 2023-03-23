import copy
from collections.abc import Iterable

# Consolidate directories here.
# We check for dupe yaml paths. If there are any, we can assume there is a directory.
# We then get the root yaml path (path without directory), and set the destination URL as `... | {rootPath}/**`
# which will have MkDocs recursively browse that directory.
def consolidateYamlMap(pathFileMap) -> dict[str, str]:
    yamlMap = {} # <yamlPath, filePath>
    for filePath, tuple in pathFileMap.items():
        yamlPath = tuple[0]
        contentFile = tuple[1]
        # We need to strip `docs` from the path, because mkdocs runs off of this directory,
        # instead of the root of the repo.
        strippedFilePath = filePath[filePath.find("/") + 1:]
        
        if yamlPath not in yamlMap:
            yamlMap[yamlPath] = strippedFilePath
        else:
            rootPath = strippedFilePath.split("/")[0]
            yamlMap[yamlPath] = f"... | {rootPath}/**"
    return yamlMap

def isDirectory(filePath):
    return "..." in filePath

def navigateToYamlPath(root, path, normalize = True):
    args = path.split("/")
    
    head = root
    prev = head
    i = 0
    lastIndex = 0
    while i < len(args):
        arg = args[i]
        
        if not isinstance(head, list):
            prev[lastIndex] = [head]
            
        map = {}
        for idx, h in enumerate(head):
            map[list(h.keys())[0]] = idx
        
        prev = head
        if arg in map:
            head = head[map[arg]][arg]
            lastIndex = map[arg]
        else:
            head.append({arg: []})
            head = head[-1][arg]
            
        i = i + 1
            
    # At this point, you are at the specified node, but if your node
    # is a singular item, this might not be helpful.
    if normalize:
        if not isinstance(head, list):
            prev[lastIndex] = { arg: [head] }
            head = prev[lastIndex][arg]
    
    return (prev, head, lastIndex)

# Main yaml logic here.
def modifyYaml(yamlData, yamlMap):
    root = copy.deepcopy(yamlData)
    nav = root['nav']
    
    for yamlPath, filePath in yamlMap.items():
        nodes = navigateToYamlPath(nav, yamlPath, True)
        prev = nodes[0]
        head = nodes[1]
        lastIndex = nodes[2]
        lastArg = yamlPath.split("/")[-1]
        
        if isDirectory(filePath):
            if filePath not in head:
                head.append(filePath)
        else:
            if len(head) == 0:
                # Change to single entry. This is new empty list, so it's the last element in the node.
                prev[-1] = { lastArg: filePath }
            else:
                if filePath not in head:
                    head.append(filePath)
                else:
                    prev[lastIndex] = { lastArg: filePath }
    return root
            
def constructNewYaml(yamlData, pathFileMap):
    yamlMap = consolidateYamlMap(pathFileMap)
    return modifyYaml(yamlData, yamlMap)