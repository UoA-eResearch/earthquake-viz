#!/bin/bash
for i in {0..250};do
  m=$(expr $i / 60)
  s=$(printf "%02d" $(expr $i % 60))
  convert -background lightgray -fill black -size 600x100 -gravity center label:"Rupture time $m:$s" timer/$i.png
done
