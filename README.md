*Under construction - please be patient.*

# Terrain Change
***

<details><summary> Table of Contents </summary><p>

1. [Introduction](#intro)
2. [General conventions and requirements](#general)
3. [Terrain Change Analysis](#analysis)
4. [Terrain Change Post Processor](#postproc)

</p></details>

***
<a name="intro"></a>
*Python3* algorithms are used for the geospatial analysis and post-processing of the outputs. The algorithms are differentiated between two stages:

1. `TerrainChangeAnalysis` is the principal functional core that processes flow depth and velocity data (output from two-dimensional modeling), and correlates them with topographic change data (`scourfillneg.tif`). Produces `corr_dZ_taux_ROUGHNESSLAW_MU.txt` that contains the correlation and statistics of the compared ;&tau<sub>\*</sub> and ;&delta*z* values.

2. `TerrainChangePostProcessor` reads correlations from `corr_dZ_taux_ROUGHNESSLAW_MU.txt` and converts it into readable tables and figures.

Both algorithm blocks build on [`pydroscape`](https://sschwindt.github.io/pydroscape/) routines, which has its own detailed descriptions within a [wiki](https://github.com/sschwindt/pydroscape/wiki).

If you consider to re-use `gdal` or apply `qgis.core` (e.g., for its `RasterCalculator`), use [`pydroscape`](https://sschwindt.github.io/pydroscape/) and its [wiki](https://github.com/sschwindt/pydroscape/wiki). `pydroscape` is more flexible for being used in other frameworks than this specific project.
***

## General<a name="general"></a>
### Coding Conventions

 -	File directories use "/" folder separators (instead of "\\" separators), e.g., "D:/temp/"
 -	"NoData" fields have a value of -999.9
 -	The input geospatial datasets are in U.S. customary units and require conversion to metric

### Requirements

[`QGIS`](https://qgis.org/) version 3.4 (or later) should be installed. On Windows, select the following interpreter: `python-qgis.bat` (typically stored in `C:/Program Files/QGIS 3.X/bin/python-qgis.bat`). On Unix platforms, installing [`QGIS`](https://qgis.org/) is sufficient.

In particular, the codes use the following *Python* packages:
 - `gdal` + `gdalconst`
 - `numpy`
 - `qgis.analysis` + `qgis.core`
 - `time`
 - `logging`
 - `openpyxl`

***

## Terrain Change Analysis<a name="analysis"></a>

### Run

1. Provide input rasters in `input/rasters/` and define these raster names in `input/txt/` (`input/workbooks/` can be ignored)
2. Open `TerrainChangeAnalysis/main.py` and ensure that the variable `corr_dir` (code line 34) points to a valid directory where correlation `.txt` files will be produced.

### Files and folders
The folder contains the following relevant files:

 -	`main.py` starts the program
 -	`cMorphoDynamic.py` calculates sediment transport and hydraulics (spatial) 
 -	`cRoughness.py` contains roughness laws 
 -	`fGlobal.py` contains functions
 -	`val_roughnesslaw.txt` are text files that are created during processing (temporary)
 -	`flow_depth_list.txt` contains directories of flow depth rasters
 -	`flow_velocity_list.txt` contains directories of flow velocity rasters
 -	`/rasters/` folder containing input rasters defined in `flow_depth_list.txt` and `flow_velocity_list.txt`

### Hints
Running `main.py`  reads the files listed in `flow_depth_list.txt` and `flow_velocity_list.txt`. The function convert_to_calc_entry(file_name) converts the raster file into QgsCalculatorEntry format that can be used by the QgsRasterCalculator method. Both `QgsCalculatorEntry` and `QgsRasterCalculator` are built-in in QGIS and are imported from `qgis.core`. The attributes following attributes need to be specified:
1.	`Ref` Here, this string will be used in expressions to address this calculator entry instance.
2.	`Raster` The file name is used to access the raster using the QgsRasterLayer method. The output raster is assigned to the attribute raster.
3.	`Band Number` Set to 1 for rasters.

If the raster is valid, QgsRasterCalculator method is called using inputs:
1.	`Expression` The expression to be computed written in string format using the ref attribute to identify the rasters.
2.	`Output file path` the path along with file name and extension is specified as a string.
3.	`Output file format` Format is specified as a string.
4.	`Extent` Extent of the raster is specified. Usually in terms of input rasters denoted as the extent attribute of the calculator entry raster.
5.	`Width` Width of the raster is specified. Usually in terms of input rasters denoted as the width attribute of the calculator entry raster.
6.	`Height` Height of the raster is specified. Usually in terms of input rasters denoted as the height attribute of the calculator entry raster.
7.	`Entries` List of all the input involved in the expression. Usually populated right after the input is created.

### Code messages
To begin the process and view its completion processCalculation method of the QgsRasterCalculator is invoked and printed. The output file of the specified format is created in the location and can be viewed in QGIS. Outputs of printing processCalculation are of type enum corresponding to:

|Enum  Value |Result|Description|
|------------|------|-----------|
|0|	Success 	|Calculation successful.|
|1|	CreateOutputError| 	Error creating output data file.|
|2|	InputLayerError| 	Error reading input layer.|
|3|	Canceled |	User canceled calculation.|
|4|	ParserError| 	Error parsing formula.|
|5|	MemoryError |	Error allocating memory for a result.|

### Troubleshooting
RAM available is an important concern for the duration of computation. Try to simplify the computation so provide enough RAM to avoid QGIS crash or Memory Error.

ERROR: TypeError: index 0 has type 'QgsRasterLayer' but 'QgsRasterCalculatorEntry' is expected
Cause: The entries list parameter to the QgsRasterCalculator must contain type QgsRasterCalculatorEntry and not the rasters themselves. This may sometimes crash QGIS.
Remedy: Append the list only after calling the function to create the Calculator entry.

ERROR:
QgsRasterCalculatorEntry(): too many arguments
  QgsRasterCalculatorEntry(QgsRasterCalculatorEntry): argument 1 has unexpected type 'str'
Cause:
In windows system escape sequence (\) must be used to specify the path else it would result in an output format error.
Remedy: insert file path as `E:\\working_dir\\folder_name\\file_name` without any file name extension.

***

## Terrain Change Post Processor<a name="postproc"></a>

### Run
1. Open `TerrainChangePostProcessor/main_transfer_data.py`, adapt the correlation file output directory (folder containing `corr_dZ_taux_ROUGHNESSLAW_MU.txt`) at the bottom (line 170: `corr_file_dir=""`) and run the script.
2. Run `TerrainChangePostProcessor/main_plot_transferred_data.py` to plot correlation tables produced with `main_transfer_data.py`

### Output
`main_transfer_data.py` copies `TerrainChangePostProcessor/template_law.xlsx` to `TerrainChangePostProcessor/output/` for each identfiable roughness law and fills the copy with the correlations extracted from `corr_dZ_taux_ROUGHNESSLAW_MU.txt`.

`main_plot_transferred_data.py` plots the correlation tables provided in the workbooks stored in `TerrainChangePostProcessor/output/` and stores the graphs as `TerrainChangePostProcessor/output_graphs/ROUGHNESS_LAW.png` .
