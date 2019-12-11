# Contributing to OnSSET

## Deployment

OnSSET is automatically deployed to PyPI when a PEP440 valid version tag is pushed
to the master branch.

Running `git tag -a v1.0a1 -m "An alpha release"` followed by `git push --tags origin master`
will create a new alpha release tag and push it to the master branch.

Travis CI will then test, build and deploy the new release to PyPI.
