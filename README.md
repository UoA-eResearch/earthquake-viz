# earthquake-viz

## Dependencies
* Blender 2.76b, , Python 3
* glob2: https://pypi.python.org/pypi/glob2
* joblib: https://pypi.python.org/pypi/joblib
* numpy & scipi: http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy (get from here on windows)
* Visual C++: http://www.microsoft.com/en-us/download/details.aspx?id=48145 (windows)

Run preprocess to convert simulation output files to interpolated surface deformations on a given DEM grid, e.g.:

python preprocess.py DEM.in input_dir output_dir

where DEM.in is the input DEM (format??), input_dir contains the files to be interpolated onto the DEM, output_dir will contain the interpolated results.



