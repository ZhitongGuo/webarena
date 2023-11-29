#!/bin/bash
#SBATCH --job-name=mind2web
#SBATCH --output=mind2web.out
#SBATCH --error=mind2web.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=5:00:00

python oracle_mind2web.py

