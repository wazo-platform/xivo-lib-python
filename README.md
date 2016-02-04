xivo-lib-python
=========
[![Build Status](https://travis-ci.org/xivo-pbx/xivo-lib-python.png?branch=master)](https://travis-ci.org/xivo-pbx/xivo-lib-python)

xivo-lib-python is a common library used by various other services in XiVO


Running unit tests
------------------

```
apt-get install libpq-dev python-dev libffi-dev libyaml-dev
pip install tox
tox --recreate -e py27
```


Running integration tests
-------------------------

You need Docker installed.

```
cd integration_tests
pip install -U -r test-requirements.txt
make test-setup
make test
```
