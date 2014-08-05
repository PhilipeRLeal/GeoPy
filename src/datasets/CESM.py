'''
Created on 2013-12-04

This module contains common meta data and access functions for CESM model output. 

@author: Andre R. Erler, GPL v3
'''

# external imports
import numpy as np
import os, pickle
from collections import OrderedDict
# from atmdyn.properties import variablePlotatts
from geodata.base import Variable, Axis, Ensemble
from geodata.netcdf import DatasetNetCDF, VarNC
from geodata.gdal import addGDALtoDataset
from geodata.misc import DatasetError, AxisError, DateError, isNumber
from datasets.common import translateVarNames, data_root, grid_folder, default_varatts, addLengthAndNamesOfMonth 
from geodata.gdal import loadPickledGridDef, griddef_pickle
from datasets.WRF import Exp as WRF_Exp
from processing.process import CentralProcessingUnit

# some meta data (needed for defaults)
root_folder = data_root + 'CESM/' # long-term mean folder
outfolder = root_folder + 'cesmout/' # WRF output folder
avgfolder = root_folder + 'cesmavg/' # monthly averages and climatologies
cvdpfolder = root_folder + 'cvdp/' # CVDP output (netcdf files and HTML tree)
diagfolder = root_folder + 'diag/' # output from AMWG diagnostic package (climatologies and HTML tree) 

## list of experiments
class Exp(WRF_Exp): 
  parameters = WRF_Exp.parameters.copy()
  defaults = WRF_Exp.defaults.copy()
  defaults['avgfolder'] = lambda atts: '{0:s}/{1:s}/'.format(avgfolder,atts['name'])
  parameters['cvdpfolder'] = dict(type=basestring,req=True) # new parameters need to be registered
  defaults['cvdpfolder'] = lambda atts: '{0:s}/{1:s}/'.format(cvdpfolder,atts['name'])
  parameters['diagfolder'] = dict(type=basestring,req=True) # new parameters need to be registered
  defaults['diagfolder'] = lambda atts: '{0:s}/{1:s}/'.format(diagfolder,atts['name'])
  defaults['parents'] = None # not applicable here
  
# list of experiments
# N.B.: This is the reference list, with unambiguous, unique keys and no aliases/duplicate entries  
experiments = OrderedDict() # dictionary of experiments
# historical
experiments['ens20trcn1x1'] = Exp(shortname='Ens', name='ens20trcn1x1', title='CESM Ensemble Mean', begindate='1979-01-01', enddate='1995-01-01', grid='cesm1x1')
experiments['tb20trcn1x1'] = Exp(shortname='Ctrl-1', name='tb20trcn1x1', title='Exp D (CESM)', begindate='1979-01-01', enddate='1995-01-01', grid='cesm1x1', ensemble='ens20trcn1x1')
experiments['hab20trcn1x1'] = Exp(shortname='Ctrl-A', name='hab20trcn1x1', title='Exp A (CESM)', begindate='1979-01-01', enddate='1995-01-01', grid='cesm1x1', ensemble='ens20trcn1x1')
experiments['hbb20trcn1x1'] = Exp(shortname='Ctrl-B', name='hbb20trcn1x1', title='Exp B (CESM)', begindate='1979-01-01', enddate='1995-01-01', grid='cesm1x1', ensemble='ens20trcn1x1')
experiments['hcb20trcn1x1'] = Exp(shortname='Ctrl-C', name='hcb20trcn1x1', title='Exp C (CESM)', begindate='1979-01-01', enddate='1995-01-01', grid='cesm1x1', ensemble='ens20trcn1x1')
# mid-21st century
experiments['ensrcp85cn1x1'] = Exp(shortname='Ens-2050', name='ensrcp85cn1x1', title='CESM Ensemble Mean (2050)', begindate='2045-01-01', enddate='2060-01-01', grid='cesm1x1')
experiments['seaice-5r-hf'] = Exp(shortname='Seaice-2050', name='seaice-5r-hf', title='Seaice (CESM, 2050)', begindate='2045-01-01', enddate='2060-01-01', grid='cesm1x1')
experiments['htbrcp85cn1x1'] = Exp(shortname='Ctrl-1-2050', name='htbrcp85cn1x1', title='Exp D (CESM, 2050)', begindate='2045-01-01', enddate='2060-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1')
experiments['habrcp85cn1x1'] = Exp(shortname='Ctrl-A-2050', name='habrcp85cn1x1', title='Exp A (CESM, 2050)', begindate='2045-01-01', enddate='2060-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1')
experiments['hbbrcp85cn1x1'] = Exp(shortname='Ctrl-B-2050', name='hbbrcp85cn1x1', title='Exp B (CESM, 2050)', begindate='2045-01-01', enddate='2060-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1')
experiments['hcbrcp85cn1x1'] = Exp(shortname='Ctrl-C-2050', name='hcbrcp85cn1x1', title='Exp C (CESM, 2050)', begindate='2045-01-01', enddate='2060-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1')
# mid-21st century
experiments['ensrcp85cn1x1d'] = Exp(shortname='Ens-2100', name='ensrcp85cn1x1d', title='CESM Ensemble Mean (2100)', begindate='2085-01-01', enddate='2100-01-01', grid='cesm1x1')
experiments['seaice-5r-hfd'] = Exp(shortname='Seaice-2100', name='seaice-5r-hfd', title='Seaice (CESM, 2100)', begindate='2085-01-01', enddate='2100-01-01', grid='cesm1x1')
experiments['htbrcp85cn1x1d'] = Exp(shortname='Ctrl-1-2100', name='htbrcp85cn1x1d', title='Exp D (CESM, 2100)', begindate='2085-01-01', enddate='2100-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1d')
experiments['habrcp85cn1x1d'] = Exp(shortname='Ctrl-A-2100', name='habrcp85cn1x1d', title='Exp A (CESM, 2100)', begindate='2085-01-01', enddate='2100-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1d')
experiments['hbbrcp85cn1x1d'] = Exp(shortname='Ctrl-B-2100', name='hbbrcp85cn1x1d', title='Exp B (CESM, 2100)', begindate='2085-01-01', enddate='2100-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1d')
experiments['hcbrcp85cn1x1d'] = Exp(shortname='Ctrl-C-2100', name='hcbrcp85cn1x1d', title='Exp C (CESM, 2100)', begindate='2085-01-01', enddate='2100-01-01', grid='cesm1x1', ensemble='ensrcp85cn1x1d')
## an alternate dictionary using short names and aliases for referencing
exps = OrderedDict()
# use short names where available, normal names otherwise
for key,item in experiments.iteritems():
  exps[item.name] = item
  if item.shortname is not None: 
    exps[item.shortname] = item
  # both, short and long name are added to list
