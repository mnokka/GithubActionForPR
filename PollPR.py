#
#
# Get Github open pull requests for given branch (use number ID)
# Show how to get one open pull request's source and target branches
# Use existing (file db) to check what PRs have been build in the past in order to select new to be build
# 
# Aiming to be used with Hydra (Nixos) builder for Ghaf project; Build new Pull Requests before merging to main line

# mika.nokka1@gmail.com 13.6.2023



from github import Github
import os,sys,argparse
import json
import urllib.request
from urllib.request import Request, urlopen
from collections import defaultdict
import copy
import time
from datetime import datetime

import subprocess

TOKENFILE="tokenfile" # NOT TO BE STORED PUBLIC GIT, used to access Github repo

TESTREPO='mnokka-unikie/ghaf' # Repo under PR observations
TESTPR='https://api.github.com/repos/mnokka-unikie/Ghaf/pulls' # used in test known repo to have open pull requests
ORGANIZATION="tiiuae" # required organization membership before building PR
BUILDPRSFILE="pr2_data" # local file to store handled (built) Pull Requests by their Github ID
BUILDCHANGEDPRSFILE="pr2_changed_data" # local file to store builds done for open, allready built, but PR having changes being made 


# Hydra build server POC related settings, change accordingly via conf file (TBD)
HYDRACTL="./hydractl.py" # CLI command (Ghaf inhouse) to manage Hydra operations 
EXT_PORT=3030 # Hybdra port dedicated for this POC build server
SERVER="http://localhost:"+str(EXT_PORT)

def main(argv):
    Finder()

##########################################################################################
# Check if any new (not built) pull requests exists in defined repo (fro main branch
#
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
    #Read done PRs in from disk, initialize possible empty bookkeeping files 
    done_prs=defaultdict(lambda:"NONE")
    myfile = open(BUILDPRSFILE, "a+")  
    myChangedfile= open(BUILDCHANGEDPRSFILE, "a+")
    
    # add fictional done PR number to an empty file in order to keep logic running....
    if (os.stat(BUILDPRSFILE).st_size == 0):
        print ("No done PRs found, adding fictional PR number to an empty file")
        FICTIONALPR=123456789 # there cant be so many PRs just like 640Kb was enough for running Dos programs
        FICTIONALPR=str(FICTIONALPR)+"\r\n"
        myfile.seek(0) 
        myfile.write(FICTIONALPR)
        
    # add fictional changed PR number (and timetoken) to an empty file in order to keep logic running....
    if (os.stat(BUILDCHANGEDPRSFILE).st_size == 0):
        print ("No done PRs file found, adding fictional PR number and change time to an empty file")
        FICTIONALPR=123456789 # there cant be so many PRs just like 640Kb was enough for running Dos programs
        FICTIONALCHANGETIME="2020-02-02-23-00-00"
        FICTIONALCHANGEPR=str(FICTIONALPR)+","+FICTIONALCHANGETIME+"\r\n"
        myChangedfile.seek(0) 
        myChangedfile.write(FICTIONALCHANGEPR)    
    ##########################################################################################################
    
    myfile.seek(0) # a+ adds fd to end of file, for appends, we need to read from start
    print ("------Built PR numbers from the DB file: "+BUILDPRSFILE+" ------")
    for one_pr_number in myfile:
        print (str(one_pr_number),end='')
        done_prs[int(one_pr_number)]="DONE"
    
    
    print("------ Checking which open PRs are new and require building ------")
    copy_done_prs=copy.copy(done_prs) # shallow copies are iterared over as defaultdict changes dict size when default value must be returned
    copy_open_prs=copy.copy(open_prs)
    tbd_list=[]
    counter=1
    ###############################################################################
    # Process all repo's open pull requests
    processed_pr=[]
    SOURCE="NONE"
    TARGET="NONE"  
    SOURCE_REPO="NONE"
    ErroCounter=0    
    
    
    for newPr in copy_open_prs:
        
        url=TESTPR+"/"+str(newPr)
        with urlopen(url) as response:
            body = response.read()        
        data = json.loads(body)

        for doneline in copy_done_prs:
               
                #check duplicate PRs in db file
                if (counter in processed_pr):
                    print (processed_pr)
                    print ("---> Duplicate PR found in db file: "+str(counter) +" skipping!")
                    counter=counter+1
                    print ("--------------------------------------------------------------------------------------------------")  
                    break
        
                elif (open_prs[counter]=="ON" and done_prs[counter]=="DONE"):
                    print ("==> OLD PR in PR list, has been built:"+str(counter))
                    
                    print ("Checking if this (still open) PR has been changed")
                    pr=repo.get_pull(counter)
                    answer,changetime=CheckChangedPR(pr,repo,counter)
                    if (answer == "YES"):
                        print ("PR has been changed indeed")
                        #timetoken=GetTimeToken()
                        #print ("Using timetoken:",timetoken," to differentiate from orginal PR build")
                        print ("PR change timetoken in use:"+str(changetime))
                        
                        processed_pr.append(counter)
                        if (counter not in tbd_list):
                            tbd_list.append(counter)
                        else:
                            print("not adding")
                        
                        changeTimeCleaned = str(changetime).replace(" ", "-") # hydra doesnt like spaces in arguments, nor :
                        changeTimeCleaned=changeTimeCleaned.replace(":","-")
                        print ("Cleaned (book keeping) timetoken:"+changeTimeCleaned)
                        
                        answer=GetChangePRData(pr,counter,myChangedfile,changeTimeCleaned,BUILDCHANGEDPRSFILE)
                        if (answer=="YES"):
                            PRBuilding(data,ErroCounter,g,counter,myfile,tbd_list,changeTimeCleaned)
                        else:
                            print ("")
                        
                        #processed_pr.append(counter)
                    #
                    else:
                        print ("No PR changes, no actions needed")
                        processed_pr.append(counter)
                    print ("--------------------------------------------------------------------------------------------------")  
                
                elif (open_prs[counter]=="ON" and done_prs[counter]=="NONE"):
                    print  ("==> NEW PR, going to build this:"+str(counter))
                    processed_pr.append(counter)
                    if (counter not in tbd_list):
                        tbd_list.append(counter)
                    else:
                        print("not adding")

                    timetoken=""
                    PRBuilding(data,ErroCounter,g,counter,myfile,tbd_list,timetoken)
                    
               
                elif (open_prs[counter]=="OFF" and done_prs[counter]=="DONE"):
                    print  ("==> OLD done PR:"+str(counter))
                    processed_pr.append[counter]
                
                
                counter=counter+1


