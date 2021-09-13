#!/bin/bash
ENV=$1
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
ID=${ENV}-deploy-snapshot-$TIMESTAMP
echo Creating ${ID}...
echo "CREATING SNAPSHOT - ${ID}"
aws --region ap-southeast-2 rds create-db-snapshot --db-instance-identifier clientapp-db-${ENV} --db-snapshot-identifier $ID
echo "WAITING FOR SNAPSHOT AVAILABILITY"
aws --region ap-southeast-2 rds wait db-snapshot-available --db-snapshot-identifier ${ID}
echo "COMPLETED"