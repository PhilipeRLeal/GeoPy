'''
Created on 2013-10-21

Script to produce climatology files from monthly mean time-series' for all or a subset of available WRF experiments.

@author: Andre R. Erler, GPL v3
'''

# external
import numpy as np
import os, gc
from datetime import datetime
# internal
from geodata.base import Variable
from geodata.netcdf import DatasetNetCDF
from geodata.gdal import GridDefinition
from geodata.misc import isInt, DateError
from datasets.common import name_of_month, days_per_month, getCommonGrid
from processing.process import CentralProcessingUnit
from processing.multiprocess import asyncPoolEC
# WRF specific
from datasets.WRF import loadWRF_TS, fileclasses
from projects.WRF_experiments import WRF_exps, Exp, WRF_experiments


def computeClimatology(experiment, filetype, domain, periods=None, offset=0, griddef=None, varlist=None, 
                       ldebug=False, loverwrite=False, lparallel=False, pidstr='', logger=None):
  ''' worker function to compute climatologies for given file parameters. '''
  # input type checks
  if not isinstance(experiment,Exp): raise TypeError
  if not isinstance(filetype,basestring): raise TypeError
  if not isinstance(domain,(np.integer,int)): raise TypeError
  if periods is not None and not (isinstance(periods,(tuple,list)) and isInt(periods)): raise TypeError
  if not isinstance(offset,(np.integer,int)): raise TypeError
  if not isinstance(loverwrite,(bool,np.bool)): raise TypeError  
  if griddef is not None and not isinstance(griddef,GridDefinition): raise TypeError
  
  #if pidstr == '[proc01]': raise TypeError # to test error handling

  # load source
  fileclass = fileclasses[filetype] # used for target file name
  logger.info('\n\n{0:s}   ***   Processing Experiment {1:<15s}   ***   '.format(pidstr,"'{:s}'".format(experiment.name)) +
        '\n{0:s}   ***   {1:^37s}   ***   \n'.format(pidstr,"'{:s}'".format(fileclass.tsfile.format(domain,''))))
  
  # assemble filename to check modification dates (should be only one file)    
  filepath = '{:s}/{:s}'.format(experiment.avgfolder,fileclass.tsfile.format(domain,''))

  # check file and read begin/enddates
  if not os.path.exists(filepath): raise IOError, "Source file '{:s}' does not exist!".format(filepath)
  import netCDF4 as nc
  ncfile = nc.Dataset(filepath,mode='r')
  begintuple = ncfile.begin_date.split('-')
  endtuple = ncfile.end_date.split('-')
  ncfile.close()
  # N.B.: at this point we don't want to initialize a full GDAL-enabled dataset, since we don't even
  #       know if we need it, and it creates a lot of overhead
  
  # determine age of oldest source file
  if not loverwrite: sourceage = datetime.fromtimestamp(os.path.getmtime(filepath))

  # figure out start date
  filebegin = int(begintuple[0]) # first element is the year
  fileend = int(endtuple[0]) # first element is the year
  begindate = offset + filebegin
  if not ( filebegin <= begindate <= fileend ): raise DateError  
  # handle cases where the first month in the record is not January
  firstmonth = int(begintuple[1]) # second element is the month
  shift = firstmonth-1 # will be zero for January (01)
  # other settings
  expfolder = experiment.avgfolder
  dataset_name = experiment.name
  
  ## loop over periods
  source = None # will later be assigned to the source dataset
  if periods is None: periods = [begindate-fileend]
