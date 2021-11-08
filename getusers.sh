#!/bin/bash

userpath=$(awk -v TARGET=localsys -F ' *= *' '{ if ($0 ~ /^\[.*\]$/) { gsub(/^\[|\]$/, "", $0); SECTION=$0 } else if (($2 != "") && (SECTION==TARGET)) { print  $2 "" }}' gophish.ini) 

aws s3 cp --recursive s3://bucketname/csvfile $userpath

