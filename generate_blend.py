import sys
import os
import bpy
import glob
import time
import numpy as np
from scipy.ndimage.filters import gaussian_filter
from struct import *

# read binary displacement data
def readBinary(fname):
    coords = []
    # data format is lon, lat, elevation
    nbytes = 4 * 3  # data is recorded as floats
    with open(fname, "rb") as f:
        byte = f.read(nbytes)
        while len(byte) > 0:
            # binary data is big-endian
            coords.append(unpack('>3f', byte))
            byte = f.read(nbytes)
    return coords

argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"

if len(argv) < 4:
  print('specify tslice, dem, texture, display type')
  exit(1)

data_dir = argv[0].strip('/') + '/*'
dem_file = argv[1]
texture_path = argv[2]
display_type = argv[3]

f = open(dem_file)
lines = f.readlines()

basemap_scale = 0.00002
disp_scale = 0.0125
vert_skip = 1
ts_skip = 3

first = [float(x) for x in lines[0].split()]
minlng = first[0]
maxlng = first[0]
minlat = first[1]
maxlat = first[1]

print('reading DEM')

dem = {}
lats = []

for line in lines:
  bits = [float(x) for x in line.split()]
  if bits[0] not in dem:
    dem[bits[0]] = {}
  if bits[1] not in lats:
    lats.append(bits[1])
  dem[bits[0]][bits[1]] = bits[2] * basemap_scale
  if bits[0] < minlng:
    minlng = bits[0]
  if bits[0] > maxlng:
    maxlng = bits[0]
  if bits[1] < minlat:
    minlat = bits[1]
  if bits[1] > maxlat:
    maxlat = bits[1]

lngs = list(dem.keys())
lngs.sort()
lats.sort()

lngs = lngs[::vert_skip]
lats = lats[::vert_skip]

n_lon = len(lngs)
n_lat = len(lats)

lng_lookup = dict((v,k) for k,v in enumerate(lngs))
lat_lookup = dict((v,k) for k,v in enumerate(lats))

smoothed_dem = np.zeros((n_lon, n_lat))

for i,lng in enumerate(lngs):
  for j,lat in enumerate(lats):
    if lng in dem and lat in dem[lng]:
      if dem[lng][lat] > 0:
        smoothed_dem[i][j] = dem[lng][lat]

smoothed_dem = gaussian_filter(smoothed_dem, sigma=2)


print("Longitude range: {} to {}. Latitude range: {} to {}. Longitude steps: {}. Latitude steps: {}.".format(minlng, maxlng, minlat, maxlat, n_lon, n_lat))

files = glob.glob(data_dir)
files.sort()
files = files[::ts_skip]
simulation = []

print('reading tslices')
s = time.time()
sys.stdout.flush()

for f in files:
  c = readBinary(f)
  matrix = np.zeros((n_lon, n_lat))
  for lng, lat, elev in c:
    lng = round(lng, 2)
    lat = round(lat, 2)
    if lng not in lng_lookup or lat not in lat_lookup:
      continue
    if lng in dem and lat in dem[lng] and dem[lng][lat] < 0:
      elev = 0
    i = lng_lookup[lng]
    j = lat_lookup[lat]
    matrix[i][j] = disp_scale * elev
  matrix = gaussian_filter(matrix, sigma=2)
  matrix += smoothed_dem
  matrix = list(matrix.flatten())
  if display_type == 'cumulative' and len(simulation) > 0:
    matrix = np.maximum(matrix, simulation[-1])
  simulation.append(matrix)

e = time.time()
print("done %.2f s" % (e - s))
sys.stdout.flush()

# Clear Blender scene
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete(use_global=False)

for item in bpy.data.meshes:
    bpy.data.meshes.remove(item)
    
verts = []
faces = []
# Create vertices
for i,lng in enumerate(lngs):
    for j,lat in enumerate(lats):
        normalised_x = (lng - minlng) / 10
        normalised_y = (lat - minlat) / 10
        vert = (normalised_x, normalised_y, smoothed_dem[i][j])
        verts.append(vert)

# Create faces
for i in range(0, n_lon - 1):
    for j in range(0, n_lat - 1):
        v0 = i * n_lat + j
        v1 = v0 + 1
        v2 = (i + 1) * n_lat + j + 1
        v3 = (i + 1) * n_lat + j
        face = (v0, v1, v2, v3)
        faces.append(face)
    

print('verts: {}. faces: {}. highest face: {}'.format(len(verts), len(faces), face))

mesh_data = bpy.data.meshes.new("dem_mesh_data")
mesh_data.from_pydata(verts, [], faces)
mesh_data.update()  # (calc_edges=True) not needed here

dem_object = bpy.data.objects.new("DEM_Object", mesh_data)

scene = bpy.context.scene
scene.objects.link(dem_object)

# animation

print("Building shape keys ..."),
s = time.time()
sys.stdout.flush()
# generate a shape key for each simulation step
obj = dem_object
obj.shape_key_add()

obj.data.shape_keys.key_blocks[0].name = "Basis"

# displacement scale

for k,d in enumerate(simulation):
    obj.shape_key_add()
    obj.data.shape_keys.key_blocks[k].name = "Key_{}".format(k+1)
    for i in range(0, n_lon):
        for j in range(0, n_lat):
            idx = j * n_lon + i
            dz = d[idx]
            obj.data.shape_keys.key_blocks[k].data[idx].co.z = dz

e = time.time()
print("done %.2f s" % (e - s))
sys.stdout.flush()

bpy.context.user_preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'

# create frames

stepsize = 1
for k in range(1, len(simulation) + 1):
    obj.data.shape_keys.key_blocks[k].value = 0.0
    obj.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize)
    obj.data.shape_keys.key_blocks[k].value = 1.0
    obj.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize + stepsize)
    obj.data.shape_keys.key_blocks[k].value = 0.0
    obj.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize + 2 * stepsize)


# Create material 

mat_name = "TextureMaterial"
mat = bpy.data.materials.new(mat_name)

mat.diffuse_color = (1.0, 1.0, 1.0)
mat.diffuse_shader = 'LAMBERT'
mat.diffuse_intensity = 0.8

mat.specular_color = (1.0, 1.0, 1.0)
mat.specular_intensity = 0.0

mat.emit = 0.75

# Add texture to material
img = bpy.data.images.load(texture_path)

mapTex = bpy.data.textures.new('MapTex', type='IMAGE')
mapTex.image = img

mtex = mat.texture_slots.add()
mtex.texture = mapTex
mtex.texture_coords = 'ORCO'
mtex.mapping = 'FLAT'
mtex.scale = (.56, .59, 1.0)

# Add material to object
dem_object.data.materials.append(mat)