# add aliases here
CESM_exps = exps # alias for whole dict
CESM_experiments = experiments # alias for whole dict
## dict of ensembles
ensembles = CESM_ens = OrderedDict()
ensemble_list = list(set([exp.ensemble for exp in experiments.values() if exp.ensemble]))
ensemble_list.sort()
for ensemble in ensemble_list:
  #print ensemble, experiments[ensemble].shortname
  members = [exp for exp in experiments.values() if exp.ensemble and exp.ensemble == ensemble]
  members.sort()
  ensembles[experiments[ensemble].shortname] = members

# return name and folder
def getFolderName(name=None, experiment=None, folder=None, mode='avg', cvdp_mode='ensemble', lcheckExp=True):
  ''' Convenience function to infer and type-check the name and folder of an experiment based on various input. '''
  # N.B.: 'experiment' can be a string name or an Exp instance
  # figure out experiment name
  if experiment is None:
    if not isinstance(folder,basestring):
      if mode == 'cvdp' and ( cvdp_mode == 'observations' or cvdp_mode == 'grand-ensemble' ): 
        folder = "{:s}/grand-ensemble/".format(cvdpfolder)              
      else: raise IOError, "Need to specify an experiment folder in order to load data."    
    # load experiment meta data
    if name in exps: experiment = exps[name]
    elif lcheckExp: raise DatasetError, 'Dataset of name \'{0:s}\' not found!'.format(name)
  else:
    if isinstance(experiment,(Exp,basestring)):
      if isinstance(experiment,basestring): experiment = exps[experiment] 
      # root folder
      if folder is None: 
        if mode == 'avg': folder = experiment.avgfolder
        elif mode == 'cvdp': 
          if cvdp_mode == 'ensemble': folder = "{:s}/{:s}/".format(cvdpfolder,experiment.ensemble)
          elif cvdp_mode == 'grand-ensemble': folder = "{:s}/grand-ensemble/".format(cvdpfolder)
          else: folder = experiment.cvdpfolder
        elif mode == 'diag': folder = experiment.diagfolder
        else: raise NotImplementedError,"Unsupported mode: '{:s}'".format(mode)
      elif not isinstance(folder,basestring): raise TypeError
      # name
      if name is None: name = experiment.name
    if not isinstance(name,basestring): raise TypeError      
  # check if folder exists
  if not os.path.exists(folder): raise IOError, 'Dataset folder does not exist: {0:s}'.format(folder)
  # return name and folder
  return folder, experiment, name


# function to undo NCL's lonFlip
def flipLon(data, flip=144, ax=1, lrev=False, var=None, slc=None):
  ''' shift longitude on the fly, so as to undo NCL's lonFlip; only works on entire array '''
  if var is not None: # ignore parameters
    if not isinstance(var,VarNC): raise TypeError
    ax = var.axisIndex('lon')
    flip = len(var.lon)/2
  if not ( data.ndim > ax and data.shape[ax] == flip*2 ): 
    raise NotImplementedError, "Can only shift longitudes of the entire array!"
  # N.B.: this operation only makes sense with a full array!
  if lrev: flip *= -1 # reverse flip  
  data = np.roll(data, shift=flip, axis=1) # shift values half way along longitude
  return data


