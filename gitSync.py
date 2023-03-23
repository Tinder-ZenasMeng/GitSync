import sys
sys.path.insert(0, "./lib")
from syncEntry import SyncEntry
from dotenv import load_dotenv
from typing import MutableSequence, Tuple
from github import ContentFile
import os
import github as gh
import utils
import githubUtils
import yamlUtils
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
                strippedRootDir = entry.path[entry.path.find("/") + 1:]
                destPath = os.path.join(syncEntry.destUrl, strippedRootDir)
                pathFileMap[destPath] = (syncEntry.yamlPath, entry)
                logging.info(f"Map for `{destPath}` created.")
        else:
            pathFileMap[syncEntry.destUrl] = (syncEntry.yamlPath, sourceContentFile)
            logging.info(f"Map for `{syncEntry.destUrl}` created.")
    return pathFileMap

# Removes items from `pathFileMap` if the file's SHA is equivalent to the one in the destination repo.
def getEquivalentSourceFiles(github, pathFileMap, destRepoName):
    logging.info("Starting comparison with destination files.")
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

def processSingleRepo(github, configData):
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
    
    if len(pathFileMap) == 0:
        logging.info(f"Repo `{DEST_REPO}`: No files needed to be sync'd.")
        return
    
    # Create blobs inside destination repo based off of URL maps.
    blobs = githubUtils.createBlobElementsInRepo(github, DEST_REPO, pathFileMap)

    # Update yaml; assumes a `mkdocs.yml` at root of dest_repo.
    yamlConfig = utils.getFile(github, DEST_REPO, MKDOCS_STR)
    yamlContent = yamlConfig.decoded_content
    yamlData = ruamel.yaml.load(yamlContent, Loader=ruamel.yaml.RoundTripLoader)
    
    newYaml = yamlUtils.constructNewYaml(yamlData, pathFileMap)
    
    # # Create yaml blob.
    newYamlSerial = ruamel.yaml.dump(newYaml, Dumper=ruamel.yaml.RoundTripDumper)
    yamlBlob = githubUtils.createBlobElementInRepo(github, DEST_REPO, newYamlSerial, "utf-8", MKDOCS_STR)
    blobs.append(yamlBlob)

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
            processSingleRepo(github, repoConfigData)
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