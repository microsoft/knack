Command Testing
===============

## Overview

There are two types of automated tests you can add. They are the [unit tests](https://en.wikipedia.org/wiki/Unit_testing) and the [integration tests](https://en.wikipedia.org/wiki/Integration_testing).

For unit tests, we support unit tests written in the forms of both standard [unittest](https://docs.python.org/3/library/unittest.html) and [nosetest](http://nose.readthedocs.io/en/latest/writing_tests.html).

For integration tests, we provide `ScenarioTest` to support [VCR.py](https://vcrpy.readthedocs.io/en/latest/) based replayable tests.

## About replayable tests

HTTP communication is captured and recorded, the integration tests can be replay in automation without a live testing environment.

We rely on [VCR.py](https://vcrpy.readthedocs.io/en/latest/) to record and replay HTTP communications. On top of the VCR.py, we build `ScenarioTest` to facilitate authoring tests.

## Authoring Scenario Tests

The `ScenarioTest` class is the preferred base class for and VCR based test cases from now on.

### Sample 1. Basic fixture
```Python
from knack.testsdk import ScenarioTest

class TestMyScenarios(ScenarioTest):
    def __init__(self, method_name):
        super(TestMyScenarios, self).__init__(mycli, method_name)

    def test_abc_list(self):
        self.cmd('abc list')
```
Note:

1. When the test is run without recording file, the test will be run under live mode. A recording file will be created at `recording/<test_method_name>.yaml`
2. Wrap the command in `self.cmd` method. It will assert the exit code of the command to be zero.
3. All the functions and classes your need for writing tests are included in `knack.testsdk` namespace. It is recommended __not__ to reference the sub-namespace to avoid breaking changes.

### Sample 2. Validate the return value in JSON

``` Python
class TestMyScenarios(ScenarioTest):
    def __init__(self, method_name):
        super(TestMyScenarios, self).__init__(mycli, method_name)

    def test_abc_list(self):
        result_list = self.cmd('abc list').get_output_in_json()
        assert len(result_list) > 0
```

Note:

1. The return value of `self.cmd` is an instance of class `ExecutionResult`. It has the exit code and stdout as its properties.
2. `get_output_in_json` deserialize the output to a JSON object

Tip:

1. Don't make any rigid assertions based on any assumptions which may not stand in a live test environment.


### Sample 3. Validate the return JSON value using JMESPath
``` Python
from knack.testsdk import ScenarioTest, JMESPathCheck
class TestMyScenarios(ScenarioTest):

    def __init__(self, method_name):
        super(TestMyScenarios, self).__init__(mycli, method_name)

    def test_abc_list(self):
        self.cmd('abc list', checks=[JMESPathCheck('length(@)', 26)])
```
Note:

1. What is JMESPath? [JMESPath is a query language for JSON](http://jmespath.site/main/)
2. If a command is return value in JSON, multiple JMESPath based check can be added to the checks list to validate the result.
3. In addition to the `JMESPatchCheck`, there are other checks list `NoneCheck` which validate the output is `None`. The check mechanism is extensible. Any callable accept `ExecutionResult` can act as a check.

## Recording Tests

### Record test for the first time

After the test is executed, a recording file will be generated at `recording/<test_name>.yaml`. The recording file will be created no matter the test pass or not. The behavior makes it easy for you to find issues when a test fails. If you make changes to the test, delete the recording and rerun the test, a new recording file will be regenerated.

It is a good practice to add a recording file to the local git cache, which makes it easy to diff the different versions of recording to detect issues or changes.

Once the recording file is generated, execute the test again. This time the test will run in playback mode. The execution is offline.

If the replay passes, you can commit the tests as well as recordings.

### Run test live

When the recording file is missing, the test framework will execute the test in live mode. You can force tests to be run live by set following environment variable:
```
export CLI_TEST_RUN_LIVE='True'
```

Also, you can author tests which are for live test only. Just derive the test class from `LiveTest`.

## Test Issues

Here are some common issues that occur when authoring tests that you should be aware of.

- **Non-deterministic results**: If you find that a test will pass on some playbacks but fail on others, there are a couple possible things to check:
  1. check if your command makes use of concurrency.
  2. check your parameter aliasing (particularly if it complains that a required parameter is missing that you know is there)
- **Paths**: When including paths in your tests as parameter values, always wrap them in double quotes. While this isn't necessary when running from the command line (depending on your shell environment), it will likely cause issues with the test framework.
