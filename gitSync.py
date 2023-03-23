from syncEntry import SyncEntry
from dotenv import load_dotenv
from typing import MutableSequence, Tuple
from github import ContentFile
import os
import github as gh
import utils
import githubUtils
import datetime
import logging
import ruamel.yaml
import copy


def createPathFileMap(github, syncEntryList: MutableSequence[SyncEntry]) -> dict[str, Tuple[str, ContentFile.ContentFile]]:
    pathFileMap = dict() # <destUrl, ContentFile>
    
    for syncEntry in syncEntryList:
        try:
            sourceContentFile = utils.getFile(github, syncEntry.sourceRepo, syncEntry.sourceUrl)
        except:
            logging.warning(f"Unable to read source file `{syncEntry.sourceUrl}`. Skipping file.")
            continue
        
        # Handle directories here.
        if isinstance(sourceContentFile, list):
            dirCrawl = utils.getFilesFromDirRecursive(github, syncEntry.sourceRepo, syncEntry.sourceUrl)
            for entry in dirCrawl:
                destPath = os.path.join(syncEntry.destUrl, entry.path)
                pathFileMap[destPath] = (syncEntry.yamlPath, entry)
                logging.info(f"Map for `{destPath}` created.")
        else:
            pathFileMap[syncEntry.destUrl] = (syncEntry.yamlPath, sourceContentFile)
            logging.info(f"Map for `{syncEntry.destUrl}` created.")
    return pathFileMap

# Removes items from `pathFileMap` if the file's SHA is equivalent to the one in the destination repo.
def getEquivalentSourceFiles(github, pathFileMap, destRepoName):
    equivalentList = []
    for filePath, tuple in pathFileMap.items():
        contentFile = tuple[1]
        try:
            destFile = utils.getFile(github, destRepoName, filePath)
        except:
            logging.debug(f"{filePath} does not currently exist in {destRepoName}.")
            continue
        
        destFileSha = destFile.sha
        sourceFileSha = contentFile.sha
        
        if destFileSha == sourceFileSha:
            logging.info(f"{contentFile.repository.name}/{filePath}: Source file is equivalent to destination file. Will not sync.")
            equivalentList.append(filePath)
    return equivalentList

# Logic might be a bit complex here. Worth refactoring later.
def constructNewYaml(yamlData, pathFileMap):
    yamlRes = copy.deepcopy(yamlData)
    
    # Consolidate directories here.
    # We check for dupe yaml paths. If there are any, we can assume there is a directory.
    # We then get the root yaml path (path without directory), and set the destination URL as `... | {rootPath}/**`
    # which will have MkDocs recursively browse that directory.
    yamlMap = {} # <yamlPath, [filePath]>
    for filePath, tuple in pathFileMap.items():
        yamlPath = tuple[0]
        contentFile = tuple[1]
        
        if yamlPath not in yamlMap:
            yamlMap[yamlPath] = filePath
        else:
            contentPath = contentFile.path.split("/")[0]
            rootPath = filePath.split(contentPath)[0][:-1]
            yamlMap[yamlPath] = f"... | {rootPath}/**"
            
    for yamlPath, filePath in yamlMap.items():
        args = yamlPath.split("/")
        
        # Navigate yaml until you reach the penultimate key.
        head = yamlRes['nav']
        for arg in args[:-1]:
            # This is a list of dicts. 
            # Each dict should only have one KV pair.
            map = {}
            for idx, h in enumerate(head):
                map[list(h.keys())[0]] = idx
            if arg in map:
                head = head[map[arg]][arg]
            else:
                head.append({arg: []})
                head = head[-1][arg]
        # Append KV pair of { yamlPath[-1]: filePath }
        # Or if directory, set it as its own array.
        if isinstance(head, list):
            if "..." in filePath:
                head.append({args[-1]: [filePath]})
            else:
                head.append({args[-1]: filePath})
    return yamlRes

def workSingleRepo(github, configData):
    # Read json file
    MKDOCS_STR = "mkdocs.yml"
    DEST_REPO = configData["destRepo"]
    MAIN_BRANCH = configData["mainBranch"]
    NEW_BRANCH = datetime.datetime.now(datetime.timezone.utc).strftime("external-sync-%Y-%m-%d-%H%M%S")
    syncEntryList = []
    logging.info("Parsing configuration.")
    for entry in configData["files"]:
        syncEntry = SyncEntry(**entry)
        syncEntryList.append(syncEntry)

    # Create destination URL maps. <destUrl, ContentFile>
    logging.info("Creating file map.")
    pathFileMap = createPathFileMap(github, syncEntryList)

    # Cut down list to be sync'd.
    equivalentList = getEquivalentSourceFiles(github, pathFileMap, DEST_REPO)
    for item in equivalentList:
        del pathFileMap[item]
    
    # Update yaml.
    # Assumes a `mkdocs.yml` at root of dest_repo.
    yamlConfig = utils.getFile(github, DEST_REPO, MKDOCS_STR)
    yamlContent = yamlConfig.decoded_content
    yamlData = ruamel.yaml.load(yamlContent, Loader=ruamel.yaml.RoundTripLoader)
    newYaml = constructNewYaml(yamlData, pathFileMap)
    
    # Create blobs inside destination repo based off of URL maps.
    blobs = githubUtils.createBlobElementsInRepo(github, DEST_REPO, pathFileMap)
    
    newYamlSerial = ruamel.yaml.dump(newYaml, Dumper=ruamel.yaml.RoundTripDumper)
    repo = github.get_repo(DEST_REPO)
    blob = repo.create_git_blob(newYamlSerial, "utf-8")
    element = gh.InputGitTreeElement(path=MKDOCS_STR, mode='100644', type='blob', sha=blob.sha)
    blobs.append(element)

    # Create new branch and push PR.
    githubUtils.createPrWithBlobs(github, DEST_REPO, MAIN_BRANCH, NEW_BRANCH, blobs)

def main():
    logging.basicConfig(level=logging.INFO)
    
    load_dotenv()
    github = gh.Github(os.getenv("GH_TOKEN"))
    
    # Experimental config
    configData = utils.readJsonFile(os.getenv("CONFIG_FILE_V2"))
    SUPPORTED_REPOS = configData["supportedRepos"]
    EXTERNAL_SYNC_CONFIG = "external-sync.json"
    
    # Go through all supported/connected repos and process.
    for repo in SUPPORTED_REPOS:
        try:
            repoConfigFile = utils.getFile(github, repo, EXTERNAL_SYNC_CONFIG)
            repoConfigData = utils.readJsonString(repoConfigFile.decoded_content)
            workSingleRepo(github, repoConfigData)
        except Exception as e:
            logging.error(f"Unable to process repo {repo} due to {e}")
            continue

    # TODO
    # Ideas
    ## Add config setting limit fileTypes?
    ## Front matter with comment on externally sync'd files?
        ### SHA, though.
    ## Repo for Map<filePath, SHA>
        ### Do we need this, though?

if __name__ == "__main__":
    main()