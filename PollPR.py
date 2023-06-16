#
# Get Github open pull requests for given branch (use number ID)
# Show how to get one open pull request's source and target branches
# Use existing (file db) to check what PRs have been build in the past in order to select new to be build
# Aiming to be used with Hydra (Nixos) builder

#mika.nokka1@gmail.com 13.62023



from github import Github
import os,sys,argparse
import json
import urllib.request
from urllib.request import Request, urlopen
from collections import defaultdict
import copy



TOKENFILE="tokenfile" # NOT TO BE STORED PUBLIC GIT
TESTREPO='mnokka-unikie/GithubActionForPR'
TESTPR='https://api.github.com/repos/mnokka-unikie/GithubActionForPR/pulls/1' # used in test known repo to have open pull requests


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

# all open prs into a dictionary
open_prs=defaultdict(lambda:"OFF")
print ("------ All open PullRequest for repo: "+TESTREPO+" -------")
for pull in pulls:
    print (pull)
    #print (pull.number)
    open_prs.update({pull.number: "ON"}) 

#print (open_prs)
#print ("1->"+str(open_prs[1]))
#print ("3->"+str(open_prs[3]))

#read done PRs in from disk
done_prs=defaultdict(lambda:"NONE")
myfile = open("pr_data", "a+")  
myfile.seek(0) # a+ adds fd to end of file, for appends, we need to read from start
print ("------Built PR numbers from the DB file: "+TOKENFILE+" ------")
for one_pr_number in myfile:
    print (str(one_pr_number),end='')
    done_prs[int(one_pr_number)]="DONE"


#print ("2:")
#print (done_prs[2])
#print ("4:")
#print (done_prs[4])
#print(done_prs)

print("------ Checking which open PRs are new and require building ------")
copy_done_prs=copy.copy(done_prs) # shallow copies are iterared over as defaultdict changes dict size when default value must be returned
copy_open_prs=copy.copy(open_prs)
counter=1

for doneline in copy_done_prs:
    for openline in copy_open_prs:

        if (open_prs[counter]=="ON" and done_prs[counter]=="DONE"):
            print ("OLD PR in PR list, has been built:"+str(openline))
            #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
            print ("*********************************************************")
        elif (open_prs[counter]=="ON" and done_prs[counter]=="NONE"):
            print  ("NEW PR, going to build this:"+str(counter))
            #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
            print ("*********************************************************")
        elif (open_prs[counter]=="OFF" and done_prs[counter]=="DONE"):
            print  ("OLD done PR:"+str(counter))
            #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
            print ("*********************************************************")
        counter=counter+1

# Get repos open pull requests
url=TESTPR
with urlopen(url) as response:
    body = response.read()

data = json.loads(body)
#print(data)
print ("----------------------------------------")  

SOURECE="NONE"
TARGET="NONE"  
try:
    print("SOURCE PR BRANCH:"+data["head"]["ref"])
    SOURCE=data["head"]["ref"]
except KeyError:
    print("no head ref found")  
  
  
try:
    print("TARGET BRANCH (like main/master):"+data["base"]["ref"])
    TARGET=data["base"]["ref"]
except KeyError:
    print("no base ref found")  
    
print("TBD: Construct Hydra(for project tiiuae/ghaf) build job set for branch:"+SOURCE )