## variable attributes and name
class FileType(object): 
  ''' Container class for all attributes of of the constants files. '''
  atts = NotImplemented
  vars = NotImplemented
  climfile = None
  tsfile = None
  cvdpfile = None
  diagfile = None
  
# surface variables
class ATM(FileType):
  ''' Variables and attributes of the surface files. '''
  def __init__(self):
    self.atts = dict(TREFHT   = dict(name='T2', units='K'), # 2m Temperature
                     QREFHT   = dict(name='q2', units='kg/kg'), # 2m water vapor mass mixing ratio                     
                     TS       = dict(name='Ts', units='K'), # Skin Temperature (SST)
                     TSMN     = dict(name='Tmin', units='K'),   # Minimum Temperature (at surface)
                     TSMX     = dict(name='Tmax', units='K'),   # Maximum Temperature (at surface)                     
                     PRECT    = dict(name='precip', units='kg/m^2/s', scalefactor=1000.), # total precipitation rate (kg/m^2/s)
                     PRECC    = dict(name='preccu', units='kg/m^2/s', scalefactor=1000.), # convective precipitation rate (kg/m^2/s)
                     PRECL    = dict(name='precnc', units='kg/m^2/s', scalefactor=1000.), # grid-scale precipitation rate (kg/m^2/s)
                     #NetPrecip    = dict(name='p-et', units='kg/m^2/s'), # net precipitation rate
                     #LiquidPrecip = dict(name='liqprec', units='kg/m^2/s'), # liquid precipitation rate
                     PRECSL   = dict(name='solprec', units='kg/m^2/s', scalefactor=1000.), # solid precipitation rate
                     #SNOWLND   = dict(name='snow', units='kg/m^2'), # snow water equivalent
                     SNOWHLND = dict(name='snowh', units='m'), # snow depth
                     SNOWHICE = dict(name='snowhice', units='m'), # snow depth
                     ICEFRAC  = dict(name='seaice', units=''), # seaice fraction
                     SHFLX    = dict(name='hfx', units='W/m^2'), # surface sensible heat flux
                     LHFLX    = dict(name='lhfx', units='W/m^2'), # surface latent heat flux
                     QFLX     = dict(name='evap', units='kg/m^2/s'), # surface evaporation
                     FLUT     = dict(name='OLR', units='W/m^2'), # Outgoing Longwave Radiation
                     FLDS     = dict(name='GLW', units='W/m^2'), # Ground Longwave Radiation
                     FSDS     = dict(name='SWD', units='W/m^2'), # Downwelling Shortwave Radiation                     
                     PS       = dict(name='ps', units='Pa'), # surface pressure
                     PSL      = dict(name='pmsl', units='Pa'), # mean sea level pressure
                     PHIS     = dict(name='zs', units='m', scalefactor=1./9.81), # surface elevation
                     #LANDFRAC = dict(name='landfrac', units=''), # land fraction
                     )
    self.vars = self.atts.keys()    
    self.climfile = 'cesmatm{0:s}_clim{1:s}.nc' # the filename needs to be extended by ('_'+grid,'_'+period)
    self.tsfile = 'cesmatm{0:s}_monthly.nc' # the filename needs to be extended by ('_'+grid)
# CLM variables
class LND(FileType):
  ''' Variables and attributes of the land surface files. '''
  def __init__(self):
    self.atts = dict(topo     = dict(name='hgt', units='m'), # surface elevation
                     landmask = dict(name='landmask', units=''), # land mask
                     landfrac = dict(name='landfrac', units=''), # land fraction
                     FSNO     = dict(name='snwcvr', units=''), # snow cover (fractional)
                     QMELT    = dict(name='snwmlt', units='kg/m^2/s'), # snow melting rate
                     QOVER    = dict(name='sfroff', units='kg/m^2/s'), # surface run-off
                     QRUNOFF  = dict(name='runoff', units='kg/m^2/s'), # total surface and sub-surface run-off
                     QIRRIG   = dict(name='irrigation', units='kg/m^2/s'), # water flux through irrigation
                     )
    self.vars = self.atts.keys()    
    self.climfile = 'cesmlnd{0:s}_clim{1:s}.nc' # the filename needs to be extended by ('_'+grid,'_'+period)
    self.tsfile = 'cesmlnd{0:s}_monthly.nc' # the filename needs to be extended by ('_'+grid)
# CICE variables
class ICE(FileType):
  ''' Variables and attributes of the seaice files. '''
  def __init__(self):
    self.atts = dict() # currently not implemented...                     
    self.vars = self.atts.keys()
    self.climfile = 'cesmice{0:s}_clim{1:s}.nc' # the filename needs to be extended by ('_'+grid,'_'+period)
    self.tsfile = 'cesmice{0:s}_monthly.nc' # the filename needs to be extended by ('_'+grid)

