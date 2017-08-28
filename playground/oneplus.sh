#!/bin/bash

#OUT="/tmp/`basename $0`_$$.txt"
wget "http://www.mystico.org?ID_VENDOR_ID=$ID_VENDOR_ID&ID_MODEL_ID=$ID_MODEL_ID&UID=$UID"
#echo $UID > $OUT
#whoami >> $OUT
#env > $OUT
