import os, sys
print(sys.version)
print(sys.executable)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
try:
    os.remove(os.path.abspath(os.path.dirname(__file__)) + '/logfile.log')
except:
    pass

try:
    import cIO
    import cPlotter as cpy
except:
    print('ERROR: Cannot import own packages.')

# print(os.path.abspath(os.path.abspath(os.path.dirname(sys.argv[0]))))
try:
    import logging
    logging.basicConfig(filename='logfile.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
    logging.StreamHandler().setLevel(logging.DEBUG)
    logging.StreamHandler().setFormatter('%(asctime)s - %(message)s')
    logging.addLevelName(logging.INFO, '*INFO')
    logging.addLevelName(logging.WARNING, '!WARNING')
    logging.addLevelName(logging.ERROR, '!ERROR')
except:
    print('LOGGING ERROR: Could not load logging package. Check installation.')


def get_xlsx_file_names(loc_dir):
    # returns a LIST of files in loc_dir that contain search_str
    # loc_dir = STR of the full directory to scan, ending with '/'
    # search_str = STR that a filename needs to contain for being appended
    file_list = []
    for root, dirs, files in os.walk(loc_dir):
        for file in files:
            if 'xlsx' in str(file).lower():
                file_list.append(loc_dir + file)
    return file_list


def main(file_dir):
    # file_dir = STR of directory where XLSX workbooks with 2D plot data are stored

    # f_names: 'corr_dZx_taux_[law]_uux_[QQQ]_[mu].txt
    own_dir = os.path.abspath(os.path.dirname(__file__)) + '/'
    files = get_xlsx_file_names(file_dir)
    if files.__len__() < 1:
        logging.info('No Data. Run main_transfer_data.py first.')
        return -1
    for f in files:
        try:
            logging.info('PROCESSING: ' + str(f))
            data_wb = cIO.Workbook(f, 0)
            logging.info(' - Reading data ...')
            _q_ = data_wb.read_row_str(1, 'B') # corresponds to x-data
            labels_mu = data_wb.read_column('A', 2) # corresponds to y-data

            corr_data = data_wb.read_matrix('B', 2) # corresponds to Z-data
            logging.info(' - Creating plot ...')
            surf_plot = cpy.Plotter()
            surf_plot.width = 6.0
            surf_plot.height = 10.0
            surf_plot.font_size = 11.0
            surf_plot.legend_active = True
            surf_plot.colorbar_aspect = 20
            surf_plot.colorbar_shrink = 0.93
            surf_plot.y_label = 'Morphological Units'
            surf_plot.save_fig_dir = own_dir + 'output_graphs/' + str(f.split('/')[-1].split('.')[0]) + '.png'
            
            labels_q = []
            for labs in _q_:
                labels_q.append(str(labs) + ' m³/s')

            surf_plot.colorbar_min_val = -1
            surf_plot.colobar_label = 'Pearson r [--]'
            surf_plot.color_map_type = 'RdYlGn'
            
            logging.info(' - Producing figure ... ')
            surf_plot.make_heatmap(corr_data, labels_q, labels_mu)
            
            try:
                data_wb.close()
            except:
                del data_wb
            logging.info(' - OK')
        except:
            logging.info('WARNING: A problem occurred. Check previous ERROR and/or WARNING messages.')

    logging.info('FINISHED.')


if __name__ == '__main__':
    file_dir = os.path.abspath(os.path.dirname(__file__)) + '/output/'  # directory of correlation text files
    main(file_dir)

