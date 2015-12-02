#
# Run this to produce matrices (lat, lon, elev)
# 
#
import sys
import numpy as np
import scipy as sp
import scipy.ndimage
import scipy.interpolate
import os
import time
from struct import *
import glob
import png
from scipy.spatial import cKDTree

def toPNG(disp, filename):
	# filter first
	#disp = sp.ndimage.filters.gaussian_filter(disp, sigma=2)	
	max = np.amax(disp)
	min = np.amin(disp)
	r = max - min
	disp = ((disp - min) / r ) * (2**16-1)
	disp = disp.astype(int)
	disp = np.flipud(disp)
	width = disp.shape[1]
	height = disp.shape[0]
	disp = disp.flatten('C')
	writer = png.Writer(width=width, height=height, bitdepth=16, greyscale=True )
	writer.write_array(open(filename, "wb"), disp)


# read binary displacement data
def readBinary(fname):
	coords = []
	# data format is lon, lat, elevation
	# we will use lat, lon, elevation to be consistent with DEM
	nbytes = 4 # data is recorded as floats
	with open(fname, "rb") as f:
		print(fname)
		sys.stdout.flush()
		
		byte = f.read(nbytes)
		while len(byte) > 0:
			# binary data is big-endian
			lat = unpack('>f', byte)[0] 
			byte = f.read(nbytes)
			lon = unpack('>f', byte)[0]
			byte = f.read(nbytes)
			elev = unpack('>f', byte)[0] 
			coords.append((lon, lat, elev))
			byte = f.read(nbytes)
	return coords
		
def interpolate(slices, dem_lat, dem_lon):
	# slices is array of sim results at each timestep
	# each slice has (lat, lon, elevation)
	# we want the simulation elevation at the dem lat, lon coords

	disps = [] # list of output displacement matrices
	n_lat = len(dem_lat)
	n_lon = len(dem_lon)	
	for slice in slices:
		# the slice data is our function of (lat, lon)
		# define the lat and lon vectors and ndarrays
		lat, lon, elev = zip(*slice)
		lat = np.array(lat, dtype=np.float)
		lon = np.array(lon, dtype=np.float)
		elev = np.array(elev, dtype=np.float)	

		# k-nearest neighbour
		k = 10 	# number of neighbours
		r = 1	# max distance of neighbour
		a = np.column_stack((lat, lon)) # format input array for tree
		tree = scipy.spatial.cKDTree(a.copy()) # intit tree with copy of data
		disp = np.zeros((n_lat, n_lon)) # init output displacement matrix

		# find nearest neighbours for each dem lat lon
		for i in range(n_lat)[:]:
			for j in range(n_lon)[:]:
				#print dem_lat[i], dem_lon[j]
				q = np.array([dem_lat[i], dem_lon[j]]) # query point
				d, idx = tree.query(q, k=k, eps=0, p=2, distance_upper_bound=r) # query returns neighbour distances and indices
				disp[i][j] = 0
				#print d, idx
				wm = 0 # weighted mean
				count = 0
				# determine mean of weigthed contributions from neighbours
				for w in range(len(idx)):
					if (np.isfinite(d[w])):
						count = count + 1
						wm += ( (r-d[w])/r ) * slice[idx[w]][2]
				if count > 0:
					disp[i][j] = wm/count
					
		disp = np.flipud(disp)
		disps.append(disp)

	return disps

def normalise(d):
	max = np.amax(d)
	min = np.amin(d)
	_range = max - min
	d = (d - min) / _range
	return d

def scale(d, n):
	return d * n

# input and output files
in_file = sys.argv[1]
input_dir = os.path.abspath(sys.argv[2])
output_dir = os.path.abspath(sys.argv[3])

print("Reading DEM basemap..."),
s = time.time()

# Open and read .in file
o_lat = []
o_lon = []
o_elev = []
with open(in_file, "r") as file:
	# read lines
	lines = file.readlines()
	# determine number of latitude and longitude points
	n_lat, n_lon = lines[0].split()
	n_lat = int(n_lat)
	n_lon = int(n_lon)
	# read latitude values
	o_lat = [float(x) for x in lines[1].split()]
	# read longitude values
	o_lon = [float(x) for x in lines[2].split()]
	# read lat, long grid
	o_elev = []
	# Bottom row in image is top row in data
	for i in range(0, n_lat):
		# flat row format
		o_elev = [float(x) for x in lines[3+i].split()] + o_elev

e = time.time()
print("done %.2f s" % (e - s))

# normalise data
lat = normalise(np.array(o_lat))
lon = normalise(np.array(o_lon))
elev = normalise(np.array(o_elev))

# scale data
#lat = scale(lat, 1)
#lon = scale(lon, 1)
#elev = scale(elev, 0.1) # reduce exaggeration on DEM surface

# reshape data
elev = elev.reshape((n_lat, n_lon))

# read distrubance data 
# TODO replace with list of time slices

files = []
for file in glob.glob(input_dir + "/*"):
	files.append(os.path.abspath(file))

slices = []
print("Reading displacement data..."),
s = time.time()
#for file in files:
for file in [files[100]]:
	#print(file)
	slices.append(readBinary(file))
e = time.time()
print("done %.2f s" % (e - s))

# Map displacement data to DEM grid
print("Interpolating data...")
sys.stdout.flush()

s = time.time()
disps = interpolate(slices, o_lat, o_lon)
e = time.time()
print("done %.2f s" % (e - s))
sys.stdout.flush()

# Write out base map:
np.savetxt("dem.csv", elev, delimiter=",")

# Write out slices
for i in range(0, len(disps)):
	d = disps[i]
	fname = "%s/disp_%d.csv" % (output_dir, i)
	np.savetxt(fname, d, delimiter=",")

