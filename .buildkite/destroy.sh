#!/bin/bash
set -euo pipefail

buildkite-agent artifact download package.zip .
buildkite-agent artifact download "terraform/*.json" terraform/

make tfdestroy
