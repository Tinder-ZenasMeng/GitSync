import github as gh
    
def createPrWithBlobs(github, destRepo, sourceBranchName, targetBranchName, blobs):
    repo = github.get_repo(destRepo)

    sourceBranchSha = repo.get_branch(sourceBranchName).commit.sha
    targetBranchRef = repo.create_git_ref(ref="refs/heads/" + targetBranchName, sha=sourceBranchSha)
    targetBranchSha = repo.get_branch(targetBranchName).commit.sha

    base_tree = repo.get_git_tree(sha=targetBranchSha)
    tree = repo.create_git_tree(blobs, base_tree)
    parent = repo.get_git_commit(sha=targetBranchSha)
    commit = repo.create_git_commit("commit_message", tree, [parent])
    targetBranchRef.edit(sha=commit.sha)

    repo.create_pull(title="PR title", body="PR body", base=sourceBranchName, head=targetBranchName)    
    
# This is slower than expected... MT?
def createBlobsInRepo(github, repoName, fileContentMap):
    repo = github.get_repo(repoName)
    
    newElements = []
    for filePath, contentFile in fileContentMap.items():
        try:
            blob = repo.create_git_blob(contentFile.content, contentFile.encoding)
            element = gh.InputGitTreeElement(path=filePath, mode='100644', type='blob', sha=blob.sha)
            newElements.append(element)
        except Exception as inst:
            print("Cannot sync file " + contentFile.name + ": " + str(inst))
    return newElements