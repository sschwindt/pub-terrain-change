import os
try:
    os.remove(os.path.abspath(os.path.dirname(__file__)) + "/logfile.log")
except:
    pass
try:
    from qgis.core import *
except:
    print("ERROR: Cannot import qgis.core. Check interpreter and installation.")

try:
    import numpy as np
    import cRoughness as cro  # old: draft2
    import cMorphoDynamic as cdyn  # old: uCalc
    import fGlobal as fun
    import time
except:
    print("ERROR: Cannot import own routines (cRoughness.py, cMorphoDynamic.py, fGlobal.py).")

# print(os.path.abspath(os.path.abspath(os.path.dirname(sys.argv[0]))))
try:
    import logging
    logging.basicConfig(filename='logfile.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
    logging.StreamHandler().setLevel(logging.DEBUG)
    logging.StreamHandler().setFormatter("%(asctime)s - %(message)s")
    logging.addLevelName(logging.INFO, '*INFO')
    logging.addLevelName(logging.WARNING, '!WARNING')
    logging.addLevelName(logging.ERROR, '!ERROR')
except:
    print("LOGGING ERROR: Could not load logging package. Check installation.")


def calculate_correlation(phi2dz_ras_list):
    corr_dir = 'D:/TerrainChangeResults/correlations/'
    re_sed = cdyn.SedimentDynamics(os.path.abspath(os.path.dirname(__file__)) + '/input/rasters/')
    [scour_fill, sf_stats] = re_sed.raster2array(os.path.abspath(os.path.dirname(__file__)) + '/input/rasters/scourfillneg.tif')
    try:
        _scour_fill_ = (scour_fill - np.nanmean(scour_fill)) / np.nanstd(scour_fill)
    except:
        logging.info('WARNING: Could not normalize scour_fill array.')
    try:
        _scour_fill_list_ = list(fun.flatten(_scour_fill_))
    except:
        logging.info('ERROR: Could not flatten (convert to list) scour_fill array.')
        return -1

    logging.info(' PREPARING TCD PER MORPH. UNIT RASTERS')
    mu_short_names = prepare_per_mu_analysis(re_sed)

    logging.info(' START CORRELATION OPERATIONS')

    mu_tcd_stats = {}
    re_sed_mu = cdyn.SedimentDynamics(os.path.abspath(os.path.dirname(__file__)) + '/input/rasters/')
    for p2z in phi2dz_ras_list:
        re_sed_phi = cdyn.SedimentDynamics(os.path.abspath(os.path.dirname(__file__)) + '/input/rasters/')
        for i in p2z:
            logging.info(' * CORRELATING scourfill (all terrain) WITH: ' + str(i))
            try:
                [output_arr, output_stats] = re_sed_phi.raster2array(i, [0.0, 10.0])  # 0/10.0 = lower/upper nan-thresholds for taux

                try:
                    _phi2dz_ = (output_arr - np.nanmean(output_arr)) / np.nanstd(output_arr)
                except:
                    logging.info('WARNING: Could not normalize phi2dz array.')

                try:
                    corr = fun.pearson_r(list(fun.flatten(_phi2dz_)), _scour_fill_list_)
                    if corr == np.nan:
                        logging.info('WARNING: Pearson r is nan.')
                except:
                    logging.info('WARNING: Failed to calculate global correlation coefficient.')
                    corr = np.nan
                logging.info(" -- calculated correlation: " + str(corr))
                try:
                    f = open(corr_dir + 'corr_dZx_' + str(i.split('/')[-1].split('.')[0]) + '_all.txt', 'a')
                    f.write('Correlation of:' + str(i) + "\nWith observed tcd (scour-fill):\n")
                    f.write(str(corr) + "\n\n")
                    f.write('File statistics [Min, Max, Mean, Stdev]: \n' + str(output_stats) + "\n")
                    f.close()
                    logging.info(" -- correlation matrix written to: " + corr_dir + 'corr_dZx_' + str(i.split('/')[-1].split('.')[0]) + '_all.txt')
                except:
                    logging.info('WARNING: could not write correlation matrix to textfile.')

                logging.info(' * CORRELATING scourfill (per morph. unit) WITH: ' + str(i))
                for mu in mu_short_names:
                    logging.info(' -- Morph. unit (short name): ' + str(mu))
                    try:
                        _phi2dz_mu_ = _phi2dz_  # create temp copy of original file
                        try:
                            # need to be reloaded because out-of-loop storage would explode RAM capacity
                            [mu_array, mu_stats] = re_sed_mu.raster2array(os.path.abspath(os.path.dirname(__file__)) +
                                                                          '/output/mu/' + mu + '.tif')
                        except:
                            logging.info('WARNING: Could not convert mu_tcd raster to array.')
                            continue
                        try:
                            mu_tcd_array = (mu_array - np.nanmean(mu_array)) / np.nanstd(mu_array)
                            _phi2dz_mu_[mu_tcd_array == np.nan] = np.nan
                        except:
                            logging.info('WARNING: Could not normalize mu_tcd array.')
                            mu_tcd_array = [np.nan]
                        mu_tcd_stats.update({mu: mu_stats})
                        try:
                            corr = fun.pearson_r(list(fun.flatten(_phi2dz_mu_)), list(fun.flatten(mu_tcd_array)))
                            if corr == np.nan:
                                logging.info('WARNING: Pearson r is nan.')
                        except:
                            logging.info('WARNING: Could not calculate correlation between normalized phi2dz and mu_tcd arrays.')
                            corr = np.nan

                        try:
                            logging.info('    * writing correlation matrix to ' + corr_dir + 'corr_dZx_' + str(i.split('/')[-1].split('.')[0]) + '_' + mu + '.txt')
                            f = open(corr_dir + 'corr_dZx_' + str(i.split('/')[-1].split('.')[0]) + '_' + mu + '.txt', 'a')
                            f.write('Correlation of:' + str(i) + "\nWith observed tcd (scour-fill):\n" + "Morph. Unit: " + mu)
                            f.write("\n" + str(corr) + "\n\n")
                            f.write('MU-tcd statistics [Min, Max, Mean, Stdev]: \n' + str(mu_tcd_stats[mu]) + "\n")
                            f.close()
                            logging.info(" -- correlation written to: " + corr_dir + 'corr_dZx_' + str(i.split('/')[-1].split('.')[0]) + '_' + mu + '.txt')
                            logging.info(" -- cooling down ...")
                            time.sleep(60)
                        except:
                            logging.info('WARNING: could not write correlation matrix to textfile.')
                    except:
                        logging.info('WARNING: Correlation operation of tcd_mu type \'' + str(mu) + '\' failed.')
            except:
                logging.info('ERROR: Shear / transport \'' + str(i) + '\' has no valid raster.')
    logging.info(' FINISHED CORRELATION OPERATIONS')


def calculate_hydraulics(roughness_laws, roughness, sediment_container):
    # roughness_laws = LIST of applicable roughness types included in roughness_dict
    # roughness = cRoughness.RoughnessLaw() object
    # sediment_container = cMorphoDynamic.SedimentDynamics() object
    qgs = launch_qgis()
    h_file = open("input/txt/flow_depth_list.txt", "r")
    u_file = open("input/txt/flow_velocity_list.txt", "r")

    h_list = h_file.read().splitlines()
    u_list = u_file.read().splitlines()
    hy_dict = dict(zip(h_list, u_list))

    roughness_dict = {"Bathurst": lambda go: roughness.Bathurst(),
                      "Drag1": lambda go: roughness.Drag1(), "Drag2": lambda go: roughness.Drag2(),
                      "Ferguson": lambda go: roughness.Ferguson(), "Hey": lambda go: roughness.Hey(),
                      "Keulegan": lambda go: roughness.Keulegan(), "MPM": lambda go: roughness.MPM(),
                      "ParkerA": lambda go: roughness.ParkerA(), "ParkerB": lambda go: roughness.ParkerB(),
                      "Smart": lambda go: roughness.Smart(), "Strickler": lambda go: roughness.Strickler()
                      }

    for rl in roughness_laws:
        logging.info(' APPLYING ROUGHNESS LAW: ' + str(rl).upper())
        logging.info(' -- Creating U-Ux Rasters ...')
        for flow_h in h_list:
            roughness.set_hy_rasters(flow_h, hy_dict[flow_h])
            try:
                logging.info(' --- Discharge: ' + str(int(roughness.label_q) * 100) + ' cfs')
            except:
                logging.warning('INVALID discharge code:  ' + str(roughness.label_q))
            try:
                roughness_dict[rl](1)
            except:
                logging.warning('ERROR: Could not calculate ' + str(roughness.label_q) + '(' + str(rl) + ')')

        logging.info(' -- Creating TAUx Rasters ...')

        # calculate dimensionless bed shear stress taux
        for i, j in zip(u_list, roughness.out_txts):
            sediment_container.make_taux_ras(i, j)
        roughness.reset_out_txt()

        logging.info(' -- Clearing uux (roughness) Rasters (required for disk space preservation) ...')
        fun.clean_dir(roughness.dir_out)
        fun.chk_dir(os.path.abspath(os.path.dirname(__file__)) + "/output/roughness/")
    qgs.exitQgis()


def calculate_phi(sediment_container, taux_raster_list):
    qgs = launch_qgis()
    for tx in taux_raster_list:
        sediment_container.make_phi2dz_mpm_ras(tx)
        sediment_container.make_phi2dz_rel_ras(tx)
    qgs.exitQgis()
    logging.info(' -- Clearing taux Rasters (required for disk space preservation) ...')
    fun.clean_dir(sediment_container.dir_out + 'taux/')


def clear_all(prefix, suffix, *args):
    # prefix = STR file start (can be empty, e.g., "", or include directory)
    # suffix = STR file ending, e.g., ".txt" or "_end.txt"
    # args = list of keywords between prefix and suffix
    for key_list in args:
        for kn in key_list:
            try:
                open(prefix + kn + suffix, 'w').close()
            except:
                pass


def prepare_per_mu_analysis(sediment_container):
    qgs = launch_qgis()
    mu_dict = {"agriplain": 4, "backswamp": 5, "bank": 6, "chute": 8, "cutbank": 9, "fast glide": 10,
               "flood runner": 11, "floodplain": 12, "high floodplain": 13, "hillside": 14, "bedrock": 14,
               "island high floodplain": 15, "island floodplain": 16, "lateral bar": 17, "levee": 18,
               "medial bar": 19, "mining pit": 20, "point bar": 21, "pond": 22, "pool": 23, "riffle": 24,
               "riffle transition": 25, "run": 26, "slackwater": 27, "slow glide": 28, "spur dike": 29,
               "swale": 30, "tailings": 31, "terrace": 32, "tributary channel": 33, "tributary delta": 34,
               "inchannel bar": 35}
    mu_short_names = []
    for mu in mu_dict.keys():
        logging.info(' * PREPARING Morph. Unit: ' + str(mu))
        mu_short_names.append(sediment_container.compare_phi_dod_per_mu(mu, mu_dict[mu]))
    qgs.exitQgis()
    return mu_short_names


def launch_qgis():
    logging.info(' * Instantiating QGIS application ... ')
    qgs = QgsApplication([], False)
    qgs.initQgis()
    logging.info(' * QGIS successfully launched.')
    return qgs


def main(roughness_laws):

    # roughness_laws = LIST of roughness laws
    own_dir = os.path.abspath(os.path.dirname(__file__)) + "/"
    input_raster_dir = own_dir + "input/rasters/"

    roughness = cro.RoughnessLaw(input_raster_dir)
    sediment = cdyn.SedimentDynamics(input_raster_dir)

    # relate discharges to durations (duration data from input/others/q_dur.txt - based on input/workbooks/MRY...xlsx)
    logging.info('LOADING FLOW FREQUENCY (duration) DATA ...')
    h_file = open("input/txt/flow_depth_list.txt", "r")
    q_labels = []
    [q_labels.append(item.split('/h')[-1]) for item in h_file.read().splitlines()]
    h_file.close()
    durations = []
    dd_file = open("input/txt/dis_dur_abs.txt", "r")
    [durations.append(item.split('\t')) for item in dd_file.read().splitlines()]
    dd_file.close()
    sediment.set_discharge_duration(q_labels, durations[0])
    logging.info(' * Done.')

    logging.info('STARTING CALCULATION OF HYDRAULIC RASTERS ...')
    calculate_hydraulics(roughness_laws, roughness, sediment)
    logging.info(' * Done.')

    logging.info('\n\nCALCULATING CORRELATION BETWEEN tau*(computed) and dZ/D84(tcd-observed)...')
    f_taux_info = open(sediment.dir_taux_txt, "r")
    taux_info = f_taux_info.read().splitlines()
    f_taux_info.close()
    del sediment
    # sediment = cdyn.SedimentDynamics(input_raster_dir)
    calculate_correlation(taux_info)
    logging.info(' * Done.')


def prepare_calculation(roughness_list):
    # verify output folder structure
    dir_corr_out = os.path.abspath(os.path.dirname(__file__)) + "/output/correlations/"
    fun.chk_dir(dir_corr_out)
    fun.chk_dir(os.path.abspath(os.path.dirname(__file__)) + "/output/phi2dz/")
    fun.chk_dir(os.path.abspath(os.path.dirname(__file__)) + "/output/roughness/")
    fun.chk_dir(os.path.abspath(os.path.dirname(__file__)) + "/output/taux/")
    clear_all(os.path.abspath(os.path.dirname(__file__)) + '/output/roughness/val_', '.txt', roughness_list)
    clear_all(os.path.abspath(os.path.dirname(__file__)) + '/output/phi2dz/val_', '.txt', ['phi_mpm', 'phi_rel'])
    clear_all(os.path.abspath(os.path.dirname(__file__)) + '/output/taux/val_', '.txt', ['taux'])
    clear_all(dir_corr_out, '.txt', [f for f in os.listdir(dir_corr_out) if
                                     os.path.isfile(os.path.join(dir_corr_out, f)) and f.split('.')[-1] == 'txt'])


if __name__ == '__main__':
    roughness_list = ['Bathurst', 'Ferguson', 'Hey', 'Drag1', 'Drag2', 'Keulegan', 'MPM', 'ParkerA', 'ParkerB', 'Smart',
                      'Strickler']
    prepare_calculation(roughness_list)
    main(roughness_list)



