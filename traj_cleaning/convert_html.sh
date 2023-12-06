#!/bin/bash


DIRECTORY="/Users/guozhitong/Desktop/WebArena/z_human-trajectories/cleaned_htmls"

for html_file in "$DIRECTORY"/*.html; do
    python convert_webarena.py --directory "$html_file"
done