xivo-lib-python
=========
[![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=xivo-lib-python)](https://jenkins.wazo.community/job/xivo-lib-python)

xivo-lib-python is a common library used by various other services in Wazo


Running unit tests
------------------

```
apt-get install libpq-dev python-dev libffi-dev libyaml-dev python3.7-dev
pip install tox
tox --recreate -e py27,py34
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

