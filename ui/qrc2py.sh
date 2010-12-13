#!/bin/bash

for f in resources/*.qrc
do
    echo "Converting file $f"
    base=`basename $f .qrc`
    pyrcc4 -py3 $f > $base"_rc.py"
done