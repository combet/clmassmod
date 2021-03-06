###############
# Script to compare 2D surface density profiles from MXXL to SD profile predicted by NFW and Diemer
###############

import os
import numpy as np
import matplotlib.pyplot as plt
import cPickle
import pkg_resources


import astropy.cosmology as astrocosmo
import astropy.units as units

import colossus.cosmology.cosmology as cCosmo
import colossus.halo.concentration as chc
import colossus.halo.profile_dk14 as dk14prof
import colossus.defaults as cDefaults

import nfwfitter.nfwutils as nfwutils
import nfwfitter.colossusMassCon as cmc
import nfwfitter.readMXXLProfile as readMXXLProfile
import nfwfitter.readAnalytic as readAnalytic
import nfwfitter.readMXXL as readMXXL


########
# mass tables

answers = {
    'halo_41' : cPickle.load(pkg_resources.resource_stream('nfwfitter',
                                                           'data/mxxlsnap41_answers.pkl')),
    'halo_54' : cPickle.load(pkg_resources.resource_stream('nfwfitter',
                                                           'data/mxxlsnap54_answers.pkl'))
}




########

def computeSDProfiles(halobase, mcmodel='diemer15'):

    #read 2D profile
    simprofile = readMXXLProfile.MXXLProfile('{}.radial_profile.txt'.format(halobase))
    simarea = np.pi*(simprofile.outer_radius**2 - simprofile.inner_radius**2)
    simdensity = simprofile.diff_mass / simarea  #M_sol / Mpc**2
    r_mpc = simprofile.median_radius

    #read halo mass
    sim_and_haloid = os.path.basename(halobase)
    tokens = sim_and_haloid.split('_')
    simid = '_'.join(tokens[:2])
    haloid = '_'.join(tokens[2:])

    #make sure cosmology always matches
    curcosmo = readMXXLProfile.cosmo
    nfwutils.global_cosmology.set_cosmology(curcosmo)
    cmc.matchCosmo()

    #compute Diemer SD prediction
    r_kpch = (r_mpc*1000*curcosmo.h)
    
    m200 = answers[simid][haloid]['m200'] #M_sol/h
    zcluster = answers[simid][haloid]['redshift']
    c200 = chc.concentration(m200, '200c', zcluster, model=mcmodel)

    diemer_profile = dk14prof.getDK14ProfileWithOuterTerms(M = m200, c = c200, z = zcluster, mdef = '200c')
    surfacedensity_func, deltaSigma_func = readAnalytic.calcLensingTerms(diemer_profile, np.max(r_kpch))
    convert_units = 1./(curcosmo.h*1e6) #M_sol / Mpc^2 -> diemer units
    diemer_surfacedensity = surfacedensity_func(r_kpch)/convert_units


    #add mean background density to Diemer prediction
    acosmo = astrocosmo.FlatLambdaCDM(curcosmo.H0, curcosmo.omega_m)
    density_units_3d = units.solMass / units.Mpc**3
    density_units_2d = units.solMass / units.Mpc**2
    back_density = (acosmo.Om(zcluster)*acosmo.critical_density(zcluster)).to(density_units_3d)
    print back_density
    back_sd_contrib = back_density*(200.*units.Mpc/curcosmo.h)
    print back_sd_contrib
#    simdensity = simdensity*density_units_2d - back_sd_contrib
    diemer_surfacedensity += back_sd_contrib

    return dict(radius=r_mpc,
                simprofile=simdensity,
                diemerprofile=diemer_surfacedensity)
    

########


def plotSDProfile(ax, halobase):

    profiles = computeSDProfiles(halobase)
    r_mpc = profiles['radius']
    simdensity = profiles['simprofile']
    diemer_surfacedensity = profiles['diemerprofile']

    #and plot results

    ax.loglog(r_mpc, simdensity, 'ko', markersize=5)
    ax.loglog(r_mpc, diemer_surfacedensity, 'b-')
    ax.axvline(3., c='k', linewidth=3, linestyle='--')


