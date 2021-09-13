#!/bin/bash
set -euo pipefail

buildkite-agent artifact download package.zip .

make tfplan

buildkite-agent artifact upload "terraform/*.tfplan"
buildkite-agent artifact upload "terraform/.terraform.lock.hcl"

cd ./terraform
zip -q -dc -r ../.terraform.zip .terraform/
cd ..

buildkite-agent artifact upload ".terraform.zip"
