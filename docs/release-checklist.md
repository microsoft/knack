# Release Checklist

## A Maintainer's Guide to Releasing Knack

All releases will be of the form X.Y.Z where X is the major version number, Y is the minor version
number and Z is the patch release number. This project strictly follows
[semantic versioning](http://semver.org/) so following this step is critical.

Modify the version number in `setup.py` and create a pull request for the changes.

### Release with Azure DevOps (preferred option)

Once the changes have been merged to `dev`, create a tag on GitHub for that commit.
Follow the format of other releases in the release notes you create on GitHub.

Visit [Knack Release](https://dev.azure.com/azure-sdk/internal/_release?definitionId=83) to publish to PyPI.

### Release manually (backup option)

Once the changes have been merged to `dev`, continue with the rest of the release.

```
git clone https://github.com/microsoft/knack
cd knack
python setup.py sdist bdist_wheel
```

```
pip install twine
```

```
export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
export TWINE_USERNAME=A_USERNAME
export TWINE_PASSWORD=A_SECRET
twine upload dist/*
```
