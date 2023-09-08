# Ghaf Github Pull Request Hydra Builder
<br>
Builder for *Ghaf *project [https://github.com/tiiuae/ghaf](URL) Github Pull Requests

Uses Ghaf build tools from [https://github.com/tiiuae/ci-public](URL) (assumes usage of Ghaf docker based Hydra build system implementation)

Activates Hydra to build new open Pull Requests (for the main repo under observations) or allready built open PRs with new changes

Can be used in service mode (polling frequently repo changes) or cherry picking one open PR for building or just running once here and then

Keeps internal records for build PRs and rebuild changed PRs (building means commanding Hydra to initiate build for given PR branch and getting "ok" from Hydra)
<br>
<br>

##USAGE
<br>
1) Setup Ghaf  Hydra build system (tools&docs in  [https://github.com/tiiuae/ci-public](URL))
<br>
2) Set Hydra env variables HYDRACTL_USERNAME="hydra" and HYDRACTL_PASSWORD="zzzzz"
<br>
3) Create tokenfile to include your access token to Ghaf repo
<br>
4) Start (one off run) poller execution: python3 PollPr.py (use docker host , tools repo in the host)
<br>
<br>
Editing "build" information files, one can manipulate which PR number is thought to be build or not
<br>

##CONFIGURATIONS (in PollPR.py)
<br>
<br>
**TOKENFILE**="tokenfile" # Includes token to access Github repo for these PR observations
<br>
**TESTREPO**='mnokka-unikie/ghaf' # Ghaf repo under PR observations 
<br>
**ORGANIZATION**="tiiuae" # required Github organization membership before building PR proceeds
<br>
**BUILDPRSFILE**="pr2_data" # local file to store handled (built) PRs by their Github ID
<br>
**BUILDCHANGEDPRSFILE**="pr2_changed_data" # local file to store builds done for open (but build initially) and changed PRs
<br>
**HYDRACTL**="./hydractl.py" # CLI command location (Ghaf inhouse public tool) to manage Hydra operations
<br>
**EXT_PORT=3030** # Hybdra port dedicated for the build server (docker will expose this to the host)
<br>
**RUNDELAY=1 **# minutes to wait before next execution of this script (in service mode

## Commandline

usage: PollPR.py [-h] [-v] [-d dry] [-t verbose] [-s service] [-p cherrypick]

Github PullRequest Hydra builder activator

options:
<br>
  -h, --help     show this help message and exit
<br>
  -v             Check Github open PRs and activate Ghaf Hydra build
<br>
  -d dry         Dry run mode
<br>
  -t verbose     Verbose, talking, mode
<br>
  -s service     Service mode, runtime delays in secs
<br>
  -p cherrypick  Cherry pick PR number, ignore others


## Examples

PollPR.py --> run once
<br>
PollPr.py -d on --> run once drymode, do not do any changes
<br>
PollPr.py -p 42 -->  Ask Hydra to build PR42
<br>
PollPr.py -s 60 --> run every hour

#