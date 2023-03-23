import hashlib
import json
from github import Github, ContentFile

def sha1DigestGit(size, dataStr):
    data = "blob " + str(size) + "\0" + dataStr
    return sha1DigestBytes(bytes(data, "utf-8"))
    
def sha1DigestBytes(bytes):
    return hashlib.sha1(bytes).hexdigest()
    
def sha1DigestFile(path):
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()

    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
            
    return sha1.hexdigest()


def writeBytesToFile(fileName: str, bytes: bytearray):
    file = open(fileName, 'w')
    file.write(bytes)
    file.close()

def readJsonFile(path: str) -> dict:
    f = open(path, "r")
    data = json.load(f)
    f.close()
    return data

def readJsonString(string: str) -> dict:
    return json.loads(string)

def getFile(github: Github, repo, filePath) -> ContentFile.ContentFile:
    repo = github.get_repo(repo)
    contents = repo.get_contents(filePath)
    return contents

def getFilesFromDirRecursive(github: Github, repo: str, dirPath: str):
    allFiles = []
    repo = github.get_repo(repo)
    contents = repo.get_contents(dirPath)
    while contents:
        if isinstance(contents, list):
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                allFiles.append(file_content)
        else:
            allFiles.append(contents)
            break
        
    return allFiles