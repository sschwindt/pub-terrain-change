import os, logging
from cQgs import QgsMaster

logging.basicConfig(filename='logfile.log', format='%(asctime)s %(message)s', level=logging.DEBUG)


class SedimentDynamics(QgsMaster):
    def __init__(self, raster_dir):
        QgsMaster.__init__(self)

        self.cell_size_x = float
        self.cell_size_y = float
        self.dict_q_dur = {}

        self.dir_out = os.path.abspath(os.path.dirname(__file__)) + "/output/"
        self.dir_phi_mpm_txt = self.dir_out + "phi2dz/val_phi_mpm.txt"
        self.dir_phi_rel_txt = self.dir_out + "phi2dz/val_phi_rel.txt"
        self.dir_mu_txt = self.dir_out + "mu/val_mu.txt"
        self.dir_taux_txt = self.dir_out + "taux/val_taux.txt"
        self.dir_tcd = raster_dir + 'scourfillneg.tif'  # default can be changed with self.set_tcd_dirs function
        self.dir_dmean = raster_dir + 'dmean'
        self.dir_mu = raster_dir + 'mu.tif'

        self.g = 32.174  # (ft/s^2) gravity acceleration constant

        self.ref_dmean = self.dir_dmean.split('/')[-1] + '@1'
        self.ref_mu = self.dir_mu.split('/')[-1] + '@1'
        self.ref_tcd = self.dir_tcd.split('/')[-1] + '@1'  # default can be changed with self.set_tcd_dirs function

    def compare_phi_dod_per_mu(self, mu_name, mu_number):
        mu_short_name = "".join(mu_name.split(" "))
        if mu_short_name.__len__() > 13:
            logging.info(" *** using shortname: " + mu_short_name)
            mu_short_name = mu_short_name[0:13]
        if not os.path.isfile(self.dir_out + 'mu/' + mu_short_name + '.tif'):
            # make mu extraction only if not yet done
            logging.info(" *** creating mu-tcd raster: .../output/mu/" + mu_short_name + ".tif")
            self.make_mu_single_ras(mu_short_name, mu_number)
        else:
            logging.info(" *** mu-tcd raster already exists (omitting): .../output/mu/" + mu_short_name + ".tif")

        return mu_short_name

    def make_mu_single_ras(self, mu_short_name, mu_number):
        expression = '("' + self.ref_mu + '"=' + str(
            mu_number) + ') * ("' + self.ref_tcd + '" * 2.2 * "' + self.ref_dmean + '"/304.7992) + ' + '("' + self.ref_mu + '"!=' + str(
            mu_number) + ') * ' + str(self.no_data_value)
        output_ras = self.dir_out + 'mu/' + mu_short_name + '.tif'
        logging.info(" *** extracting MU-type " + mu_short_name + " (saving as own Raster).")
        self.calculate_raster(expression, output_ras, [self.dir_mu, self.dir_tcd, self.dir_dmean], self.dir_mu_txt)

    def make_phi2dz_mpm_ras(self, dir_taux_ras, a=str(4.93), b=str(1), c=str(1.6)):
        # phi classic computation: a*(b*T - Tcr)^c
        tau_ref = dir_taux_ras.split('/')[-1] + '@1'
        self.set_exp_phi2dz(dir_taux_ras.split('uux')[-1].split('.tif')[0])
        phi = a + '*(("' + tau_ref + '"-0.047)^' + c + ')'
        expression = phi + ' 1.0'
        output_file = self.dir_out + "phi2dz/dz_mpm_" + dir_taux_ras.split('uux')[-1]
        logging.info(" *** calculating phi2dz (MPM) for " + dir_taux_ras + ".")
        try:
            self.calculate_raster(expression, output_file, [dir_taux_ras], self.dir_phi_mpm_txt)
        except:
            logging.info("ERROR: Raster calculation failed (possible reason: no valid pixels in input / output rasters).")

    def make_phi2dz_rel_ras(self, dir_taux_ras, d=str(14), e=str(2.45), f=str(10)):
        # phi relative computation:{d*(T^c/(1+(Tcr/T*)^f)}
        tau_ref = dir_taux_ras.split('/')[-1] + '@1'
        self.set_exp_phi2dz(dir_taux_ras.split('uux')[-1].split('.tif')[0])
        phi = '(' + d + '*("' + tau_ref + '"^' + e + '))/(1+(0.047/' + tau_ref + ')^' + f + ')'
        expression = phi + '* 1.0'
        output_file = self.dir_out + "phi2dz/dz_rel_" + dir_taux_ras.split('uux')[-1]
        logging.info(" *** calculating phi2dz (REL) for " + dir_taux_ras + ".")
        self.calculate_raster(expression, output_file, [dir_taux_ras, dir_taux_ras], self.dir_phi_rel_txt)

    def make_taux_ras(self, dir_u_ras, dir_uux_ras):
        # Tau computation:{ux^2/(g*(s-1)*D84)}
        # uses g = 32.174, (s-1) = 1.68, D84 = 2.2*self.ref_dmean/304.7992
        #    32.174*1.68*2.2/304.7992 = 0.3901
        ref_u = dir_u_ras.split('/')[-1] + '@1'
        ref_uux = dir_uux_ras.split('/')[-1] + '@1'
        expression = '(("' + ref_u + '"/"' + ref_uux + '")^2)/(0.3901*"' + self.ref_dmean + '")'
        output_file = self.dir_out + "taux/taux_" + dir_uux_ras.split('/')[-1]
        self.calculate_raster(expression, output_file, [dir_u_ras, dir_uux_ras, self.dir_dmean], self.dir_taux_txt)

    def set_discharge_duration(self, discharge_labels, duration):
        # discharge_labels = LIST of discharge labels, where '010' corresponds to a discharge of 1000 cfs
        self.dict_q_dur = dict(zip(discharge_labels, duration))

    def set_tcd_dirs(self, dir_tcd):
        # dir_tcd = STR directories to rasters
        try:
            logging.info(' *** loading flow depth raster ...')
            self.dir_tcd = dir_tcd
            self.ref_tcd = dir_tcd.split('/')[-1] + '@1'
            logging.info(' *** ok')
        except:
            logging.info("ERROR: Could not interpret flow depth raster string.")
