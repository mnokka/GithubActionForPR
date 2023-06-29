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
#TESTREPO='mnokka-unikie/GithubActionForPR'
#TESTPR='https://api.github.com/repos/mnokka-unikie/GithubActionForPR/pulls/1' # used in test known repo to have open pull requests
#ORGANIZATION="tiiuae" # required organization membership before building PR
#BUILDPRSFILE="pr_data"

TESTREPO='mnokka-unikie/ghaf'
TESTPR='https://api.github.com/repos/mnokka-unikie/Ghaf/pulls' # used in test known repo to have open pull requests
ORGANIZATION="tiiuae" # required organization membership before building PR
BUILDPRSFILE="pr2_data"



# Hydra POC settings, change accordingly via conf file (TBD)
HYDRACTL="../hydractl/hydractl.py" 
EXT_PORT=3030
SERVER="http://localhost:"+str(EXT_PORT)


def main(argv):
    Finder()

#############################################################################
def Finder():
    CREATED=""
    CHANGED=""
    
    #########################################################################
    #Authorization to Github
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
    

    
    ##########################################################################
    # Get all open prs into a dictionary
    i=0
    open_prs=defaultdict(lambda:"OFF")
    print ("------ All open PullRequest for repo: "+TESTREPO+" -------")
    for pull in pulls:
        print (pull)
        #print (pull.number)
        open_prs.update({pull.number: "ON"}) 
        i=i+1
        
    if (i==0):
        print ("No open PRs found, exiting")    
        #print ("i:"+str(i))
        sys.exit(4)

    ###########################################################################
    #read done PRs in from disk, initialize possible empty file 
    done_prs=defaultdict(lambda:"NONE")
    myfile = open(BUILDPRSFILE, "a+")  
    
    # add fictional done PR number to an empty file in order to keep logic running....
    if (os.stat(BUILDPRSFILE).st_size == 0):
        print ("No done PRs found, adding fictional PR number to an empty file")
        FICTIONALPR=123456789 # there cant be so many PRs just like 640Kb is enough for running Dos programs
        FICTIONALPR=str(FICTIONALPR)+"\r\n"
        myfile.seek(0) 
        myfile.write(FICTIONALPR)
        
    
    myfile.seek(0) # a+ adds fd to end of file, for appends, we need to read from start
    print ("------Built PR numbers from the DB file: "+BUILDPRSFILE+" ------")
    for one_pr_number in myfile:
        print (str(one_pr_number),end='')
        done_prs[int(one_pr_number)]="DONE"
    
    
    print("------ Checking which open PRs are new and require building ------")
    copy_done_prs=copy.copy(done_prs) # shallow copies are iterared over as defaultdict changes dict size when default value must be returned
    copy_open_prs=copy.copy(open_prs)
    #tbd=0
    
    #newPRs=len(open_prs)
    #print ("size:"+str(newPRs))
    tbd_list=[]
    counter=1
    ###############################################################################
    # Process all repo's open pull requests
    tbd_list=[]
    processed_pr=[]
    counter=1
    SOURCE="NONE"
    TARGET="NONE"  
    SOURCE_REPO="NONE"
    ErroCounter=0

    for newPr in copy_open_prs:
        
        url=TESTPR+"/"+str(newPr)
        with urlopen(url) as response:
            body = response.read()        
        data = json.loads(body)
        #print(data)
        print ("--------------------------------------------------------------------------------------------------")  
        

        for doneline in copy_done_prs:
           # for openline in copy_open_prs:

                #check duplicate PRs in db file
                if (counter in processed_pr):
                    print (processed_pr)
                    print ("---> Duplicate PR found in db file: "+str(counter) +" skipping!")
                    counter=counter+1
                    break
        
                elif (open_prs[counter]=="ON" and done_prs[counter]=="DONE"):
                    print ("==> OLD PR in PR list, has been built:"+str(counter))
                    #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
                    #print ("*********************************************************")
                    processed_pr.append(counter)
                elif (open_prs[counter]=="ON" and done_prs[counter]=="NONE"):
                    print  ("==> NEW PR, going to build this:"+str(counter))
                    #tbd=counter
                    processed_pr.append(counter)
                    if (counter not in tbd_list):
                        tbd_list.append(counter)
                    else:
                        print("not adding")
                    #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
                    
                    
                    
                    ##############################################################################
                    # parse PR info (from Github JSON)
                    SOURCE="NONE"
                    TARGET="NONE"  
                    SOURCE_REPO="NONE"
                    ErroCounter=0
                    print ("")
                    try:
                        print("==> SOURCE PR BRANCH:"+data["head"]["ref"])
                        SOURCE=data["head"]["ref"]
                    except KeyError:
                        print("ERROR: no head ref found")
                        ErroCounter=ErroCounter+1  
                        
                    try:
                        print("==> TARGET BRANCH (like main/master):"+data["base"]["ref"])
                        TARGET=data["base"]["ref"]
                        if (TARGET=="main"):
                            print("==> OK target(main) repo")
                        else:
                            print ("ERROR: source repo is not main")
                            ErroCounter=ErroCounter+1
                            #sys.exit(5)
                    except KeyError:
                        print("no base ref found")  
                    
                    try:
                        print("==> SOURCE REPO:"+data["head"]["repo"]["html_url"])
                        SOURCE_REPO=data["head"]["repo"]["html_url"]
                    except KeyError:
                        print("ERROR:no source repo info found")
                        ErroCounter=ErroCounter+1
                    
                    USER=data["user"]["login"]
                    org = g.get_organization(ORGANIZATION)
                    user = g.get_user(USER)
                    
                    if (org.has_in_members(user) or USER=="mnokka"): # TBD remove test user backdoor
                        print(f"---> The user '{USER}' is a member of the organization '{ORGANIZATION}'.")
                        #for x in tbd_list:
                        if (counter in tbd_list):
                            print ("------> Handling PR number:"+str(counter))
                            if (ErroCounter==0):
                                PRActions(SOURCE,counter,TARGET,myfile,USER,SOURCE_REPO)
                            else:
                                print("Errors in PR data from Github, not doing build activities")    
                    else:
                        print(f"The user '{USER}' is not a member of the organization '{ORGANIZATION}'.")
                        print ("No build activities done")
                    
                    
                    

                    ######################################################################################
                    # Checking if done PR has been updated is under construction 
                    #pr=repo.get_pull(counter)
                    #CREATED=pr.created_at
                    #commits=pr.get_commits()
                    # Checking if done PR has been update is under construction
                    # Sort the commits by the commit timestamp in descending order
                    #sorted_commits = sorted(commits, key=lambda c: c.commit.committer.date, reverse=True)
                    #print ("commits:"+str(sorted_commits))
                    # Get the timestamp of the most recent commit
                    #CHANGED= sorted_commits[0].commit.committer.date
                    #CHANGED=pr.changed_at
                    #print ("CREATED:"+str(CREATED))
                    #print ("CHANGED:"+str(CHANGED))
                    #print ("*********************************************************")
                    #########################################################################################
                elif (open_prs[counter]=="OFF" and done_prs[counter]=="DONE"):
                    print  ("==> OLD done PR:"+str(counter))
                    processed_pr.append[counter]
                    #print ("counter:"+str(counter)+"  openline:"+str(openline)+" "+str(open_prs[openline])+"  doneline:"+str(doneline)+" "+str(done_prs[doneline]))
                    #print ("*********************************************************")

                
                counter=counter+1

