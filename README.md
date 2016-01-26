# earthquake-viz

## Dependencies
* Blender 2.76b, , 
* glob2: https://pypi.python.org/pypi/glob2
* joblib: https://pypi.python.org/pypi/joblib
* Python 3, numpy & scipi: anaconda (need to change to same Python version as Blender - with conda command): 
* conda install python=3.4.2=0 (need exact build number) 

* pypng

Run preprocess to convert simulation output files to interpolated surface deformations on a given DEM grid, e.g.:

python preprocess.py DEM.in input_dir output_dir

where DEM.in is the input DEM (format??), input_dir contains the files to be interpolated onto the DEM, output_dir will contain the interpolated results.

add blender to path (if on Windows)
remove Python folder within BLender install (so uses system Python)

blender -b -P blendtest.py
