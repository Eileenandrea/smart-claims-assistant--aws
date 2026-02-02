#!/bin/bash
sam build && sam deploy --region ap-southeast-1 --resolve-s3 --capabilities CAPABILITY_IAM
