#!/bin/bash
set -euo pipefail

buildkite-agent artifact download package.zip .

make deploy

buildkite-agent artifact upload "terraform/*.json"