#########################################################################################
#
def PRBuilding(data,ErroCounter,g,counter,myfile,tbd_list,timetoken):

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
                        if (counter in tbd_list):
                            print ("------> Handling PR number:"+str(counter))
                            if (ErroCounter==0):
                           
                                PRActions(SOURCE,counter,TARGET,myfile,USER,SOURCE_REPO,timetoken)

                            else:
                                print("Errors in PR data from Github, not doing build activities")    
                    else:
                        print("The user: '{USER}' is not a member of the organization '{ORGANIZATION}'")
                        print ("No build activities done")
                    print ("--------------------------------------------------------------------------------------------------")  
                    
                    #pr=repo.get_pull(counter)
                    #answer=CheckChangedPR(pr,repo,counter)
                    #print("answer:",answer)

#########################################################################################
# Check if PR (still open) has been changed since creation time
#
def CheckChangedPR(pr,repo,counter):

                    print("Checking PR:",pr)
                    pr=repo.get_pull(counter)
                    CREATED=pr.created_at
                    commits=pr.get_commits()
                    # Sort the commits by the commit timestamp in descending order
                    sorted_commits = sorted(commits, key=lambda c: c.commit.committer.date, reverse=True)
                    print ("Found commits:"+str(sorted_commits))
                    # Get the timestamp of the most recent commit
                    CHANGED= sorted_commits[0].commit.committer.date
                    #CHANGED=pr.changed_at
                    print ("CREATED:"+str(CREATED))
                    print ("CHANGED:"+str(CHANGED))

                    date_format = "%Y-%m-%d %H:%M:%S"
                    time_diff_mins = (CHANGED - CREATED).total_seconds() / 60
                    print ("Time difference in minutes:",time_diff_mins)
                    
                    if (time_diff_mins > 10):
                        print ("Possible change in open PR detected, may require rebuilding")
                        return "YES",CHANGED
                    else:
                        ("No changes for open PR detected")
                        return "NO",""
                    