#   periods.sort(reverse=True) # reverse, so that largest chunk is done first
  for period in periods:       
            
    # figure out period
    enddate = begindate + period     
    if filebegin > enddate: raise DateError    
    if enddate-1 > fileend: # if filebegin is 1979 and the simulation is 10 years, fileend will be 1988, not 1989!
      endmsg = "\n{:s}   ---   Invalid Period for '{:s}': End Date {:4d} not in File!   ---   \n".format(pidstr,dataset_name,enddate)
      endmsg += "{:s}   ---   ('{:s}')\n".format(pidstr,filepath)
      logger.info(endmsg)
      
    else:  

      # determine if sink file already exists, and what to do about it      
      periodstr = '{0:4d}-{1:4d}'.format(begindate,enddate)
      gridstr = '' if griddef is None or griddef.name is 'WRF' else '_'+griddef.name
      filename = fileclass.climfile.format(domain,gridstr,'_'+periodstr)
      if ldebug: filename = 'test_' + filename
      if lparallel: tmppfx = 'tmp_wrfavg_{:s}_'.format(pidstr[1:-1])
      else: tmppfx = 'tmp_wrfavg_'.format(pidstr[1:-1])
      tmpfilename = tmppfx + filename
      assert os.path.exists(expfolder)
      filepath = expfolder+filename
      tmpfilepath = expfolder+tmpfilename
      lskip = False # else just go ahead
      if os.path.exists(filepath): 
        if not loverwrite: 
          age = datetime.fromtimestamp(os.path.getmtime(filepath))
          # if sink file is newer than source file, skip (do not recompute)
          if age > sourceage and os.path.getsize(filepath) > 1e6: lskip = True
          # N.B.: NetCDF files smaller than 1MB are usually incomplete header fragments from a previous crash
          #print sourceage, age
        if not lskip: os.remove(filepath) 
      
      # depending on last modification time of file or overwrite setting, start computation, or skip
      if lskip:        
        # print message
        skipmsg =  "\n{:s}   >>>   Skipping: file '{:s}' in dataset '{:s}' already exists and is newer than source file.".format(pidstr,filename,dataset_name)
        skipmsg += "\n{:s}   >>>   ('{:s}')\n".format(pidstr,filepath)
        logger.info(skipmsg)              
      else:
         
        ## begin actual computation
        beginmsg = "\n{:s}   <<<   Computing '{:s}' (d{:02d}) Climatology from {:s}".format(
                    pidstr,dataset_name,domain,periodstr)
        if griddef is None: beginmsg += "  >>>   \n" 
        else: beginmsg += " ('{:s}' grid)  >>>   \n".format(griddef.name)
        logger.info(beginmsg)

        ## actually load datasets
        if source is None:
          source = loadWRF_TS(experiment=experiment, filetypes=[filetype], domains=domain) # comes out as a tuple... 
        if not lparallel and ldebug: logger.info('\n'+str(source)+'\n')

        # prepare sink
        if os.path.exists(tmpfilepath): os.remove(tmpfilepath) # remove old temp files
        sink = DatasetNetCDF(name='WRF Climatology', folder=expfolder, filelist=[tmpfilename], atts=source.atts.copy(), mode='w')
        sink.atts.period = periodstr 
        
        # initialize processing
        if griddef is None: lregrid = False
        else: lregrid = True
        CPU = CentralProcessingUnit(source, sink, varlist=varlist, tmp=lregrid, feedback=ldebug) # no need for lat/lon
        
        # start processing climatology
        if shift != 0: 
          logger.info('{0:s}   (shifting climatology by {1:d} month, to start with January)   \n'.format(pidstr,shift))
        CPU.Climatology(period=period, offset=offset, shift=shift, flush=False)
        # N.B.: immediate flushing should not be necessary for climatologies, since they are much smaller!
        
        # reproject and resample (regrid) dataset
        if lregrid:
          CPU.Regrid(griddef=griddef, flush=True)
          logger.info('%s    ---   '+str(griddef.geotansform)+'   ---   \n'%(pidstr))              
        
        # sync temporary storage with output dataset (sink)
        CPU.sync(flush=True)
        
        # add Geopotential Height Variance
        if 'GHT_Var' in sink and 'Z_var' not in sink:
          data_array = ( sink['GHT_Var'].data_array - sink['Z'].data_array**2 )**0.5
          atts = dict(name='Z_var',units='m',long_name='Square Root of Geopotential Height Variance')
          sink += Variable(axes=sink['Z'].axes, data=data_array, atts=atts)
          
        # add (relative) Vorticity Variance
        if 'Vorticity_Var' in sink and 'zeta_var' not in sink:
          data_array = ( sink['Vorticity_Var'].data_array - sink['zeta'].data_array**2 )**0.5
          atts = dict(name='zeta_var',units='1/s',long_name='Square Root of Relative Vorticity Variance')
          sink += Variable(axes=sink['zeta'].axes, data=data_array, atts=atts)
          
        # add names and length of months
        sink.axisAnnotation('name_of_month', name_of_month, 'time', 
                            atts=dict(name='name_of_month', units='', long_name='Name of the Month'))        
        if not sink.hasVariable('length_of_month'):
          sink += Variable(name='length_of_month', units='days', axes=(sink.time,), data=days_per_month,
                        atts=dict(name='length_of_month',units='days',long_name='Length of Month'))
        
        # close... and write results to file
        sink.sync()
        sink.close()
        writemsg =  "\n{:s}   >>>   Writing to file '{:s}' in dataset {:s}".format(pidstr,filename,dataset_name)
        writemsg += "\n{:s}   >>>   ('{:s}')\n".format(pidstr,filepath)
        logger.info(writemsg)      
        # rename file to proper name
        if os.path.exists(filepath): os.remove(filepath) # remove old file
        os.rename(tmpfilepath,filepath) # this will overwrite the old file
        
        # print dataset
        if not lparallel and ldebug:
          logger.info('\n'+str(sink)+'\n')
        
        # clean up (not sure if this is necessary, but there seems to be a memory leak...   
        del sink, CPU; gc.collect() # get rid of these guys immediately
          
  # this one is only loaded once for all periods    
  # clean up and return
  if source is not None: source.unload(); del source
  # N.B.: garbage is collected in multi-processing wrapper as well

  # return
  return 0 # so far, there is no measure of success, hence, if there is no crash...


