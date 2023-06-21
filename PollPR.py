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
ORGANIZATION="tiiuae" # required organization membership before building PR
BUILDPRSFILE="pr_data"

# Hydra POC settings, change accordingly via conf file (TBD)
HYDRACTL="../hydractl/hydractl.py" 
EXT_PORT=3030
SERVER="http://localhost:"+str(EXT_PORT)


def main(argv):
    Finder()

#############################################################################
def Finder():
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
    
    #read done PRs in from disk
    done_prs=defaultdict(lambda:"NONE")
    myfile = open(BUILDPRSFILE, "a+")  
    myfile.seek(0) # a+ adds fd to end of file, for appends, we need to read from start
    print ("------Built PR numbers from the DB file: "+BUILDPRSFILE+" ------")
    for one_pr_number in myfile:
        print (str(one_pr_number),end='')
        done_prs[int(one_pr_number)]="DONE"
    
    
    print("------ Checking which open PRs are new and require building ------")
    copy_done_prs=copy.copy(done_prs) # shallow copies are iterared over as defaultdict changes dict size when default value must be returned
    copy_open_prs=copy.copy(open_prs)
    tbd=0
    counter=1
    
    for doneline in copy_done_prs:
        for openline in copy_open_prs:
    
            if (open_prs[counter]=="ON" and done_prs[counter]=="DONE"):
                print ("OLD PR in PR list, has been built:"+str(openline))
                #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
                print ("*********************************************************")
            elif (open_prs[counter]=="ON" and done_prs[counter]=="NONE"):
                print  ("NEW PR, going to build this:"+str(counter))
                print ("TBD: Collect PR to array")
                tbd=counter
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
    
    
    SOURCE="NONE"
    TARGET="NONE"  
    try:
        print("SOURCE PR BRANCH:"+data["head"]["ref"])
        SOURCE=data["head"]["ref"]
    except KeyError:
        print("no head ref found")  
      
      
    try:
        print("TARGET BRANCH (like main/master):"+data["base"]["ref"])
        TARGET=data["base"]["ref"]
        if (TARGET=="main"):
            print("OK terget(main) repo")
        else:
            print ("FAIL. source repo is not main")
            sys.exit(5)
    except KeyError:
        print("no base ref found")  
    
    USER=data["user"]["login"]
    org = g.get_organization(ORGANIZATION)
    user = g.get_user(USER)
    
    # TODO: collect all new PRs to list? to process in a loop
    
    if org.has_in_members(user):
        print(f"The user '{USER}' is a member of the organization '{ORGANIZATION}'.")
        #print("TBD: Construct Hydra(for project tiiuae/ghaf) build job set for branch:"+SOURCE )
        #print ("--> Source branch:" +SOURCE)
        #print ("--> PR number:"+str(tbd))
        PRActions(SOURCE,tbd,TARGET,myfile)
    else:
        print(f"The user '{USER}' is not a member of the organization '{ORGANIZATION}'.")
        print ("No build activities done")

########################################################
def PRActions(SOURCE,tbd,TARGET,myfile):
    print("TBD: HANDLE ALL NEW PRS")
    print("TBD: Construct Hydra(for project tiiuae/ghaf) build job set for branch:"+SOURCE )
    print ("Target maina branch:"+TARGET)
    print ("--> Source branch:" +SOURCE)
    print ("--> PR number:"+str(tbd))
    print ("--> HYDRACTL command: "+HYDRACTL) 
    print ("--> Hydra port:"+str(EXT_PORT))
    print ("--> Hydra server:"+SERVER)
    print ("----------------------------------------------")
    print ("Fake OK command execution detected, going to record fake PR as done deed")
    FAKEDONE=3+tbd
    FAKEDONE=str(FAKEDONE)+"\r\n"
    #rint ("FAKEDONE:"+FAKEDONE)
    myfile.write(FAKEDONE)
    
    
########################################################    
if __name__ == "__main__":
    main(sys.argv[1:]) 
    