########################################################
# Construct Hydra build command from PullRequests data
# Record hadnled PR info to local db file
#
def PRActions(SOURCE,PR,TARGET,myfile,USER,SOURCE_REPO):
    print("")
    print("TBD: Construct Hydra(for project tiiuae/ghaf) build job set for branch:"+SOURCE )
    print ("--> Target main branch:"+TARGET)
    print ("--> Source branch:" +SOURCE)
    print ("--> Source repo:"+SOURCE_REPO)
    print ("--> PR number:"+str(PR))
    print ("--> HYDRACTL command: "+HYDRACTL) 
    print ("--> Hydra port:"+str(EXT_PORT))
    print ("--> Hydra server:"+SERVER)
    print ("--> User:"+USER)
    print ("Fake OK command execution detected, going to record fake PR as done deed")
    print ("")
    DESCRIPTION="\"PR:"+str(PR)+" User:"+USER+" From branch:"+SOURCE+"\""
    PROJECT=str(PR)+"-"+USER+"-"+SOURCE
    FLAKE="git+https://github.com/tiiuae/ghaf/?ref="+SOURCE
    JOBSET=str(PR)+"-"+SOURCE
    print ("--> PROJECT:"+PROJECT)    
    print ("--> DESCRIPTION:"+DESCRIPTION)
    print ("--> FLAKE:"+FLAKE)
    print("--> JOBSET:"+JOBSET)
    APCOMMAND="python3 "+HYDRACTL+" "+SERVER+" AP --project "+PROJECT+" --display "+DESCRIPTION 
    AJCOMMAND="python 3 "+HYDRACTL+" "+SERVER+" AJ --project "+PROJECT+" --description "+DESCRIPTION+" --check 300 --type flake --flake "+FLAKE+" -s enabled --jobset "+JOBSET
    print ("")
    print ("APCOMMAND:"+APCOMMAND)
    print ("")
    print ("AJCOMMAND:"+AJCOMMAND)
    FAKEDONE=33+PR # write PR number to db file, this is testing addition
    FAKEDONE=str(FAKEDONE)+"\r\n"
    myfile.write(FAKEDONE)
    print ("*******************************************************************************************************")
    
########################################################    
if __name__ == "__main__":
    main(sys.argv[1:]) 
    