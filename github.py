#
# V-Ray Python Tools
#
# http://chaosgroup.com
#
# Author: Andrei Izrantcev
# E-Mail: andrei.izrantcev@chaosgroup.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.

import json
import os
import requests
import sys
import urllib.request


def _githubRequest(url):
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        return r.json()
    return None


def _githubCmd(repo, cmd):
    return _githubRequest('https://api.github.com/repos/%s/%s' % (repo, cmd))


def _getBranchSha(repo, branchName):
    r = _githubCmd(repo, 'branches')
    if not r:
        return None
    for branch in r:
        if branch['name'] == branchName:
            return branch['commit']['sha']
    return None


def _getBranchTree(repo, sha):
    return _githubCmd(repo, 'git/trees/%s?recursive=1' % sha)


def _getSubmoduleTree(git_url, recursive=False):
    return _githubRequest("%s?recursive=%i" % (git_url, recursive))


def _cloneTree(treeUrl, repoName, repoUrl, repoBranch, dstDir):
    treeDest = _githubRequest(treeUrl)

    tree     = treeDest['tree']
    treeSize = len(tree)

    for i,blob in enumerate(tree):
        if blob['type'] == 'tree':
            continue
        elif blob['type'] == 'commit':
            commitContents = _githubCmd(repoName, 'contents/%s' % blob['path'])
            if commitContents['type'] == 'submodule':
                repo_name   = repoName
                repo_branch = 'master'

                tree_url = commitContents['git_url']
                repo_url = commitContents['submodule_git_url'][:-4] # Strip '.git' at the end

                sys.stdout.write("\nDownloading submodule: %s\n" % commitContents['name'])

                _cloneTree("%s?recursive=1" % tree_url, repo_name, repo_url, repo_branch, os.path.join(dstDir, blob['path']))
        else:
            fileName = blob['path']

            if fileName.startswith("."):
                continue

            fileMode = int(blob['mode'][3:], 8)

            fileUrl  = "%s/raw/%s/%s" % (repoUrl, repoBranch, fileName)
            filePath = os.path.join(dstDir, fileName)
            fileDirpath = os.path.dirname(filePath)

            if not os.path.exists(fileDirpath):
                os.makedirs(fileDirpath)

            pers = 100 * (i+1) / treeSize
            persStr = ("%i" % pers).rjust(3)

            msg = fileUrl
            if len(msg) > 80:
                msg = msg[:37] + "..." + msg[-37:]
            msg = fileUrl.ljust(80)

            sys.stdout.write("\r[%s%%] Downloading: %s" % (persStr, msg))

            urllib.request.urlretrieve(fileUrl, filePath)
            os.chmod(filePath, fileMode)


def GithubCloneRepo(repo, branch, dstDir):
    repoUrl = "https://github.com/%s" % repo

    treeSHA = _getBranchSha(repo, branch)
    treeUrl = "https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (repo, treeSHA)

    sys.stdout.write("Cloning %s...\n" % repoUrl)

    _cloneTree(treeUrl, repo, repoUrl, branch, dstDir)

    sys.stdout.write("\nCloning done.\n")


if __name__ == '__main__':
    clodeDir = os.path.join(os.path.expanduser("~/tmp"), "vb30")

    githubRepo   = "bdancer/vb30"
    githubBranch = "master"

    GithubCloneRepo(githubRepo, githubBranch, clodeDir)
