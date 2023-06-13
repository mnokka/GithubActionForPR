#
# Get Github open pull requests for given branch
# Show how to get one open pull request's source and target branches

#mika.nokka1@gmail.com 13.62023



from github import Github
import os,sys,argparse
import json
import urllib.request
from urllib.request import Request, urlopen


TOKENFILE="tokenfile"
TESTREPO='mnokka-unikie/GithubActionForPR'
TESTPR='https://api.github.com/repos/mnokka-unikie/GithubActionForPR/pulls/1' # use in test known repo to have open pull requests


file_exists = os.path.exists(TOKENFILE)
if (file_exists):
        file = open(TOKENFILE, "r")
        config_array=file.read().split()
        githubtoken=str(config_array[0])
else:
    print("No Github tokenfile found, check:"+TOKENFILE)
    sys.exit(5)

if githubtoken == None:
    print ("No Github token defined, check:"+TOKENFILE,file=sys.stderr)
    sys.exit(5)

g=Github(githubtoken)


repo = g.get_repo(TESTREPO)
pulls = repo.get_pulls(state='open', sort='created', base='main')


print ("All open PullRequest for repo: "+TESTREPO)
for pull in pulls:
    print (pull)



url=TESTPR
with urlopen(url) as response:
    body = response.read()

data = json.loads(body)
print(data)
print ("----------------------------------------")  
  
try:
    print("SOURCE PR BRANCH:"+data["head"]["ref"])
except KeyError:
    print("no head ref found")  
  
  
try:
    print("TARGET BRANCH;"+data["base"]["ref"])
except KeyError:
    print("no base ref found")  
 