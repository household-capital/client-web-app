#!/bin/bash
set -euo pipefail

buildkite-agent artifact download package.zip .

buildkite-agent artifact download "terraform/*.tfplan" terraform/ --step "${PLAN_STEP}"
buildkite-agent artifact download "terraform/.terraform.lock.hcl" terraform/ --step "${PLAN_STEP}"
buildkite-agent artifact download ".terraform.zip" . --step "${PLAN_STEP}"

unzip -q ./.terraform.zip -d ./terraform

make tfapply

buildkite-agent artifact upload "terraform/*.json"
