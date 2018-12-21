#!/bin/bash

# Get the commit
COMMIT=$1

# Run through branches
git checkout 2.7-alpine && git cherry-pick $COMMIT && git push origin 2.7-alpine
git checkout 2.7-slim && git cherry-pick $COMMIT && git push origin 2.7-slim
git checkout 3.6-alpine && git cherry-pick $COMMIT && git push origin 3.6-alpine
git checkout 3.6-slim && git cherry-pick $COMMIT && git push origin 3.6-slim
git checkout 3.7-alpine && git cherry-pick $COMMIT && git push origin 3.7-alpine
git checkout 3.7-slim && git cherry-pick $COMMIT && git push origin 3.7-slim
git checkout master && git cherry-pick $COMMIT && git push origin master