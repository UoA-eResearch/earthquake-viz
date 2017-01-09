#!/usr/bin/env python

import sys
import time

inputs = sys.argv[1:]
matrix = {}

s = time.time()

for filename in inputs:
  with open(filename) as f:
    stats = {}
    while True:
      bits = f.readline().split()
      if len(bits) == 2:
        v = float(bits[1]) if '.' in bits[1] else int(bits[1])
        stats[bits[0]] = v
      else:
        break
    print(filename, stats)
    if 'dx' in stats:
      dx = stats['dx']
      dy = stats['dy']
    elif 'cellsize' in stats:
      dx = stats['cellsize']
      dy = stats['cellsize']
    for row in range(stats['nrows']):
      for col in range(stats['ncols']):
        lng = round((stats['xllcorner'] + dx * row), 2)
        lat = round((stats['yllcorner'] + dy * col), 2)
        if lng not in matrix:
          matrix[lng] = {}
        matrix[lng][lat] = bits[col]
      bits = f.readline().split()
  print("{} done, {}s elapsed".format(filename, time.time() - s))

with open('out.txt', 'w') as out:
  for lng in matrix:
    for lat in matrix[lng]:
      out.write("{}\t{}\t{}\n".format(lng, lat, elev))