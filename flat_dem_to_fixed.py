import sys
import numpy as np

if len(sys.argv) < 2:
  print('specify infile')
  exit(1)

infile = sys.argv[1]
f = open(infile)
lines = f.readlines()

dem = {}
first = [float(x) for x in lines[0].split()]
minlng = first[0]
maxlng = first[0]
minlat = first[1]
maxlat = first[1]
for line in lines:
  bits = [float(x) for x in line.split()]
  if bits[1] not in dem:
    dem[bits[1]] = {}
  if bits[2] == -9999:
    bits[2] = 0
  dem[bits[1]][bits[0]] = bits[2]
  if bits[0] < minlng:
    minlng = bits[0]
  if bits[0] > maxlng:
    maxlng = bits[0]
  if bits[1] < minlat:
    minlat = bits[1]
  if bits[1] > maxlat:
    maxlat = bits[1]

# fill in DEM
lngrange = range(int(minlng * 100), int(maxlng * 100))
n_lng = len(lngrange)
n_lat = len(dem)

print(n_lat,n_lng)
lats = list(dem.keys())
lats.sort()

print(' '.join([str(x) for x in lats]))
print(' '.join([str(x/100.0) for x in lngrange]))
for lat in lats:
  elev = []
  for lng in lngrange:
    lng /= 100.0
    if lng in dem[lat]:
      elev.append(dem[lat][lng])
    else:
      elev.append(0)
  print(' '.join([str(x) for x in elev]))
