#!/bin/bash
# Regenera el netlist desde el esquematico y simula con ngspice
set -e
cd "$(dirname "$0")"
xschem -n -q -x -o . -N cross_coupled_test1.spice cross_coupled_test1.sch
ngspice -b cross_coupled_test1.spice
python3 analyze_notch.py test1_ac.csv