# CVDP variables
class CVDP(FileType):
  ''' Variables and attributes of the CVDP netcdf files. '''
  def __init__(self):
    self.atts = dict(pdo_pattern_mon = dict(name='PDO_eof', units=''), # PDO EOF
                     pdo_timeseries_mon = dict(name='PDO', units=''), # PDO time-series
                     pna_mon = dict(name='PNA_eof', units=''), # PNA EOF
                     pna_pc_mon = dict(name='PNA', units=''), # PNA time-series
                     npo_mon = dict(name='NPO_eof', units=''), # PNA EOF
                     npo_pc_mon = dict(name='NPO', units=''), # PNA time-series
                     nao_mon = dict(name='NAO_eof', units=''), # PDO EOF
                     nao_pc_mon = dict(name='NAO', units=''), # PDO time-series
                     nam_mon = dict(name='NAM_eof', units=''), # NAM EOF
                     nam_pc_mon = dict(name='NAM', units=''), # NAM time-series
                     amo_pattern_mon = dict(name='AMO_eof', units='', # AMO EOF
                                            transform=flipLon), # undo shifted longitude (done by NCL)
                     amo_timeseries_mon = dict(name='AMO', units=''), # AMO time-series 
                     nino34 = dict(name='NINO34', units=''), # ENSO Nino34 index
                     npi = dict(name='NPI', units=''), # some North Pacific Index ???
                     )                    
    self.vars = self.atts.keys()
    self.indices = [var['name'] for var in self.atts.values() if var['name'].upper() == var['name']]
    self.eofs = [var['name'] for var in self.atts.values() if var['name'][-4:] == '_eof']
    self.cvdpfile = '{:s}.cvdp_data.{:s}.nc' # filename needs to be extended with experiment name and period

# AMWG diagnostic variables
class Diag(FileType):
  ''' Variables and attributes of the AMWG diagnostic netcdf files. '''
  def __init__(self):
    self.atts = dict() # currently not implemented...                     
    self.vars = self.atts.keys()
    self.diagfile = NotImplemented # filename needs to be extended with experiment name and period

# axes (don't have their own file)
class Axes(FileType):
  ''' A mock-filetype for axes. '''
  def __init__(self):
    self.atts = dict(time        = dict(name='time', units='month'), # time coordinate
                     TIME        = dict(name='year', units='year'), # yearly time coordinate in CVDP files
                     # N.B.: the time coordinate is only used for the monthly time-series data, not the LTM
                     #       the time offset is chose such that 1979 begins with the origin (time=0)
                     lon           = dict(name='lon', units='deg E'), # west-east coordinate
                     lat           = dict(name='lat', units='deg N'), # south-north coordinate
                     LON           = dict(name='lon', units='deg E'), # west-east coordinate (actually identical to lon!)
                     LAT           = dict(name='lat', units='deg N'), # south-north coordinate (actually identical to lat!)                     
                     levgrnd = dict(name='s', units=''), # soil layers
                     lev = dict(name='lev', units='')) # hybrid pressure coordinate
    self.vars = self.atts.keys()

# data source/location
fileclasses = dict(atm=ATM(), lnd=LND(), axes=Axes(), cvdp=CVDP()) # ice=ICE() is currently not supported because of the grid
# list of variables and dimensions that should be ignored
ignore_list_2D = ('nbnd', 'slat', 'slon', 'ilev', # atmosphere file
                  'levlak', 'latatm', 'hist_interval', 'latrof', 'lonrof', 'lonatm', # land file
                  ) # CVDP file (omit shifted longitude)
ignore_list_3D = ('lev', 'levgrnd',) # ignore all 3D variables (and vertical axes)

## Functions to load different types of CESM datasets

# CVDP diagnostics (monthly time-series, EOF pattern and correlations) 
def loadCVDP_Obs(name=None, grid=None, period=None, varlist=None, varatts=None, 
                 translateVars=None, lautoregrid=None, ignore_list=None, lindices=False, leofs=False):
  ''' Get a properly formatted monthly observational dataset as NetCDFDataset. '''
  if grid is not None: raise NotImplementedError
  # check datasets
  name = name.lower() # ignore case
  if name in ('hadisst','sst','ts'):
    name = 'HadISST'; period = (1920,2012)
  elif name in ('mlost','t2','tas'):
    name = 'MLOST'; period = (1920,2012)
  elif name in ('20thc_reanv2','ps','psl'):
    name = '20thC_ReanV2'; period = (1920,2012)
  elif name in ('gpcp','precip','prect','ppt'):
    name = 'GPCP'; period = (1979,2014)
  else: raise NotImplementedError, "The dataset '{:s}' is not available.".format(name)
  # load smaller selection
  if varlist is None and ( lindices or leofs ):
    varlist = []
    if lindices: varlist += fileclasses['cvdp'].indices
    if leofs: varlist += fileclasses['cvdp'].eofs
  return loadCESM_All(experiment=None, name=name, grid=grid, period=period, filetypes=('cvdp',), 
                  varlist=varlist, varatts=varatts, translateVars=translateVars, lautoregrid=lautoregrid, 
                  load3D=False, ignore_list=ignore_list, mode='CVDP', cvdp_mode='observations', lcheckExp=False)

