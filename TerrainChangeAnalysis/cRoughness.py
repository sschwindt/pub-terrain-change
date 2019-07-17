import os, logging
from cQgs import QgsMaster

logging.basicConfig(filename='logfile.log', format='%(asctime)s %(message)s', level=logging.DEBUG)


class RoughnessLaw(QgsMaster):
    def __init__(self, raster_dir):
        QgsMaster.__init__(self)
        self.entries = []
        self.dir_dmean = raster_dir + 'dmean'
        self.dir_h = ''
        self.dir_out = os.path.abspath(os.path.dirname(__file__)) + "/output/roughness/"
        self.out_txts = []
        self.out_txt = self.dir_out + 'out_file.txt'
        self.dir_u = ''

        self.label_q = ''

        self.ref_h = ''
        self.ref_u = ''
        self.ref_dmean = 'dmean' + '@1'

    def reset_out_txt(self):
        self.out_txts = []

    def set_hy_rasters(self, dir_h, dir_u):
        # dir_h, dir_u = STR directories to rasters
        try:
            logging.info(' *** loading flow depth raster ...')
            self.dir_h = dir_h
            self.ref_h = dir_h.split('/')[-1] + '@1'
            self.label_q = str(dir_h).split('/h')[-1]
            logging.info(' *** ok')
        except:
            logging.info("ERROR: Could not interpret flow depth raster string.")
        try:
            logging.info(' *** loading flow velocity raster ...')
            self.dir_u = dir_u
            self.ref_u = dir_u.split('/')[-1] + '@1'
            logging.info(' *** ok')
        except:
            logging.info("ERROR: Could not interpret flow depth raster string.")

    def Bathurst(self):
        # Bathurst {D84 = 2.2 D50 in m /304.7992}
        expression = '4+5.62*log10("'+self.ref_h+'"/(2.2*("'+self.ref_dmean+'"/304.7992)))'
        logging.info(" *** Bathurst law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Bathurst_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def Drag1(self):
        # Drag1 {g = 32.174; mannings n set to 0.04}
        n = 0.04
        expression = '32.174*('+str(n)+'^2)*'+self.ref_h+'^(-1/3)'
        logging.info(" *** Drag law 1 g*(n^2)*h(-1/3) called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Drag1_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h], self.out_txt)

    def Drag2(self):
        # Drag2 {Reynold's number = uh/v; 1 m2/s = 10.76391}
        expression = '1.4+36*(10.76391*10^-6)/('+self.ref_h+'*'+self.ref_u+')'
        logging.info(" *** Drag law 2 1.4+36/Re called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Drag2_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_u], self.out_txt)

    def Ferguson(self, a1=str(6.5), a2=str(2.5)):
        # Ferguson {a1 a2 default values 6.5 and 2.5 {D84 = 2.2 D50 in m /304.7992}}
        expression = "("+a1+'*'+a2+'*("'+self.ref_h+'"/(2.2*("'+self.ref_dmean+'"/304.7992))))/(sqrt(sqrt(('+a1+'^2+('+a2+'^2)*("'+self.ref_h+'"/(2.2*("'+self.ref_dmean+'"/304.7992)))^(5/3))^2)))'
        logging.info(" *** Ferguson law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Ferguson_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        # self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean, self.dir_h, self.dir_dmean],
                              self.out_txt)

    def Hey(self):
        # Hey {3.75*D84 = 2.2*3.75 D50 in m /304.7992}
        expression = '6.25+5.75*log10("'+self.ref_h+'"/(8.25*("'+self.ref_dmean+'"/304.7992)))'
        logging.info(" *** Hey law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Hey_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def Keulegan(self):
        # Keulegan {D84 = 2.2 D50 in m /304.7992}
        expression = '6.25+5.75*log10("'+self.ref_h+'"/(2.2*("'+self.ref_dmean+'"/304.7992)))'
        logging.info(" *** Keulegan law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Keulegan_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def MPM(self):
        # MPM { g = 32.174ft/s2 ; 26/sqrt(g) = 4.583 ; D90 = 2.75 D50 in m /304.7992}
        # change D84 to D90. Find multiplication factor
        expression = '4.583748*("'+self.ref_h+'"/(2.75*("'+self.ref_dmean+'"/304.7992)))^(1/6)'
        logging.info(" *** MPM law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "MPM_uux"+self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def ParkerA(self):
        # ParkerA {2*D84 = 2*2.2 D50 in m /304.7992}
        expression = '8.1*("'+self.ref_h+'"/(4.4*("'+self.ref_dmean+'"/304.7992)))^(1/6)'
        logging.info(" *** ParkerA law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "ParkerA_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def ParkerB(self):
        # ParkerB {11/2 within ln; D84 = 2.2 D50 in m /304.7992}
        expression = '(1/0.41)*ln((11/2)*("'+self.ref_h+'"/(2.2*("'+self.ref_dmean+'"/304.7992))))'
        logging.info("ParkerB law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "ParkerB_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def Smart(self):
        # Smart {12.2/2 within log; D84 = 2.2D50 = 2.2*D50/304.7992}
        expression = '5.75*log10((12.2/2)*("'+self.ref_h+'"/(2.2*("'+self.ref_dmean+'"/304.7992))))'
        logging.info(" *** Smart law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Smart_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)

    def Strickler(self):
        # Strickler {g = 32.174, 21.1/sqrt(g) = 3.71988853; D50 = D50 in m / 304.7992}
        expression = '3.719888*("'+self.ref_h+'"/("'+self.ref_dmean+'"/304.7992))^(1/6)'
        logging.info(" *** Strickler law calculation called for " + str(self.label_q) + ".")
        output_file = self.dir_out + "Strickler_uux" + self.ref_h[1:-2] + '.tif'
        self.out_txts.append(output_file)
        self.calculate_raster(expression, output_file, [self.dir_h, self.dir_dmean], self.out_txt)
