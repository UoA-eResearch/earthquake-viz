# earthquake-viz

Insert description here

## Ubuntu setup
1. Install linux dependencies: `sudo apt-get install blender python3-pip python3-numpy python3-scipy git`
1. Install Python 3 dependencies: `sudo pip3 install glob2 joblib pypng`
1. Clone repo into desired location: `git clone https://github.com/UoA-eResearch/earthquake-viz.git`

## Windows setup
1. Download and install [Blender 2.76b 64bit](https://www.blender.org/download/).
1. Add the Blender install directory to your PATH.
1. Download and install [Python 3.4.2 64bit](https://www.python.org/download/releases/3.4.2/).
1. Add the Python install directory to your PATH.
1. Force Blender to use your system copy of Python by deleting Blender's python folder: `C:\Program Files\Blender Foundation\Blender\2.76\python`.
1. Install the glob2, joblib and pypng dependencies with the command: `pip install glob2 joblib pypng`.
1. To install numpy and scipy dependencies, first download the wheel files `numpy-1.10.4+mkl-cp34-none-win_amd64.whl`, `Pillow-3.1.0-cp34-none-win_amd64.whl` and `scipy-0.17.0-cp34-none-win_amd64.whl` from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).
1. Then, install numpy and scipy with the following command: `pip install numpy-1.10.4+mkl-cp34-none-win_amd64.whl Pillow-3.1.0-cp34-none-win_amd64.whl scipy-0.17.0-cp34-none-win_amd64.whl`.
1. From a terminal clone repo into desired location (assuming you have git installed): `git clone https://github.com/UoA-eResearch/earthquake-viz.git`

##  Preprocessing

Your project directory should look like this:

```bash
user@pc:~/workspace/earthquake-viz$ ls
DEMSurface_4.in              input    postprocess.py  README.md
google_sat_3857_clipped.bmp  LICENSE  preprocess.py
```

In this case, the input files are in `~/workspace/earthquake-viz/input`:

```bash
jamie@jamie-VirtualBox:~/workspace/earthquake-viz/input$ ls
2010Dec26_m4pt7_pcmx_ts0000.0  2010Dec26_m4pt7_pcmx_ts0201.0
2010Dec26_m4pt7_pcmx_ts0001.0  2010Dec26_m4pt7_pcmx_ts0202.0
2010Dec26_m4pt7_pcmx_ts0002.0  2010Dec26_m4pt7_pcmx_ts0203.0
2010Dec26_m4pt7_pcmx_ts0003.0  2010Dec26_m4pt7_pcmx_ts0204.0
2010Dec26_m4pt7_pcmx_ts0004.0  2010Dec26_m4pt7_pcmx_ts0205.0 ...
```

Before running the preprocessor, make sure you have an output directory to save the output into ( `~/workspace/earthquake-viz/output`in our example above).

On Ubuntu, to convert the input files to interpolated surface deformations for a given DEM grid, run the following command:

```bash
user@pc:~/workspace/earthquake-viz$ python3 preprocess.py DEMSurface_4.in input output
Reading DEM basemap...
done 1.77 s
Interpolating data ...
2010Dec26_m4pt7_pcmx_ts0000.0    19.65 s
2010Dec26_m4pt7_pcmx_ts0001.0    19.23 s
2010Dec26_m4pt7_pcmx_ts0002.0    19.49 s
```

When running on Windows call `python` instead of `python3`:

```bash
C:\Users\User\workspace\earthquake-viz\> python preprocess.py DEMSurface_4.in input output
Reading DEM basemap...
done 1.77 s
Interpolating data ...
2010Dec26_m4pt7_pcmx_ts0000.0    19.65 s
2010Dec26_m4pt7_pcmx_ts0001.0    19.23 s
2010Dec26_m4pt7_pcmx_ts0002.0    19.49 s
```

Where DEM.in is the input DEMSurface_4.in (format??), input contains the files to be interpolated onto the DEM, output will contain the interpolated results.

##  Generating Blender animation

To generate the Blender animation, run the following command:

```bash
blender -P postprocess.py -- data_dir dem.csv texture.bmp
```

Where data_dir is the output from the preprocess, dem.csv is the ? and texture.bmp is the name of the texture file.