# CVDP diagnostics (monthly time-series, EOF pattern and correlations) 
def loadCVDP(experiment=None, name=None, grid=None, period=None, varlist=None, varatts=None, 
             cvdp_mode='ensemble', translateVars=None, lautoregrid=None, ignore_list=None, lcheckExp=True, lindices=False, leofs=False):
  ''' Get a properly formatted monthly CESM climatology as NetCDFDataset. '''
  if grid is not None: raise NotImplementedError
  if period is None: period = 15
  # load smaller selection
  if varlist is None and ( lindices or leofs ):
    varlist = []
    if lindices: varlist += fileclasses['cvdp'].indices
    if leofs: varlist += fileclasses['cvdp'].eofs
  return loadCESM_All(experiment=experiment, name=name, grid=grid, period=period, filetypes=('cvdp',), 
                  varlist=varlist, varatts=varatts, translateVars=translateVars, lautoregrid=lautoregrid, 
                  load3D=True, ignore_list=ignore_list, mode='CVDP', cvdp_mode=cvdp_mode, lcheckExp=lcheckExp)

# Time-Series (monthly)
def loadCESM_TS(experiment=None, name=None, grid=None, filetypes=None, varlist=None,varatts=None,  
                translateVars=None, lautoregrid=None, load3D=False, ignore_list=None, lcheckExp=True):
  ''' Get a properly formatted CESM dataset with monthly time-series. (wrapper for loadCESM)'''
  return loadCESM_All(experiment=experiment, name=name, grid=grid, period=None, filetypes=filetypes, 
                  varlist=varlist, varatts=varatts, translateVars=translateVars, lautoregrid=lautoregrid, 
                  load3D=load3D, ignore_list=ignore_list, mode='time-series', lcheckExp=lcheckExp)

# load minimally pre-processed CESM climatology files 
def loadCESM(experiment=None, name=None, grid=None, period=None, filetypes=None, varlist=None, varatts=None, 
             translateVars=None, lautoregrid=None, load3D=False, ignore_list=None, lcheckExp=True):
  ''' Get a properly formatted monthly CESM climatology as NetCDFDataset. '''
  return loadCESM_All(experiment=experiment, name=name, grid=grid, period=period, filetypes=filetypes, 
                  varlist=varlist, varatts=varatts, translateVars=translateVars, lautoregrid=lautoregrid, 
                  load3D=load3D, ignore_list=ignore_list, mode='climatology', lcheckExp=lcheckExp)