if __name__ == '__main__':
  
  ## read arguments
  # number of processes NP 
  if os.environ.has_key('PYAVG_THREADS'): 
    NP = int(os.environ['PYAVG_THREADS'])
  else: NP = None
  # run script in debug mode
  if os.environ.has_key('PYAVG_DEBUG'): 
    ldebug =  os.environ['PYAVG_DEBUG'] == 'DEBUG' 
  else: ldebug = False # i.e. append
  # run script in batch or interactive mode
  if os.environ.has_key('PYAVG_BATCH'): 
    lbatch =  os.environ['PYAVG_BATCH'] == 'BATCH' 
  else: lbatch = False # i.e. append  
  # re-compute everything or just update 
  if os.environ.has_key('PYAVG_OVERWRITE'): 
    loverwrite =  os.environ['PYAVG_OVERWRITE'] == 'OVERWRITE' 
  else: loverwrite = ldebug # False means only update old files
    # file types to process 
  # domains to process
  if os.environ.has_key('PYAVG_DOMAINS'): 
    domains = os.environ['PYAVG_DOMAINS'].split(';') # semi-colon separated list
  else: domains = None # defaults are set below
  if os.environ.has_key('PYAVG_FILETYPES'): 
    filetypes = os.environ['PYAVG_FILETYPES'].split(';') # semi-colon separated list
  else: filetypes = None # defaults are set below

  
  # default settings
  if not lbatch:
    NP = 4 ; ldebug = False # for quick computations
    NP = 1 ; ldebug = True # just for tests
    loverwrite = False
    varlist = None # ['lat2D', ]
    experiments = []
    experiments += ['max-ctrl-dry']
