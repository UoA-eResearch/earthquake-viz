# earthquake-viz

Insert description here

## Windows setup
1. Download and install [Blender 2.76b 64bit](https://www.blender.org/download/).
1. Add the Blender install directory to your PATH.
1. Download and install [Python 3.4.2 64bit](https://www.python.org/download/releases/3.4.2/).
1. Add the Python install directory to your PATH.
1. Force Blender to use your system copy of Python by deleting Blender's python folder: `C:\Program Files\Blender Foundation\Blender\2.76\python`.
1. Install the glob2, joblib and pypng dependencies with the command: `pip install glob2 joblib pypng`.
1. To install numpy and scipy dependencies, first download the wheel files `numpy-1.10.4+mkl-cp34-none-win_amd64.whl`, `Pillow-3.1.0-cp34-none-win_amd64.whl` and `scipy-0.17.0-cp34-none-win_amd64.whl` from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).
1. Then, install numpy and scipy with the following command: `pip install numpy-1.10.4+mkl-cp34-none-win_amd64.whl Pillow-3.1.0-cp34-none-win_amd64.whl scipy-0.17.0-cp34-none-win_amd64.whl`.

## Ubuntu setup
1. 

##  Running

To convert simulation output files to interpolated surface deformations for a given DEM grid, run the following command:

```bash
python preprocess.py DEM.in input_dir output_dir
```
where DEM.in is the input DEM (format??), input_dir contains the files to be interpolated onto the DEM, output_dir will contain the interpolated results.

To generate the Blender animation, run the following command:

```bash
blender -P postprocess.py -- data_dir dem.csv texture.bmp
```

Where data_dir is the output from the preprocess, dem.csv is the ? and texture.bmp is the name of the texture file.