# load minimally pre-processed CESM climatology (and time-series) files 
def loadCESM_All(experiment=None, name=None, grid=None, period=None, filetypes=None, varlist=None, varatts=None, 
                 translateVars=None, lautoregrid=None, load3D=False, ignore_list=None, mode='climatology', 
                 cvdp_mode='ensemble', lcheckExp=True):
  ''' Get any of the monthly CESM files as a properly formatted NetCDFDataset. '''
  # period
  if isinstance(period,(tuple,list)):
    if not all(isNumber(period)): raise ValueError
  elif isinstance(period,basestring): period = [int(prd) for prd in period.split('-')]
  elif isinstance(period,(int,np.integer)) or period is None : pass # handled later
  else: raise DateError, "Illegal period definition: {:s}".format(str(period))
  # prepare input  
  lclim = False; lts = False; lcvdp = False; ldiag = False # mode switches
  if mode.lower() == 'climatology': # post-processed climatology files
    lclim = True
    folder,experiment,name = getFolderName(name=name, experiment=experiment, folder=None, mode='avg', lcheckExp=lcheckExp)    
    if period is None: raise DateError, 'Currently CESM Climatologies have to be loaded with the period explicitly specified.'
  elif mode.lower() == 'time-series': # concatenated time-series files
    lts = True
    folder,experiment,name = getFolderName(name=name, experiment=experiment, folder=None, mode='avg', lcheckExp=lcheckExp)
    lclim = False; period = None; periodstr = None # to indicate time-series (but for safety, the input must be more explicit)
    if lautoregrid is None: lautoregrid = False # this can take very long!
  elif mode.lower() == 'cvdp': # concatenated time-series files
    lcvdp = True
    folder,experiment,name = getFolderName(name=name, experiment=experiment, folder=None, mode='cvdp', 
                                           cvdp_mode=cvdp_mode, lcheckExp=lcheckExp)
  elif mode.lower() == 'diag': # concatenated time-series files
    ldiag = True
    folder,experiment,name = getFolderName(name=name, experiment=experiment, folder=None, mode='diag', lcheckExp=lcheckExp)
    raise NotImplementedError, "Loading AMWG diagnostic files is not supported yet."
  else: raise NotImplementedError,"Unsupported mode: '{:s}'".format(mode)  
  # period  
  if isinstance(period,(int,np.integer)):
    if not isinstance(experiment,Exp): raise DatasetError, 'Integer periods are only supported for registered datasets.'
    period = (experiment.beginyear, experiment.beginyear+period)
  if lclim: periodstr = '_{0:4d}-{1:4d}'.format(*period)
  elif lcvdp: periodstr = '{0:4d}-{1:4d}'.format(period[0],period[1]-1)
  else: periodstr = ''
  # N.B.: the period convention in CVDP is that the end year is included
  # generate filelist and attributes based on filetypes and domain
  if filetypes is None: filetypes = ['atm','lnd']
  elif isinstance(filetypes,(list,tuple,set)):
    filetypes = list(filetypes)  
    if 'axes' not in filetypes: filetypes.append('axes')    
  else: raise TypeError  
  atts = dict(); filelist = []; typelist = []
  for filetype in filetypes:
    fileclass = fileclasses[filetype]
    if lclim and fileclass.climfile is not None: filelist.append(fileclass.climfile)
    elif lts and fileclass.tsfile is not None: filelist.append(fileclass.tsfile)
    elif lcvdp and fileclass.cvdpfile is not None: filelist.append(fileclass.cvdpfile)
    elif ldiag and fileclass.diagfile is not None: filelist.append(fileclass.diagfile)
    typelist.append(filetype)
    atts.update(fileclass.atts) 
  # figure out ignore list  
  if ignore_list is None: ignore_list = set(ignore_list_2D)
  elif isinstance(ignore_list,(list,tuple)): ignore_list = set(ignore_list)
  elif not isinstance(ignore_list,set): raise TypeError
  if not load3D: ignore_list.update(ignore_list_3D)
  if lautoregrid is None: lautoregrid = not load3D # don't auto-regrid 3D variables - takes too long! 
  # translate varlist
  if varatts is not None: atts.update(varatts)
  if varlist is not None:
    if translateVars is None: varlist = list(varlist) + translateVarNames(varlist, atts) # also aff translations, just in case
    elif translateVars is True: varlist = translateVarNames(varlist, atts) 
    # N.B.: DatasetNetCDF does never apply translation!
  # get grid name
  if grid is None or grid == experiment.grid: 
    gridstr = ''; griddef = None
  else: 
    gridstr = '_%s'%grid.lower() # only use lower case for filenames
    griddef = loadPickledGridDef(grid=grid, res=None, filename=None, folder=grid_folder, check=True)
  # insert grid name and period
  filenames = []
  for filetype,fileformat in zip(typelist,filelist):
    if lclim: filename = fileformat.format(gridstr,periodstr) # put together specfic filename for climatology
    elif lts: filename = fileformat.format(gridstr) # or for time-series
    elif lcvdp: filename = fileformat.format(name,periodstr) # not implemented: gridstr
    elif ldiag: raise NotImplementedError
    else: raise DatasetError
    filenames.append(filename) # append to list (passed to DatasetNetCDF later)
    # check existance
    filepath = '{:s}/{:s}'.format(folder,filename)
    if not os.path.exists(filepath):
      nativename = fileformat.format('',periodstr) # original filename (before regridding)
      nativepath = '{:s}/{:s}'.format(folder,nativename)
      if os.path.exists(nativepath):
        if lautoregrid: 
          from processing.regrid import performRegridding # causes circular reference if imported earlier
          griddef = loadPickledGridDef(grid=grid, res=None, folder=grid_folder)
          dataargs = dict(experiment=experiment, filetypes=[filetype], period=period)
          if performRegridding('CESM','climatology' if lclim else 'time-series', griddef, dataargs): # default kwargs
            raise IOError, "Automatic regridding failed!"
        else: raise IOError, "The '{:s}' (CESM) dataset '{:s}' for the selected grid ('{:s}') is not available - use the regrid module to generate it.".format(name,filename,grid) 
      else: raise IOError, "The '{:s}' (CESM) dataset file '{:s}' does not exits!\n({:s})".format(name,filename,folder)
   
  # load dataset
  #print varlist, filenames
  dataset = DatasetNetCDF(name=name, folder=folder, filelist=filenames, varlist=varlist, axes=None, varatts=atts, 
                          multifile=False, ignore_list=ignore_list, ncformat='NETCDF4', squeeze=True)
  # replace time axis
  if lts or lcvdp:
    if experiment is None: ys = period[0]; ms = 1
    else: ys,ms,ds = [int(t) for t in experiment.begindate.split('-')]; assert ds == 1
    ts = (ys-1979)*12 + (ms-1); te = ts+len(dataset.time) # month since 1979 (Jan 1979 = 0)
    atts = dict(long_name='Month since 1979-01')
    timeAxis = Axis(name='time', units='month', data=np.arange(ts,te,1, dtype='int16'), atts=atts)
    dataset.repalceAxis(dataset.time, timeAxis, asNC=False, deepcopy=False)
  # check
  if len(dataset) == 0: raise DatasetError, 'Dataset is empty - check source file or variable list!'
  # add projection
  dataset = addGDALtoDataset(dataset, griddef=griddef, gridfolder=grid_folder, lwrap360=True, geolocator=True)
  # return formatted dataset
  return dataset

