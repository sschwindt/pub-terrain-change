try:
    from qgis.core import *
    from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
except:
    print("ERROR: Cannot import qgis.core. Check interpreter and installation.")
import sys, os, logging
import numpy as np
import time
import gdal, gdalconst

print(os.path.abspath(os.path.abspath(os.path.dirname(sys.argv[0]))))
logging.basicConfig(filename='logfile.log', format='%(asctime)s %(message)s', level=logging.DEBUG)

QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.4/apps/Python37/', True)
qgs = QgsApplication([], False)
qgs.initQgis()


class QgsMaster:
    def __init__(self):
        self.dir_master = os.path.abspath(os.path.dirname(__file__)) + "/"
        self.no_data_value = -999.9
        self.reference = None
        self.reference_set = False
        self.reference_proj = str()
        self.reference_trans = tuple()
        self.band_ref = gdal.Band
        self.x_ref = int()
        self.y_ref = int()
        self.referencefile = 'empty'

    def align_raster(self, raster2align_path):
        gdal.AllRegister()
        logging.info(' *** -- aligning raster ... ')
        input = gdal.Open(raster2align_path, gdalconst.GA_ReadOnly)
        input_proj = input.GetProjection()

        try:
            if not self.reference_set:
                logging.info('        -- setting up reference raster ... ')
                self.set_reference_raster()
                logging.info('           > OK -- cooling down ... ')
                time.sleep(60)
        except:
            logging.info('WARNING: Could not set reference raster for alignment.')

        try:
            outputfile = raster2align_path.split('.tif')[0] + 'a.tif'  # Path to output file
        except:
            logging.info('WARNING: Invalid raster path for alignment: ' + str(raster2align_path))

        try:
            if os.path.exists(outputfile):
                try:
                    logging.info('        -- removing existing file (' + outputfile + ') ... ')
                    os.remove(outputfile)
                except:
                    logging.info('WARNING: Cannot write aligned output (' + outputfile + ' is locked).')
            logging.info('        -- set driver ...')
            driver = gdal.GetDriverByName('GTiff')
            driver.Register()
            output = driver.Create(outputfile, self.x_ref, self.y_ref, 1, self.band_ref.DataType)
            logging.info('        -- apply transformation ...')
            output.SetGeoTransform(self.reference_trans)
            logging.info('        -- apply projection ...')
            output.SetProjection(self.reference_proj)
            logging.info('        -- project image ..')
            gdal.ReprojectImage(input, output, input_proj, self.reference_proj, gdalconst.GRA_Bilinear)
            # dst_ds = driver.CreateCopy(destFile, output, 0)
            new_path = outputfile
            logging.info(' *** -- OK - aligned raster path: ' + new_path + '... cooling down ...')
            time.sleep(5)
        except:
            logging.info('ERROR: Alignment failed.')
            new_path = 'none'
        return new_path

    def calculate_raster(self, exp, output_ras, input_ras_dirs, dir_text_file):
        # raster calculator function for multi-layer-operations
        # exp = STR containing calculation expression
        # output_ras = STR of output Raster name
        # input_ras_dirs = LIST of calculator entries created with self.convert_to_calc_entry() function
        # dir_text_file = STR of a text file (full path) used where output Raster names will be logged

        logging.info(' *** -- expression: ' + exp)
        logging.info(' *** -- output target Raster: ' + str(output_ras))
        ras_lyrs = []
        entries = []
        for i in input_ras_dirs:
            lyr, ras = self.convert_to_calc_entry(i)
            ras_lyrs.append(ras)
            entries.append(lyr)
        try:
            if ras_lyrs[0].isValid():
                '''
                self.ras_lyrs[0].extent().width = self.output_size
                self.ras_lyrs[0].extent().height = self.output_size
                self.ras_lyrs[0].width= self.output_size
                self.ras_lyrs[0].height= self.output_size
                '''
                try:
                    logging.info(" *** -- calculating ... ")
                    calc = QgsRasterCalculator(exp, output_ras, 'GTiff', ras_lyrs[0].extent(), ras_lyrs[0].width(),
                                               ras_lyrs[0].height(), entries)
                    try:
                        logging.info(" *** -- " + str(calc.processCalculation()))
                    except:
                        print(calc.processCalculation())
                    logging.info(" *** -- calculation success (done).")
                except:
                    logging.warning("FAILED Raster Calculation.")
                    return -1
                if QgsRasterLayer(output_ras).isValid():
                    f = open(dir_text_file, 'a')
                    f.write(output_ras + "\n")
                    logging.info(" *** -- created Raster: " + output_ras + "\n")
                    f.close()
                else:
                    logging.warning("INVALID Output Raster: " + output_ras)
            else:
                try:
                    logging.warning("INVALID Raster: " + ras_lyrs[0].ref)
                except:
                    logging.warning("INVALID Raster.")
        except:
            logging.info("ERROR: Testing raster_layer.isValid() failed.")

    def convert_to_calc_entry(self, file_name):
        # Raster calculator entry type for using QgsRasterCalculator
        my_raster = QgsRasterLayer(file_name)
        my_layer = QgsRasterCalculatorEntry()
        my_layer.raster = my_raster
        my_layer.ref = file_name.split('/')[-1] + '@1'
        my_layer.bandNumber = 1
        return my_layer, my_raster

    def get_pixel_size(self, file_name):
        lyr, ras = self.convert_to_calc_entry(file_name)
        x = ras.rasterUnitsPerPixelX()
        y = ras.rasterUnitsPerPixelY()
        return x, y

    def raster2array(self, file_name, *nan_thresholds):
        # nan_threshold[0] = float number below which all raster values will be set to np.nan
        # nan_threshold[1] = float number above which all raster values will be set to np.nan

        file_name = self.align_raster(file_name)
        gdal.AllRegister()
        print('* screeninfo: processing ' + file_name)
        try:
            logging.info(" *** opening file " + str(file_name) + " ...")
            file = gdal.Open(file_name)
            ras = file.GetRasterBand(1)
        except:
            logging.info('WARNING: Could not open ' + str(file_name))
        try:
            logging.info(" *** converting Raster to Array ...")
            ras_array = ras.ReadAsArray()
        except:
            logging.info('WARNING: Could not convert raster to array.')

        # make non-relevant pixels np.nan
        logging.info(" *** normalizing Array (identify nan and apply sigmoid normalization) ...")
        try:
            ras_array = ras_array.astype(float)
        except:
            logging.info('WARNING: Could not convert array(raster) to floats --> error will likely occur.')

        ras_array[ras_array <= self.no_data_value] = np.nan
        try:
            ras_array[ras_array < nan_thresholds[0][0]] = np.nan
            ras_array[ras_array > nan_thresholds[0][1]] = np.nan
        except:
            pass
        ras_array[ras_array == 0] = np.nan

        array_dim = ras_array.shape
        for i in range(0, array_dim[0] - 1):
            for j in range(0, array_dim[1] - 1):
                if not (np.isnan(ras_array[i][j]) or np.round(ras_array[i][j], 1) == self.no_data_value or np.round(ras_array[i][j], 4) == 0.0000):
                    try:
                        ras_array[i][j] = 1 / (1 + np.exp(-ras_array[i][j]))
                    except:
                        ras_array[i][j] = np.nan
                else:
                    ras_array[i][j] = np.nan
                if ras_array[i][j] == 0:
                    ras_array[i][j] = np.nan

        logging.info("     Max array value: " + str(np.nanmax(ras_array)))
        logging.info("     Min array value: " + str(np.nanmin(ras_array)))
        logging.info(" *** calculating Array statistics ...")
        stats = ras.GetStatistics(0, 1)
        print('* processed * ' + str(file_name))

        return [ras_array, stats]

    def set_reference_raster(self, *ref_ras_name):
        # refras_name[0] = str(reference raster to use)
        logging.info(' *** -- setting reference raster ... ')
        try:
            self.referencefile = ref_ras_name[0]  # Path to reference file
        except:
            self.referencefile = self.dir_master + 'input/rasters/base_ras.tif'
        logging.info('        ref. name: ' + self.referencefile)
        try:
            print('*')  # do not delete -- print msg imposes a required variable evaluation break
            logging.info('        -- attempting to delete old reference ... ')
            self.reference = None
            print('* pace')  # do not delete -- print msg imposes a required variable evaluation break
            logging.info('        -- OK -- renewing reference ... ')
            self.reference = gdal.Open(self.referencefile, gdalconst.GA_ReadOnly)
            logging.info('        -- OK ')
        except:
            logging.info('WARNING: Cannot open reference raster.')
        try:
            logging.info('        -- reading reference projection ... ')
            self.reference_proj = self.reference.GetProjection()
            logging.info('        -- reading reference transformation ... ')
            self.reference_trans = self.reference.GetGeoTransform()
            logging.info('        -- reading reference band ... ')
            self.band_ref = self.reference.GetRasterBand(1)
            logging.info('        -- reading reference raster sizes (x and y) ... ')
            self.x_ref = self.reference.RasterXSize
            self.y_ref = self.reference.RasterYSize
            logging.info('        -- OK')
            self.reference_set = True
        except:
            logging.info('WARNING: Cannot access properties of reference raster.')
        logging.info(' *** -- OK (reference set) ')

    def __call__(self, *args, **kwargs):
        print('Class Info: <type> = QgsMaster (own class inheriting from qgis.core).')
