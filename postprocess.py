#
# Converts data from preprocess.py into a Blender animation
#

import bpy
import sys
import numpy as np
import os
import time
from struct import *
import glob


def normalise(d):
    max = np.amax(d)
    min = np.amin(d)
    _range = max - min
    d = (d - min) / _range
    return d


def scale(d, n):
    return d * n

basemap_scale = 0.00005
disp_scale = 0.005

argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"

data_dir = os.path.abspath(argv[0])
csv_path = os.path.abspath(argv[1])
texture_path = os.path.abspath(argv[2])

print("Data directory: " + str(data_dir))
print("CSV file path: " + str(csv_path))
print("Texture file path: " + str(texture_path))
sys.stdout.flush()

# Clear Blender scene
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete(use_global=False)

for item in bpy.data.meshes:
    bpy.data.meshes.remove(item)

# Read basemap
basemap = np.loadtxt(csv_path, delimiter=",")

# Read in data
print("Reading displacement data..."),
sys.stdout.flush()
s = time.time()
files = glob.glob(data_dir + '/*')

# sort the files
files = sorted(files, key=lambda f: int(f.split('_')[1].split('.')[0]))

data = []
#for file in files[0:10]:
for file in files:
    d = np.loadtxt(file, delimiter=",")
    data.append(d)
e = time.time()
print("done %.2f s" % (e - s))
sys.stdout.flush()

# scale basemap
basemap = scale(basemap, basemap_scale)  # reduce exaggeration on DEM surface

# basemap properties
n_lat = basemap.shape[0]
n_lon = basemap.shape[1]

verts = []
faces = []
# Create vertices
for i in range(n_lat):
    for j in range(n_lon):
        vert = (i / n_lat, j / n_lon, basemap[i][j])
        verts.append(vert)

# Create faces
for i in range(0, n_lat - 1):
    for j in range(0, n_lon - 1):
        v0 = i * n_lon + j
        v1 = v0 + 1
        v2 = (i + 1) * n_lon + j + 1
        v3 = (i + 1) * n_lon + j
        face = (v0, v1, v2, v3)
        faces.append(face)

mesh_data = bpy.data.meshes.new("dem_mesh_data")
mesh_data.from_pydata(verts, [], faces[:])
mesh_data.update()  # (calc_edges=True) not needed here

dem_object = bpy.data.objects.new("DEM_Object", mesh_data)

scene = bpy.context.scene
scene.objects.link(dem_object)

bpy.ops.object.select_pattern(pattern='DEM_Object')
bpy.ops.object.duplicate()
cumulative = bpy.data.objects['DEM_Object.001']
cumulative.name = "Cumulative DEM_Object"
cumulative.location = (10, 0, 0)


# animation

nsteps = len(data)

print("Building shape keys ..."),
s = time.time()
sys.stdout.flush()
# generate a shape key for each simulation step
obj = dem_object
obj.shape_key_add()
cumulative.shape_key_add()
obj.data.shape_keys.key_blocks[0].name = "Basis"
cumulative.data.shape_keys.key_blocks[0].name = "Basis"

# displacement scale

for k in range(1, nsteps + 1):
    obj.shape_key_add()
    cumulative.shape_key_add()
    obj.data.shape_keys.key_blocks[k].name = "Key_{k}".format(k=k)
    cumulative.data.shape_keys.key_blocks[k].name = "Key_{k}".format(k=k)
    disp = data[k - 1]  # simulation timestep
    for i in range(0, disp.shape[0]):
        for j in range(0, disp.shape[1]):
            idx = i * n_lon + j
            bz = obj.data.shape_keys.key_blocks["Basis"].data[idx].co[2]
            dz = disp_scale * disp[i][j]
            obj.data.shape_keys.key_blocks[k].data[idx].co[2] = dz + bz
            prev = cumulative.data.shape_keys.key_blocks[k-1].data[idx].co[2]
            if bz + dz > prev:
              cumulative.data.shape_keys.key_blocks[k].data[idx].co[2] = dz + bz
            else:
              cumulative.data.shape_keys.key_blocks[k].data[idx].co[2] = prev

e = time.time()
print("done %.2f s" % (e - s))
sys.stdout.flush()

bpy.context.user_preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'

# create frames

stepsize = 1
for k in range(1, nsteps + 1):
    obj.data.shape_keys.key_blocks[k].value = 0.0
    obj.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize)
    obj.data.shape_keys.key_blocks[k].value = 1.0
    obj.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize + stepsize)
    obj.data.shape_keys.key_blocks[k].value = 0.0
    obj.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize + 2 * stepsize)
    
    cumulative.data.shape_keys.key_blocks[k].value = 0.0
    cumulative.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize)
    cumulative.data.shape_keys.key_blocks[k].value = 1.0
    cumulative.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize + stepsize)
    cumulative.data.shape_keys.key_blocks[k].value = 0.0
    cumulative.data.shape_keys.key_blocks[k].keyframe_insert(data_path='value', frame=k * stepsize + 2 * stepsize)

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
mtex.scale = (0.69, 0.65, 1.0)

# Add material to object
obj.data.materials.append(mat)
