#!/bin/bash

# Get the commit
COMMIT=$1

# Check to push
PUSH_TO_ORIGIN=$2

# Iterate through each branch
for branch in $(git for-each-ref --format='%(refname:short)' refs/heads/); do

    # Prompt for cherry-picking
    read -p "Apply commit to $branch? " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        # Apply the commit
        echo -e "\nApplying $COMMIT to $branch...\n"
        git checkout "$branch" && git cherry-pick "$COMMIT"

        # Prompt for pushing
        read -p "Push $branch to origin? " -n 1 -r
        echo    # (optional) move to a new line
        if [[ $REPLY =~ ^[Yy]$ ]]
        then
            # Push to origin
            echo -e "\nPushing $branch to origin...\n"
            git push origin "$branch"
        fi
    fi

done