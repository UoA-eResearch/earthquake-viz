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

if len(argv) < 3:
  print('specify tslice, dem, texture')
  exit(1)

data_dir = argv[0].strip('/') + '/*'
dem_file = argv[1]
texture_path = argv[2]

f = open(dem_file)
lines = f.readlines()

basemap_scale = 0.000005
disp_scale = 0.1

first = [float(x) for x in lines[0].split()]
minlng = first[0]
maxlng = first[0]
minlat = first[1]
maxlat = first[1]

print('reading DEM')

dem = {}
for line in lines:
  bits = [float(x) for x in line.split()]
  if bits[0] not in dem:
    dem[bits[0]] = {}
  if bits[2] == -9999:
    bits[2] = 0
  dem[bits[0]][bits[1]] = bits[2]
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
n_lon = len(lngs)

latrange = range(int(minlat * 100), int(maxlat * 100))
latrange = [x/100.0 for x in latrange]
n_lat = len(latrange)

smoothed_dem = np.zeros((n_lon, n_lat))

for i,lng in enumerate(lngs):
  for j,lat in enumerate(latrange):
    if lng in dem and lat in dem[lng]:
      smoothed_dem[i][j] = dem[lng][lat]

smoothed_dem = gaussian_filter(smoothed_dem, sigma=2)


print("Longitude range: {} to {}. Latitude range: {} to {}. Longitude steps: {}. Latitude steps: {}.".format(minlng, maxlng, minlat, maxlat, n_lon, n_lat))

files = glob.glob(data_dir)
files.sort()
simulation = []

print('reading tslices')

for f in files[200:202]:
  c = readBinary(f)
  matrix = {}
  for lng, lat, elev in c:
    lng = round(lng, 2)
    lat = round(lat, 2)
    if lng not in matrix:
      matrix[lng] = {}
    matrix[lng][lat] = elev
  filled_matrix = np.zeros((n_lon, n_lat))
  for i,lng in enumerate(lngs):
    for j,lat in enumerate(latrange):
      if lng in matrix and lat in matrix[lng]:
        filled_matrix[i][j] = matrix[lng][lat]
  filled_matrix = gaussian_filter(filled_matrix, sigma=2)
  filled_matrix = list(filled_matrix.flatten())
  simulation.append(filled_matrix)

print('done')

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
    for j,lat in enumerate(latrange):
        normalised_x = (lng - minlng) / 10
        normalised_y = (lat - minlat) / 10
        vert = (normalised_x, normalised_y, smoothed_dem[i][j] * basemap_scale)
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
    k += 1
    obj.data.shape_keys.key_blocks[k].name = "Key_{k}".format(k=k)
    for i in range(0, n_lon):
        for j in range(0, n_lat):
            idx = j * n_lon + i
            bz = obj.data.shape_keys.key_blocks["Basis"].data[idx].co[2]
            dz = disp_scale * d[idx]
            obj.data.shape_keys.key_blocks[k].data[idx].co[2] = dz + bz

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