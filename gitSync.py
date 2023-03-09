from syncEntry import SyncEntry
from dotenv import load_dotenv
import os
import github as gh
import utils
import githubUtils
import datetime
import logging

def createPathFileMap(github, syncEntryList):
    pathFileMap = dict() # <destUrl, ContentFile>
    
    for syncEntry in syncEntryList:
        sourceContentFile = utils.getFile(github, syncEntry.sourceRepo, syncEntry.sourceUrl)
        
        # Handle directories here.
        if isinstance(sourceContentFile, list):
            dirCrawl = utils.getFilesFromDirRecursive(github, syncEntry.sourceRepo, syncEntry.sourceUrl)
            for entry in dirCrawl:
                destPath = os.path.join(syncEntry.destUrl, entry.path)
                pathFileMap[destPath] = entry
                logging.info(f"Map for `{destPath}` created.")
        else:
            pathFileMap[syncEntry.destUrl] = sourceContentFile
            logging.info(f"Map for `{syncEntry.destUrl}` created.")
    return pathFileMap

def main():
    logging.basicConfig(level=logging.INFO)
    
    load_dotenv()
    github = gh.Github(os.getenv("GH_TOKEN"))
    
    # Read json file
    configData = utils.readJson(os.getenv("CONFIG_FILE"))
    DEST_REPO = configData["destRepo"]
    MAIN_BRANCH = configData["mainBranch"]
    NEW_BRANCH = datetime.datetime.now().strftime("external-sync-%m%d%y-%H%M%S")
    syncEntryList = []
    logging.info("Parsing configuration.")
    for entry in configData["files"]:
        syncEntry = SyncEntry(**entry)
        syncEntryList.append(syncEntry)

    # Create destination URL maps.
    logging.info("Creating file map.")
    pathFileMap = createPathFileMap(github, syncEntryList)

    # Create blobs inside destination repo based off of URL maps.
    blobs = githubUtils.createBlobsInRepo(github, DEST_REPO, pathFileMap)

    # Create new branch and push PR.
    githubUtils.createPrWithBlobs(github, DEST_REPO, MAIN_BRANCH, NEW_BRANCH, blobs)


    # TODO
    # Validate json all file paths are possible.
    ## Source/dest files.

    # Get list of all SHAs from dest and compare to source.
    ## Replace all non matching SHAs.

    # Update mkdocs.yml.
        # Determine new things added.
        # Yaml parse
        # Append data.
    
    # Create PR

    # Ideas
    # Front matter with comment on externally sync'd files?
    # Repo for Map<filePath, SHA>    

if __name__ == "__main__":
    main()