##########################################################################################
# Construct Hydra build command from PullRequests data (Using Ghaf inhouse CLI command)
# Record handled PR info to local db file
#
def PRActions(SOURCE,PR,TARGET,myfile,USER,SOURCE_REPO,timetoken):
    OK_CMDEXE_COUNTER=0
    print("")
    print("Construct Hydra(for project tiiuae/ghaf) build job set for branch:"+SOURCE )
    print ("--> Target main branch:"+TARGET)
    print ("--> Source branch:" +SOURCE)
    print ("--> Source repo:"+SOURCE_REPO)
    print ("--> PR number:"+str(PR))
    print ("--> HYDRACTL command location used: "+HYDRACTL) 
    print ("--> Hydra port:"+str(EXT_PORT))
    print ("--> Hydra server:"+SERVER)
    print ("--> User:"+USER)
    print ("--> Timetoken:"+timetoken)
    print ("")
    DESCRIPTION="\"PR:"+str(PR)+" User:"+USER+" Repo:"+SOURCE_REPO+" Branch:"+SOURCE+"\""
                                    
                                #processed_pr.append(counter)
                                #if (counter not in tbd_list):
                                #    tbd_list.append(counter)
                                #else:
                                #    print("not adding to done table ??")
                                #print ("--------------------------------------------------------------------------------------------------")  
                                
    if (len(timetoken) == 0):
       PROJECT=USER+"X"+SOURCE
    else:
        PROJECT=USER+"X"+SOURCE+"X"+timetoken
        
    #two phased convertings got this item usage working working....
    PROJECT = PROJECT.encode('ascii',errors='ignore')
    #Then convert it from bytes back to a string using:
    PROJECT = PROJECT.decode()

    FLAKE="git+"+SOURCE_REPO+"/?ref="+SOURCE
    if (len(timetoken) == 0):
        JOBSET=SOURCE+"X"+str(PR)
    else: 
        JOBSET=SOURCE+"X"+str(PR)+"X"+timetoken
        
    print ("--> Hydra PROJECT:"+PROJECT)    
    print ("--> Hydra DESCRIPTION:"+DESCRIPTION)
    print ("--> Hydra FLAKE:"+FLAKE)
    print("--> Hydra JOBSET:"+JOBSET)
    APCOMMAND="python3 "+HYDRACTL+" "+SERVER+" AP --project "+PROJECT+" --display "+DESCRIPTION 
    AJCOMMAND="python3 "+HYDRACTL+" "+SERVER+" AJ --description "+DESCRIPTION+" --check 300 --type flake --flake "+FLAKE+" -s enabled --jobset "+JOBSET+" --project "+PROJECT
    print ("")
    print ("Hydra CLI APCOMMAND:"+APCOMMAND)
    print ("")
    print ("Hydra CLI AJCOMMAND:"+AJCOMMAND)
    DONE=PR # write PR number to db file if both CMD exections are ok
    DONE=str(DONE)+"\r\n"
    #myfile.write(DONE)
    
    # NOTE: As executing commands from Python file failed (Hydra jobset creation) and using same commands were ok from shell
    # saving commands to file and executing the content from the read file.....
    # this is temp solution for this POC only

    cmdfile1 = open("cmdfile1", "w")  
    #cmdfile1.seek(0) # only if mode a used
    cmdfile2 = open("cmdfile2", "w")  
    #cmdfile2.seek(0)
    FIRSTLINE="#!/bin/bash"+"\r\n"
    
    cmdfile1.write(FIRSTLINE)
    cmdfile1.write(APCOMMAND)
    
    cmdfile2.write(FIRSTLINE)
    cmdfile2.write(AJCOMMAND)

    cmdfile1.close()
    cmdfile2.close()

    cmd1=open("cmdfile1","r")
    APline1=cmd1.read()   
    rc,out,err=ExeCMD(APline1)
    if (rc != 0):
        print("Command execution error:"+str(rc))
        print ("Error message:"+str(err))
    else:
        print("OK command execution")
        OK_CMDEXE_COUNTER +=1
    
    time.sleep(2)
    cmd2=open("cmdfile2","r")
    AJline2=cmd2.read()
    rc,out,err=ExeCMD(AJline2)
    if (rc != 0):
        print("Command execution error:"+str(rc))
        print ("Error message:"+str(err))
    else:
        print("OK command execution")
        OK_CMDEXE_COUNTER +=1
        
    if (OK_CMDEXE_COUNTER == 2):
        if (len(timetoken) == 0):
            print ("2 correct CMD executions,NEW build, going to record PR:"+str(PR)+" as done deed")
            myfile.write(DONE)
        else:
            print ("2 correct CMD executions, CHANGED PR build, going to record PR:"+str(PR)+" with CHANGE time:"+timetoken+" to own db file")
    else:
        print ("-------------------------------------------------------------------------------")
        print ("ERROR ===> CMD executions errors found, NOT marking PR:"+str(PR)+" as done")
        print ("-------------------------------------------------------------------------------")
        
    #clean temp commandfiles
    os.remove("./cmdfile1")
    os.remove("./cmdfile2")
    time.sleep(2)

    print ("*******************************************************************************************************")
    
