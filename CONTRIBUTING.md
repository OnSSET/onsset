# Contributing to OnSSET

There are many ways in which you can contribute to OnSSET.

For example, here are a list of ways you could help out:
- Connecting potential users of the tool with OnSSET
- Development of new functionality
- Organising issues, bug reports and project management
- Coordinating student studies which use OnSSET
- Collaboration and sharing results
- Developing training material
- Answering questions and discussing issues for other users
- Recording instructional videos
- Develop the wiki and documentation to answer frequently answered questions


## Deployment

OnSSET is automatically deployed to PyPI when a [PEP440](https://www.python.org/dev/peps/pep-0440/)
valid version tag is pushed to the master branch.

Running `git tag -a v1.0a1 -m "An alpha release"` followed by `git push --tags origin master`
will create a new alpha release tag and push it to the master branch.

Travis CI will then test, build and deploy the new release to PyPI.
