#!/bin/bash

for f in *.ui
do
    echo "Converting file $f"
    base=`basename $f .ui`
    pyuic4 --from-imports $f > "ui_"$base".py"
done