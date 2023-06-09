# For Ghaf project, building GitHub PR branch
# Assumes https://github.com/tiiuae/ci-public build project being in use

source "setenvs.sh"

HYDRACTL="../hydractl/hydractl.py"
EXT_PORT=3030


SERVER="http://localhost:${EXT_PORT}/"
#export HYDRACTL_USERNAME="automation"

# TODO: All this should come from a configuration layer, and not be
#       hardcoded guesses of what is wanted
 # AP Setup project data ,-i project id, -D description
python3 "$HYDRACTL" "$SERVER" AP -i ghafCLI -D ghafCLI  

# JA Setup jobset data ,-p project, -i id, -D description , -t type, -f spec file
python3 "$HYDRACTL" \
        "$SERVER" AJ  \
        -p ghafCLI -i ghafCLI -D ghafCLI \
        -t flake -f git+https://github.com/tiiuae/ghaf/

python3 "$HYDRACTL" "$SERVER" AP -i ghaf-23-05-CLI -D "Ghaf project 23.05 CLI"

python3 "$HYDRACTL" \
        "$SERVER" AJ \
        -p ghaf-23-05-CLI -i ghaf -D "Ghaf project 23.05 CLI" \
        -t flake -f "git+https://github.com/tiiuae/ghaf/?ref=ghaf-23.05"

#TODO: -s state  one-shot
mnokka@gerrit:~/GIT_REPOT/c