#######

def plotAvgProfile(ax, halobases, mcmodel='diemer15', profilefunc=computeSDProfiles):

    
    profiles = [profilefunc(halo, mcmodel=mcmodel) for halo in halobases]


    #average up the profiles
    averadius = np.mean(np.row_stack([x['radius'] for x in profiles]), axis=0)
    avesimprofile = np.mean(np.row_stack([x['simprofile'] for x in profiles]), axis=0)
    avediemerprofile = np.mean(np.row_stack([x['diemerprofile'] for x in profiles]), axis=0)

    ax.loglog(averadius, avesimprofile, 'ko', markersize=5)
    ax.loglog(averadius, avediemerprofile, 'b-')
    ax.axvline(3., c='k', linewidth=3, linestyle='--')


########


def compute3DProfile(halobase, mcmodel='diemer15'):

    #read 3D profile
    simprofile = readMXXLProfile.MXXLProfile('{}.radial_profile_3D.txt'.format(halobase))
    simvolume = (4./3.)*np.pi*(simprofile.outer_radius**3 - simprofile.inner_radius**3)
    simdensity = simprofile.diff_mass / simvolume  #M_sol / Mpc**3
    r_mpc = simprofile.median_radius

    #read halo mass
    sim_and_haloid = os.path.basename(halobase)
    tokens = sim_and_haloid.split('_')
    simid = '_'.join(tokens[:2])
    haloid = '{}_0'.format(tokens[2])

    #make sure cosmology always matches
    curcosmo = readMXXLProfile.cosmo
    nfwutils.global_cosmology.set_cosmology(curcosmo)
    cmc.matchCosmo()

    #compute Diemer SD prediction
    r_kpch = (r_mpc*1000*curcosmo.h)
    
    m200 = answers[simid][haloid]['m200'] #M_sol/h
    zcluster = answers[simid][haloid]['redshift']
    c200 = chc.concentration(m200, '200c', zcluster, model=mcmodel)

    diemer_profile = dk14prof.getDK14ProfileWithOuterTerms(M = m200, c = c200, z = zcluster, mdef = '200c')
    #density is returned with units M_solh^2/kpc^3. 
    convert_units = 1e9*curcosmo.h**2  # converts to M_sol/Mpc^3

    diemer_density = diemer_profile.density(r_kpch)*convert_units

    return dict(radius=r_mpc,
                simprofile=simdensity,
                diemerprofile=diemer_density)
    

########

class ProfileSet(object):

    def __init__(self):
        self.r_mpc = None
        self.beta_s = None
        self.beta_s2 = None
        self.zcluster = None
        self._ghats = []

    def __add__(self, profile):

        if self.r_mpc is None:
            self.r_mpc = profile.r_mpc
            self.beta_s = profile.beta_s
            self.beta_s2 = profile.beta_s2
            self.zcluster = profile.zcluster
#        else:
            #all halos at same redshift with same radial range:
            #    -> r_mpc, beta_s, zcluster all same across halos
#            assert((profile.r_mpc == self.r_mpc).all() and \
#               profile.beta_s == self.beta_s and \
#               profile.beta_s2 == self.beta_s2 and \
#               profile.zcluster == self.zcluster)


        self._ghats.append(profile.ghat)

        return self

    @property
    def ghats(self):
        return np.row_stack(self._ghats)

    def todict(self):
        return dict(r_mpc = self.r_mpc,
                    beta_s = self.beta_s,
                    beta_s2 = self.beta_s2,
                    zcluster = self.zcluster,
                    ghats = self.ghats)


def computeStackedShearProfile(halobases, config):

    profilebuilder = config['profilebuilder']

    simreader = config['simreader']


    def mapProfile(halobase):
        sim = simreader.load(halobase)
        profile = profilebuilder(sim)
        return profile

    reduceProfiles = lambda profileset, profile: profileset + profile    


    profiles = map(mapProfile, halobases)
    profileset = reduce(reduceProfiles, profiles, ProfileSet())

    return profileset
    


