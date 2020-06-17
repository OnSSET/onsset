# Contributing to OnSSET

There are many ways in which you can contribute to OnSSET.

For example, here are a list of ways you could help out:
- Ask a question by creating a [new issue](https://github.com/OnSSET/onsset/issues/new/choose)
- Connecting potential users of the tool with OnSSET
- Development of [new functionality](https://github.com/OnSSET/onsset/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)
- Organising [issues & bug reports](https://github.com/OnSSET/onsset/issues)
  and helping with [project management](https://github.com/OnSSET/onsset/projects)
- Coordinating student studies which use OnSSET
- Collaboration on electrification research and sharing results
- Helping to develop [training material](https://github.com/OnSSET/teaching_kit)
- Answering [questions](https://github.com/OnSSET/onsset/labels/question) and discussing issues for other users
- Recording instructional videos for the [training material](https://github.com/OnSSET/teaching_kit)
- Develop the [wiki](https://github.com/OnSSET/onsset/wiki)
  and [documentation](https://onsset.readthedocs.io/en/latest/?badge=latest) to answer frequently answered questions


## Deployment

OnSSET is automatically deployed to PyPI when a [PEP440](https://www.python.org/dev/peps/pep-0440/)
valid version tag is pushed to the master branch.

Running `git tag -a v1.0a1 -m "An alpha release"` followed by `git push --tags origin master`
will create a new alpha release tag and push it to the master branch.

Travis CI will then test, build and deploy the new release to PyPI.
