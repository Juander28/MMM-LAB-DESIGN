#!/bin/bash
set -e
cd "$(dirname "$0")"
xschem -n -q -x -o . -N cross_coupled_x10.spice cross_coupled_x10.sch
ngspice -b cross_coupled_x10.spice
python3 analyze_notch.py x10_ac.csv
