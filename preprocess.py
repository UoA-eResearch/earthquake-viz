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
import multiprocessing
from joblib import Parallel, delayed


# read binary displacement data
def readBinary(fname):
    coords = []
    # data format is lon, lat, elevation
    # we will use lat, lon, elevation to be consistent with DEM
    nbytes = 4  # data is recorded as floats
    with open(fname, "rb") as f:
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


def interpolate(fname, dem_lat, dem_lon, output_dir, files):
    slice = readBinary(fname)

    # slice is sim results at each timestep
    # each slice has array of (lat, lon, elevation)
    # we want the simulation elevation at the dem lat, lon coords

    # size of data dimensions
    n_lat = len(dem_lat)
    n_lon = len(dem_lon)

    # record time taken to interpolate
    s = time.time()

    # the slice data is our function of (lat, lon)
    # define the lat and lon vectors and ndarrays
    lat, lon, elev = zip(*slice)
    lat = np.array(lat, dtype=np.float)
    lon = np.array(lon, dtype=np.float)
    elev = np.array(elev, dtype=np.float)

    # search for nearby points using k-nearest neighbour
    k = 9  # number of neighbours
    r = 1  # max distance of neighbourhood
    a = np.column_stack((lat, lon))  # format input array for tree
    tree = scipy.spatial.cKDTree(a.copy())  # init tree with copy of data
    disp = np.zeros((n_lat, n_lon))  # init output displacement matrix

    # find nearest neighbours for each DEM lat lon
    for i in range(n_lat)[:]:
        for j in range(n_lon)[:]:
            # print dem_lat[i], dem_lon[j]
            q = np.array([dem_lat[i], dem_lon[j]])  # query point
            n_d, n_idx = tree.query(q, k=k, eps=0, p=2,
                                    distance_upper_bound=r)  # query returns neighbour distances and indices
            disp[i][j] = 0
            # print d, idx
            wm = 0  # weighted mean
            count = 0
            # determine mean of weigthed contributions from neighbours
            for ni in range(len(n_idx)):
                if (np.isfinite(n_d[ni])):
                    count = count + 1
                    w = (r - n_d[ni]) / r
                    wm += w * elev[n_idx[ni]]  # weighted distace x elevation at neighbour
            if count > 0:
                disp[i][j] = wm / count  # average of weighted contributions

    disp = np.flipud(disp)

    e = time.time()
    print(os.path.basename(fname) + "    %.2f s" % (e - s))
    sys.stdout.flush()

    fname = "%s/disp_%d.csv" % (output_dir, files.index(fname))
    np.savetxt(fname, disp, delimiter=",")


def scale(d, n):
    return d * n


if __name__ == '__main__':
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
        # Bottom row in image is top row in data
        for i in range(0, n_lat):
            # flat row format
            o_elev = [float(x) for x in lines[3 + i].split()] + o_elev

    e = time.time()
    print("done %.2f s" % (e - s))

    # reshape data
    o_elev = np.array(o_elev)
    elev = o_elev.reshape((n_lat, n_lon))
    # Write out base map:
    np.savetxt("dem.csv", elev, delimiter=",")

    # read displacement data
    files = glob.glob(input_dir + "/*")
    files.sort()

    if (len(files) == 0):
        print("No input files found");
        sys.exit(1)

    # Map displacement data to DEM grid
    print("Interpolating data ...")
    sys.stdout.flush()

    num_cores = multiprocessing.cpu_count()
    Parallel(n_jobs=num_cores)(delayed(interpolate)(f, o_lat, o_lon, output_dir, files) for f in files)
