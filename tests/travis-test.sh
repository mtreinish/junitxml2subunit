#!/bin/bash
set -eo pipefail
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

pushd $parent_path > /dev/null
test-venv/bin/python -m subunit.run test_command | test-venv/bin/subunit-trace
popd > /dev/null
