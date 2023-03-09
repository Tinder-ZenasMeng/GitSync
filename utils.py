import hashlib
import json

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


def writeBytesToFile(fileName, bytes):
    file = open(fileName, 'w')
    file.write(bytes)
    file.close()

def readJson(path):
    f = open(path, "r")
    data = json.load(f)
    f.close()
    return data

def getFile(github, repo, filePath):
    repo = github.get_repo(repo)
    contents = repo.get_contents(filePath)
    return contents

def getFilesFromDirRecursive(github, repo, dirPath):
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