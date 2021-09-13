#!/bin/bash
set -euo pipefail

make build

buildkite-agent artifact upload "package.zip"