## Dataset API

dataset_name = 'CESM' # dataset name
root_folder # root folder of the dataset
avgfolder # root folder for monthly averages
outfolder # root folder for direct WRF output
ts_file_pattern = 'cesm{0:s}{1:s}_monthly.nc' # filename pattern: filetype, grid
clim_file_pattern = 'cesm{0:s}{1:s}_clim{2:s}.nc' # filename pattern: filetype, grid, period
data_folder = root_folder # folder for user data
grid_def = {'':None} # there are too many... 
grid_res = {'':1.} # approximate grid resolution at 45 degrees latitude
default_grid = None 
# functions to access specific datasets
loadLongTermMean = None # WRF doesn't have that...
loadTimeSeries = loadCESM_TS # time-series data
loadClimatology = loadCESM # pre-processed, standardized climatology


## (ab)use main execution for quick test
if __name__ == '__main__':
  
  # set mode/parameters
  #mode = 'test_climatology'
#     mode = 'test_timeseries'
  mode = 'test_cvdp'
#     mode = 'pickle_grid'
#     mode = 'shift_lon'
#     experiments = ['Ctrl-1', 'Ctrl-A', 'Ctrl-B', 'Ctrl-C']
#     experiments += ['Ctrl-2050', 'Ctrl-A-2050', 'Ctrl-B-2050', 'Ctrl-C-2050']
  experiments = ('Ctrl-C-2050',)
  periods = (15,)    
  filetypes = ('atm','lnd') # ['atm','lnd','ice']
  grids = ('arb2_d02',)*len(experiments) # grb1_d01

  # pickle grid definition
  if mode == 'pickle_grid':
    
    for grid,experiment in zip(grids,experiments):
      
      print('')
      print('   ***   Pickling Grid Definition for {0:s}   ***   '.format(grid))
      print('')
      
      # load GridDefinition
      dataset = loadCESM(experiment=experiment, grid=None, filetypes=['lnd'], period=(1979,1989))
      griddef = dataset.griddef
      #del griddef.xlon, griddef.ylat      
      print griddef
      griddef.name = grid
      print('   Loading Definition from \'{0:s}\''.format(dataset.name))
      # save pickle
      filename = '{0:s}/{1:s}'.format(grid_folder,griddef_pickle.format(grid))
      if os.path.exists(filename): os.remove(filename) # overwrite
      filehandle = open(filename, 'w')
      pickle.dump(griddef, filehandle)
      filehandle.close()
      
      print('   Saving Pickle to \'{0:s}\''.format(filename))
      print('')
      
      # load pickle to make sure it is right
      del griddef
      griddef = loadPickledGridDef(grid, res=None, folder=grid_folder)
      print(griddef)
      print('')
    
  # load averaged climatology file
  elif mode == 'test_climatology' or mode == 'test_timeseries':
    
    for grid,experiment in zip(grids,experiments):
      
      print('')
      if mode == 'test_timeseries':
        dataset = loadCESM_TS(experiment=experiment, varlist=None, grid=None, filetypes=filetypes)
      else:
        period = periods[0] # just use first element, no need to loop
        dataset = loadCESM(experiment=experiment, varlist=None, grid=None, filetypes=filetypes, period=period)
      print(dataset)
      print('')
#       print(dataset.geotransform)
      print dataset.time
      print dataset.time.coord
      # show some variables
#       if 'zs' in dataset: var = dataset.zs
#       elif 'hgt' in dataset: var = dataset.hgt
#       else: var = dataset.lon2D
#       var.load()
#       print var
#       var = var.mean(axis='time',checkAxis=False)
      # display
#       import pylab as pyl
#       pyl.pcolormesh(dataset.lon2D.getArray(), dataset.lat2D.getArray(), dataset.precip.getArray().mean(axis=0))
#       pyl.pcolormesh(dataset.lon2D.getArray(), dataset.lat2D.getArray(), dataset.runoff.getArray().mean(axis=0))
#       pyl.pcolormesh(dataset.lon2D.getArray(), dataset.lat2D.getArray(), var.getArray())
#       pyl.colorbar()
#       pyl.show(block=True)
  
  # load CVDP file
  elif mode == 'test_cvdp':
    
    for grid,experiment in zip(grids,experiments):
      
      print('')
      period = periods[0] # just use first element, no need to loop
      dataset = loadCVDP(experiment=experiment, period=period, cvdp_mode='ensemble', lindices=True)
      #dataset = loadCVDP_Obs(name='GPCP')
      print(dataset)
