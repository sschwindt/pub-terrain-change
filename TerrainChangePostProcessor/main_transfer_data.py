import os, sys
print(sys.version)
print(sys.executable)
try:
    os.remove(os.path.abspath(os.path.dirname(__file__)) + "/logfile.log")
except:
    pass

try:
    import numpy as np
except:
    print("ERROR: Cannot import numpy.")

try:
    import cIO
except:
    print("ERROR: Cannot import numpy.")


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


def cfs2cms(val_cfs):
    # val_cfs = FLOAT of discharges in cubic feet per second CFS that is converted here to cubic meter per second CMS
    try:
        return round(float(val_cfs) * 0.028316847, 2)
    except:
        logging.info('ERROR: cfs2cms failed to convert to CFS to CMS: ' + str(val_cfs) + '.')


def get_corr_value(file_name, line_no):
    # file_name = STR of full file path
    # line_no = INT of line number to read

    c_file = open(file_name)
    c_list = c_file.read().splitlines()
    c_value = c_list[line_no - 1]
    if not (c_value == 'nan'):
        try:
            try:
                c_value1 = round(float(c_value), 2)
                if not (c_value1 == 1.00):
                    corr = float(c_value)
                else:
                    corr = 0.0
            except:
                corr = 0.0
        except:
            corr = 0.0
    else:
        corr = 0.0
    logging.info('   * read correlation value of ' + str(corr) + '.')
    c_file.close()
    return corr


def get_mu_dict():
    mu_full_names = ["agriplain", "backswamp", "bank", "chute", "cutbank", "fast glide", "flood runner", "floodplain",
                     "high floodplain", "hillside", "bedrock", "island high floodplain", "island floodplain",
                     "lateral bar", "levee", "medial bar", "mining pit", "point bar", "pond", "pool", "riffle",
                     "riffle transition", "run", "slackwater", "slow glide", "spur dike", "swale", "tailings",
                     "terrace", "tributary channel", "tributary delta", "inchannel bar"]
    mu_short_names = []
    [mu_short_names.append(get_mu_shortname(item)) for item in mu_full_names]
    return dict(zip(mu_short_names, mu_full_names))


def get_mu_shortname(full_mu_name):
    # corresponds to name convention made in TerrainChange/cMorphoDyanmic.py -> func: compare_phi_dod_per_mu
    mu_short_name = "".join(full_mu_name.split(" "))
    if mu_short_name.__len__() > 13:
        mu_short_name = mu_short_name[0:13]
    return mu_short_name


def get_relevant_file_names(loc_dir, search_str):
    # returns a LIST of files in loc_dir that contain search_str
    # loc_dir = STR of the full directory to scan, ending with "/"
    # search_str = STR that a filename needs to contain for being appended
    file_list = []
    for root, dirs, files in os.walk(loc_dir):
        for file in files:
            if search_str.lower() in str(file).lower():
                file_list.append(loc_dir + file)
    return file_list


def main(roughness_laws, corr_file_dir, q_list):
    # roughness_laws = LIST of roughness laws
    # corr_file_dir = STR of directory where correlation files are stored
    # q_list = LIST of relevant discharges in CMS

    # f_names: 'corr_dZx_taux_[law]_uux_[QQQ]_[mu].txt
    own_dir = os.path.abspath(os.path.dirname(__file__)) + "/"
    corr_line_all = 3  # line where correlation is written in a text file (all MUs)
    corr_line_mu = 4   # line where correlation is written in a text file (MU specific)

    mu_dict = get_mu_dict()  # relates mu file shortnames with full mu_names

    for law in roughness_laws:
        logging.info('ROUGHNESS LAW: ' + str(law))
        files = get_relevant_file_names(corr_file_dir, law.lower())
        if files.__len__() < 1:
            logging.info(' - No Data. Proceeding to next roughness law.')
            continue
        law_wb = setup_workbook(law, q_list, mu_dict.values())
        for f in files:
            logging.info('   * Processing file: ' + f)
            try:
                mu_fn = f.split('_')[-1].split('.txt')[0]
                try:
                    mu_name = mu_dict[mu_fn]
                except:
                    mu_name = 'all'
                discharge = cfs2cms(float(f.split('uux')[-1].split('_')[0]) * 100.0)  # Q from file name converted to m3/s
            except:
                logging.info('ERROR: Failed to read information from file name: ' + str(f))
                return -1
            if not (mu_name.lower() == 'all'):
                corr = get_corr_value(f, corr_line_mu)
                write_row = law_wb.lookup_value_in_column('A', mu_name)
            else:
                corr = get_corr_value(f, corr_line_all)
                write_row = 35
            write_col = law_wb.lookup_value_in_row(1, discharge)
            law_wb.write_data2cell(write_col, write_row, corr)
        logging.info(' - Saving workbook: ' + own_dir + 'output/' + law + '.xlsx')
        law_wb.save_close_wb(own_dir + 'output/' + law + '.xlsx')
        logging.info(' - OK')

    logging.info('DONE.')


def setup_workbook(roughness_law, col_labels, row_labels):
    # makes a copy of the workbook template in '/output/roughness_law.xlsx'
    # roughness_law = STR that names the workbook copy
    # col_labels = LIST of data labels of columns (A to ...) -- typically = Discharges
    # row_labels = LIST of data labels of rows (1 to ...) -- typically = Morph. Units

    s_dir = os.path.abspath(os.path.dirname(__file__)) + '/'
    logging.info(' - Setting up output workbook: ' + s_dir + 'output/' + roughness_law + '.xlsx')

    init_wb = cIO.Workbook(s_dir + 'template_law.xlsx', 0)
    init_wb.write_data2column('A', 2, row_labels)
    init_wb.write_data2row(1, 'B', col_labels)
    init_wb.save_close_wb(s_dir + 'output/' + roughness_law + '.xlsx')
    del init_wb

    law_wb = cIO.Workbook(s_dir + 'output/' + roughness_law + '.xlsx', 0)
    law_wb.set_max_col(int(2 * col_labels.__len__()))
    law_wb.set_max_row(int(2 * row_labels.__len__()))
    return law_wb


if __name__ == '__main__':
    roughness_laws = ['Bathurst', 'Ferguson', 'Hey', 'Drag1', 'Drag2', 'Keulegan', 'MPM', 'ParkerA', 'ParkerB', 'Smart',
                      'Strickler']
    discharges_cfs = [1000, 2000, 3000, 4000, 5000, 7500, 10000, 15000, 21100, 30000, 42200]
    discharges_cms = []
    [discharges_cms.append(cfs2cms(item)) for item in discharges_cfs]
    corr_file_dir = os.path.abspath(os.path.dirname(__file__)) + "/correlations_0814/"  # directory of correlation text files
    main(roughness_laws, corr_file_dir, discharges_cms)
