# Release Checklist

## A Maintainer's Guide to Releasing Knack

All releases will be of the form X.Y.Z where X is the major version number, Y is the minor version
number and Z is the patch release number. This project strictly follows
[semantic versioning](http://semver.org/) so following this step is critical.

Modify `HISTORY.rst` and the version number in `setup.py` and create a pull request for the changes.

### Release with Travis CI

Once the changes have been merged to master, create a tag on GitHub for that commit.

A Travis CI build will be kicked-off that will publish to PyPI.

### Release manually 

Once the changes have been merged to master, continue with the rest of the release.

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
