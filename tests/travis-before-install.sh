#!/bin/bash

set -eo pipefail

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

pushd $parent_path > /dev/null
virtualenv test-venv

source test-venv/bin/activate
pip install -U pip setuptools
pip install -U testtools python-subunit os-testr stestr
popd > /dev/null