#     experiments += ['erai-3km','max-3km']
#     experiments += ['erai-wc2-bugaboo','erai-wc2-rocks']
#     experiments += ['new','noah','max','max-2050']
#     experiments += ['new-grell-old','new','max-nmp','max-nmp-old','max-clm','max']
#     experiments += ['max-1deg', 'max-1deg-2050','max-1deg-2100']
#     experiments += ['new-v36-nmp', 'new-v36-noah', 'erai-v36-noah', 'new-v36-clm']
#     experiments += ['max-ctrl','max-ens-A','max-ens-B','max-ens-C',]
#     experiments += ['max-ctrl-2050','max-ens-A-2050','max-ens-B-2050','max-ens-C-2050',]    
#     experiments += ['max-ctrl-2100','max-ens-A-2100','max-ens-B-2100','max-ens-C-2100',]
#     experiments += ['max-nofdda','max-fdda']
#     experiments += ['max-ctrl-2100']
#     experiments += ['ctrl-arb1', 'ctrl-arb1-2050', 'ctrl-2-arb1',]
#     experiments += ['max-3km']
#     experiments += ['erai-max']
    offset = 0 # number of years from simulation start
    periods = [] # not that all periods are handled within one process! 
#     periods += [1]
#     periods += [3]
    periods += [5]
#     periods += [9]
    periods += [10]
    periods += [15]
#     domains = (1,) # domains to be processed
    domains = None # process all domains
#     filetypes = ['plev3d'] # filetypes to be processed
#     filetypes = ['srfc','xtrm','plev3d','hydro','lsm'] # filetypes to be processed # ,'rad'
#     filetypes = ['srfc','xtrm','lsm','hydro']
    filetypes = ['hydro'] # filetypes to be processed
#     filetypes = ['srfc','xtrm','plev3d','hydro']
    grid = 'native'
  else:
    NP = NP or 2
    ldebug=False
    loverwrite = False
    varlist = None # all variables
    experiments = None # WRF experiment names (passed through WRF_exps)
#     experiments = [] # list of most important experiments
#     experiments += ['max-1deg', 'max-1deg-2050','max-1deg-2100',]
#     experiments += ['erai-max', 'max-seaice-2050','max-seaice-2100',]
#     experiments += ['max-ctrl','max-ens-A','max-ens-B','max-ens-C',]
#     experiments += ['max-ctrl-2050','max-ens-A-2050','max-ens-B-2050','max-ens-C-2050',]    
#     experiments += ['max-ctrl-2100','max-ens-A-2100','max-ens-B-2100','max-ens-C-2100',]
    offset = 0 # number of years from simulation start
    periods = (5,10,15,) # averaging period
    domains = None # domains to be processed (None means all domains)
    filetypes = ['srfc','xtrm','plev3d','hydro','lsm'] # filetypes to be processed # , rad
    grid = 'native' 

  # expand experiments
  if experiments is None: experiments = WRF_experiments.values() # do all 
  else: experiments = [WRF_exps[exp] for exp in experiments] 

  # shall we do some fancy regridding?
  if grid == 'native':
    griddef = None
  else:
    griddef = getCommonGrid(grid)
  
  # print an announcement
  print('\n Computing Climatologies for WRF experiments:\n')
  print([exp.name for exp in experiments])
  if grid != 'native': print('\nRegridding to \'{0:s}\' grid.\n'.format(grid))
  print('\nOVERWRITE: {0:s}\n'.format(str(loverwrite)))
      
  # assemble argument list and do regridding
  args = [] # list of arguments for workers, i.e. "work packages"
  # generate list of parameters
  for experiment in experiments:    
    # loop over file types
    for filetype in filetypes:                
      # effectively, loop over domains
      if domains is None:
        tmpdom = range(1,experiment.domains+1)
      else: tmpdom = domains
      for domain in tmpdom:
        # arguments for worker function
        args.append( (experiment, filetype, domain) )        
  # static keyword arguments
  kwargs = dict(periods=periods, offset=offset, griddef=griddef, loverwrite=loverwrite, varlist=varlist)        
  # call parallel execution function
  ec = asyncPoolEC(computeClimatology, args, kwargs, NP=NP, ldebug=ldebug, ltrialnerror=True)
  # exit with fraction of failures (out of 10) as exit code
  exit(int(10+np.ceil(10.*ec/len(args))) if ec > 0 else 0)