##############################################################
#  Execute given command string and return system feedback
# 
def ExeCMD(commandLine):

    print ("------------------------------------------------------------------------------------------")
    print("Executing command:"+commandLine)    
    print ("------------------------------------------------------------------------------------------")
    
    sp = subprocess.Popen(commandLine,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    rc=sp.wait()
    out,err=sp.communicate()

    return rc,out,err

############################################################################
# Create datetime token (like 15.10.1971 15:00 ---> 151019711500)
# 
def GetTimeToken():
    now = datetime.now()
    day = now.strftime("%d")
    month = now.strftime("%m")
    year = now.strftime("%Y")
    hour = now.strftime("%H")
    minute = now.strftime("%M")
    
    date_time_string = day + month + year + hour + minute
    return date_time_string


########################################################  
#
def GetChangePRData(pr,counter,myChangedfile,changetime,BUILDCHANGEDPRSFILE):
    #print ("GetChangePRData executing for PR:"+str(pr))
    #print ("counter:"+str(counter))
    print ("-----------------------------------------------------")
    pr=str(counter)
    myChangedfile.seek(0) # we need to read from start
    print ("Changed PR numbers and change times from the DB file: "+BUILDCHANGEDPRSFILE)
    foundnewtime=0
    #filefoudnewPR=0
    PRCount=0
    FilePRNumbers=[]
    ContentOfFilePRNumber=[]
    
    myChangedfile.seek(0)
    for one_line in myChangedfile:
       PRCount=PRCount+1
       ContentOfFilePRNumber.append(one_line) # get tuntime copy for possible changes
    PRCount=PRCount-1 # fictional first value
    print ("Existing PRs with done change builds:"+str(PRCount))
   
    myChangedfile.seek(0) 
    for one_line in myChangedfile:
        #print ("Changed PR line:"+one_line)
        
        values = one_line.strip().split(",")
        readPR=values[0]
        readChangetime=values[1:] 
        
        #print ("readPR:"+readPR+"   pr:"+pr)
        if (readPR == pr):
            FilePRNumbers.append(pr)
            count=len(readChangetime)
            newChangetime=""          
            for item in readChangetime:
                print  ("Latest changetime found/build for this PR:"+item)
                if (changetime==item):
                    print ("Changetime is same as in latest done build. No actions needed")
                    count=count-1
                else:
                    print ("Internal: No match with current changetime list item...")
                newChangetime=item
            if (count>0):
                print ("New changetime found:"+str(newChangetime))
                foundnewtime=foundnewtime+1
         
                
    if (pr in FilePRNumbers and foundnewtime==0):
         print ("No new PRs nor existing PRs with new changes found. No actions needed")
         return "NO"
    elif (pr not in FilePRNumbers):
        print ("New PR:"+pr+" with changes found. Cleaned changetime:"+changetime)    
        print ("Going to update changed PRs file!")
        addline=pr+","+changetime
        ContentOfFilePRNumber.append(addline)
        myChangedfile.seek(0)
        for line in ContentOfFilePRNumber: # write whole "changed PRs build" file again. 
            niceline=line+"\r"
            myChangedfile.write(niceline)
        return "YES"
        
    #for line in ContentOfFilePRNumber:
    #    print ("line:"+line)


########################################################  
if __name__ == "__main__":
    main(sys.argv[1:]) 
