'''
Distributions of where the profile center lands
'''

#############

import numpy as np

import astropy.io.ascii as asciireader
import readtxtfile
import nfwutils
import voigt_tools as vt
import globalconfig

#############


class NoOffset(object):
        
    def __call__(self, sim):
        return 0., 0.

########

class SZSimOffset(object):

    def __init__(self):

        self.szsim_offsetcat = asciireader.read('{}/SPT_SN_offset.dat'.format(globalconfig.offsetdistro_dir))

    def configure(self, config):

        self.coresize = config['coresize']
        self.targetz = config['targetz']

    def offset(sim):

        offsetingcoresize = self.szsim_offsetcat[self..szsim_offsetcat['coresize[arcmin]'] == self.coresize]

        selectedsim =np.random.uniform(0, len(offsetingcoresize))

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    
        targetDl = nfwutils.global_cosmology.angulardist(self.targetz)
        anglescale = targetDl/dL  #account for the fact that the fixed angular scatter turns into different effective r_mpc scatter
        offsetx = anglescale*(offsetingcoresize['peak_xpix[arcmin]'] - offsetingcoresize['cluster_xpix'])[selectedsim]  #arcmin
        offsety = anglescale*(offsetingcoresize['peak_ypix'] - offsetingcoresize['cluster_ypix'])[selectedsim]


        offset_phi = np.random.uniform(0, 2*np.pi)

        newoffsetx = offsetx*np.cos(offset_phi) - offsety*np.sin(offset_phi)
        newoffsety = offsetx*np.sin(offset_phi) + offsety*np.cos(offset_phi)

        return newoffsetx, newoffsety


#######


class SZLensingPeakOffset(object):

    def configure(self, config):
        self.targetz = config['targetz']

    def offset(sim):

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    
        targetDl = nfwutils.global_cosmology.angulardist(self.targetz)

        scatter = 0.237*targetDl/dL #arcmin, scaled
        centeroffsetx, centeroffsety = scatter*np.random.standard_normal(2)

        return centeroffsetx, centeroffsety


####


class SZXVPTheoryOffset(object):

    def __init__(self):
        self.xvpoffset = XrayXVPOffset()

    def configure(self, config):

        self.targetz = config['targetz']
        

    def offset(sim):

        #physical scatter in arcmin, approp for target redshift
        xvp_offsetx, xvp_offsety = self.xvpoffset(sim)


        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    
        targetDl = nfwutils.global_cosmology.angulardist(self.targetz)

        sz_noisescatter = 0.3*targetDl/dL #arcmin, scaled
        centeroffsetx, centeroffsety = sz_noisescatter*np.random.standard_normal(2)

        return (centeroffsetx + xvp_offsetx, 
                centeroffsety + xvp_offsety)


####



class SZXVPBCGOffset(object):

    def __init__(self):

        self.sz_xvp_bcg_offsets_deg = readtxtfile.readtxtfile('{}/sptxvp_bcgsz'.format(self.config['offsetdistro_dir']))[:,1]

    def configure(self, config):
        self.targetz = config['targetz']

    def offset(sim):


        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    
        targetDl = nfwutils.global_cosmology.angulardist(self.targetz)
        anglescale = targetDl/dL  #account for the fact that the fixed angular scatter turns into different effective r_mpc scatter

        offset = 60*anglescale*sz_xvp_bcg_offsets_deg[np.random.randint(0, len(sz_xvp_bcg_offsets_deg), 1)]

        offset_phi = np.random.uniform(0, 2*np.pi)

        newoffsetx = offset*np.cos(offset_phi)
        newoffsety = offset*np.sin(offset_phi)

        return newoffsetx, newoffsety


####

class SZAnalytic(object):

    def configure(self, config):
        self.targetz = config['targetz']
        self.szbeam = config['szbeam']
        self.coresize = config['coresize']
        self.sz_xi = config['sz_xi']

    def offset(sim):

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    
        targetDl = nfwutils.global_cosmology.angulardist(self.targetz)
        anglescale = targetDl/dL  #account for the fact that the fixed angular scatter turns into different effective r_mpc scatter

        sz_noisescatter = anglescale*np.sqrt(self.szbeam**2 + self.coresize**2)/self.sz_xi

        centeroffsetx, centeroffsety = sz_noisescatter*np.random.standard_normal(2)

        return (centeroffsetx, 
                centeroffsety)
    
####    