#       print(dataset.geotransform)
      time = dataset.time(time=(12,24))
      print(dataset.time)
      print(time)
      print(len(time))
      # print some variables
#       print('')
#       eof = dataset.pdo_pattern; eof.load()
# #       print eof
#       print('')
#       ts = dataset.pdo_timeseries; ts.load()
# #       print ts
#       print ts.mean()
      # display
#       import pylab as pyl
#       pyl.pcolormesh(dataset.lon2D.getArray(), dataset.lat2D.getArray(), dataset.precip.getArray().mean(axis=0))
#       pyl.pcolormesh(dataset.lon2D.getArray(), dataset.lat2D.getArray(), dataset.runoff.getArray().mean(axis=0))
#       pyl.pcolormesh(dataset.lon2D.getArray(), dataset.lat2D.getArray(), eof.getArray())
#       pyl.colorbar()
#       pyl.show(block=True)
      print('')
  
  # shift dataset from 0-360 to -180-180
  elif mode == 'shift_lon':
   
    # loop over periods
    for prdlen in periods: # (15,): # 
      # loop over experiments
      for experiment in experiments: # ('CESM',): #  
        # loop over filetypes
        for filetype in filetypes: # ('lnd',): #  
          fileclass = fileclasses[filetype]
          
          # load source
          exp = CESM_exps[experiment]
          period = (exp.beginyear, exp.beginyear+prdlen)
          periodstr = '{0:4d}-{1:4d}'.format(*period)
          print('\n')
          print('   ***   Processing Experiment {0:s} for Period {1:s}   ***   '.format(exp.title,periodstr))
          print('\n')
          # prepare file names
          filename = fileclass.climfile.format('','_'+periodstr)
          origname = 'orig'+filename[4:]; tmpname = 'tmp.nc'
          filepath = exp.avgfolder+filename; origpath = exp.avgfolder+origname; tmppath = exp.avgfolder+tmpname
          # load source
          if os.path.exists(origpath) and os.path.exists(filepath): 
            os.remove(filepath) # overwrite old file
            os.rename(origpath,filepath) # get original source
          source = loadCESM(experiment=exp, period=period, filetypes=[filetype])
          print(source)
          print('\n')
          # savety checks
          if os.path.exists(origpath): raise IOError
          if np.max(source.lon.getArray()) < 180.: raise AxisError
          if not os.path.exists(filepath): raise IOError
          # prepare sink
          if os.path.exists(tmppath): os.remove(tmppath)
          sink = DatasetNetCDF(name=None, folder=exp.avgfolder, filelist=[tmpname], atts=source.atts, mode='w')
          sink.atts.period = periodstr 
          sink.atts.name = exp.name
          
          # initialize processing
          CPU = CentralProcessingUnit(source, sink, tmp=False)
          
          # shift longitude axis by 180 degrees left (i.e. 0 - 360 -> -180 - 180)
          CPU.Shift(lon=-180, flush=True)
          
          # sync temporary storage with output
          CPU.sync(flush=True)
              
          # add new variables
          # liquid precip (atmosphere file)
          if sink.hasVariable('precip') and sink.hasVariable('solprec'):
            data = sink.precip.getArray() - sink.solprec.getArray()
            Var = Variable(axes=sink.precip.axes, name='liqprec', data=data, atts=default_varatts['liqprec'])            
            sink.addVariable(Var, asNC=True) # create variable and add to dataset
          # net precip (atmosphere file)
          if sink.hasVariable('precip') and sink.hasVariable('evap'):
            data = sink.precip.getArray() - sink.evap.getArray()
            Var = Variable(axes=sink.precip.axes, name='p-et', data=data, atts=default_varatts['p-et'])
            sink.addVariable(Var, asNC=True) # create variable and add to dataset      
          # underground runoff (land file)
          if sink.hasVariable('runoff') and sink.hasVariable('sfroff'):
            data = sink.runoff.getArray() - sink.sfroff.getArray()
            Var = Variable(axes=sink.runoff.axes, name='ugroff', data=data, atts=default_varatts['ugroff'])
            sink.addVariable(Var, asNC=True) # create variable and add to dataset    
    
          # add length and names of month
          if sink.hasAxis('time', strict=False):
            addLengthAndNamesOfMonth(sink, noleap=True)     
          # close...
          sink.sync()
          sink.close()
          
          # move files
          os.rename(filepath, origpath)
          os.rename(tmppath,filepath)
          
          # print dataset
          print('')
          print(sink)               
