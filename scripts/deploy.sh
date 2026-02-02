#!/bin/bash
sam build && sam deploy --resolve-s3 --capabilities CAPABILITY_IAM