class XrayWTGOffset(object):

    def __init__(self):

        self.wtg_offsets_mpc = [x[0] for x in readtxtfile.readtxtfile('{}/wtg_offsets.dat'.format(globalconfig.offsetdistro_dir))]


    def offset(sim):


        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    

        radial_offset_mpc = self.wtg_offsets_mpc[np.random.randint(0, len(self.wtg_offsets_mpc), 1)]
        radial_offset_arcmin = (radial_offset_mpc/(dL))*(180./np.pi)*60.
        phi_offset = np.random.uniform(0, 2*np.pi)
        centeroffsetx = radial_offset_arcmin*np.cos(phi_offset)
        centeroffsety = radial_offset_arcmin*np.sin(phi_offset)

        return centeroffsetx, centeroffsety


###

class XraySPTHSTOffset(object):

    def offset(sim):

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    

        #offset distribution simple log delta r ~ N(mu, sig) fit to SPT-HST xray bcg offset distro (from Inon)
        centeroffset_mpc = np.exp(-2.625 + 1.413*np.random.standard_normal())
        offset_radial = (centeroffset_mpc/dL)*(180./np.pi)*60.
        offset_phi = np.random.uniform(0, 2*np.pi)

        centeroffsetx = offset_radial*np.cos(offset_phi)
        centeroffsety = offset_radial*np.sin(offset_phi)

        return centeroffsetx, centeroffsety

###


class XrayXVPOffset(object):

    def __init__(self):

        self.xvp_offsets_mpc = readtxtfile.readtxtfile('{}/sptxvp_bcgxray'.format(globalconfig.offsetdistro_dir))[:,0]


    def offset(sim):


        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    


        radial_offset_mpc = self.xvp_offsets_mpc[np.random.randint(0, len(self.xvp_offsets_mpc), 1)][0]
        radial_offset_arcmin = (radial_offset_mpc/(dL))*(180./np.pi)*60.
        phi_offset = np.random.uniform(0, 2*np.pi)
        centeroffsetx = radial_offset_arcmin*np.cos(phi_offset)
        centeroffsety = radial_offset_arcmin*np.sin(phi_offset)

        return centeroffsetx, centeroffsety


###


class XrayCCCPOffset(object):

    def __init__(self):

        self.offsets_kpc = [x[0] for x in readtxtfile.readtxtfile('{}/cccp_offsets.dat'.format(globalconfig.offsetdistro_dir))]

    def offset(sim):

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    



        radial_offset_kpc = self.offsets_kpc[np.random.randint(0, len(self.offsets_kpc), 1)]
        radial_offset_arcmin = (radial_offset_kpc/(1000.*dL))*(180./np.pi)*60.
        phi_offset = np.random.uniform(0, 2*np.pi)
        centeroffsetx = radial_offset_arcmin*np.cos(phi_offset)
        centeroffsety = radial_offset_arcmin*np.sin(phi_offset)

        return centeroffsetx, centeroffsety


###


class XrayLensingPeakOffset(object):

    def offset(sim):

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    

        delta_mpc = 0.107*np.random.standard_normal(2)

        centeroffsetx, centeroffsety = (delta_mpc/dL)*(180./np.pi)*60 #arcmin

        return centeroffsetx, centeroffsety

###

class XrayLensingPeakVoigtOffset(object):

    def offset(sim):

        print 'Xray Lensing Peak Voigt'

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    

        delta_mpc = vt.voigtSamples(0.048, 0.0565, 2, limits=(-0.3, 0.3))

        centeroffsetx, centeroffsety = (delta_mpc/dL)*(180./np.pi)*60 #arcmin

        return centeroffsetx, centeroffsety

###



class XrayMagneticumOffset(object):

    def __init__(self):

        self.xray_magneticum_distro = asciireader.read('{}/magneticum_offsets.dat'.format(globalconfig.offsetdistro_dir))


    def offset(sim):

        dL = nfwutils.global_cosmology.angulardist(sim.zcluster)    

        delta_kpc = self.xray_magneticum_distro['xrayoffset'][np.random.randint(0, len(self.xray_magneticum_distro), 1)][0]

        radial_offset_arcmin = (delta_kpc/(1000*dL))*(180./np.pi)*60 #arcmin
        phi_offset = np.random.uniform(0, 2*np.pi)

        centeroffsetx = radial_offset_arcmin*np.cos(phi_offset)
        centeroffsety = radial_offset_arcmin*np.sin(phi_offset)



        return centeroffsetx, centeroffsety


    

###

