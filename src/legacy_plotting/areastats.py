'''
Created on 2013-11-14

A simple script to plot area-averaged monthly climatologies. 

@author: Andre R. Erler, GPL v3
'''

# external imports
import numpy as np
import matplotlib as mpl
# mpl.use('Agg') # enforce QT4
import matplotlib.pylab as pyl
# prevent figures from closing: don't run in interactive mode, or plt.show() will not block
pyl.ioff()
# internal imports
# PyGeoDat stuff
from datasets.GPCC import loadGPCC
from datasets.CRU import loadCRU
from datasets.PRISM import loadPRISM
from datasets.PCIC import loadPCIC
from datasets.CFSR import loadCFSR
from datasets.NARR import loadNARR
from datasets.Unity import loadUnity
from datasets.WSC import Basin
from legacy_plotting.legacy import loadDatasets # for annotation
from plotting.misc import loadStyleSheet
# ARB project related stuff
from projects.WesternCanada import figure_folder, getFigureSettings, WRF_exps, CESM_exps

def getVarSettings(plottype, area, lPRISM=False, mode='all'):
  flxlabel = r'Water Flux [$10^6$ kg/s]' 
  if area == 'athabasca': flxlim = (-2,4) if lPRISM else (-3,7)
  elif area == 'fraser': flxlim = (-5,20)
  elif area == 'northcoast': flxlim = (0,35)
  elif area == 'southcoast': flxlim = (-5,25)
  else: flxlim = (-5,20)
  if plottype == 'heat':
    varlist = ['lhfx','hfx']; filetypes = ['hydro','srfc']; 
    lsum = False; leg = (2,3); ylabel = r'Heat Flux [W m$^{-2}$]'; ylim = (-50,150)  
  elif plottype == 'pet':
    varlist = ['precip','evap','pet']; filetypes = ['srfc','hydro']; # 'waterflx' 
    lsum = True; leg = (2,3); ylabel = flxlabel; ylim = (0,14)
  elif plottype == 'flux':
    varlist = ['snwmlt','p-et','precip','solprec']; filetypes = ['srfc','hydro']; # 'waterflx' 
    lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'evap': # flux - solprec
    varlist = ['snwmlt','p-et','precip']; filetypes = ['srfc','hydro']; # 'waterflx' 
    lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'snwmlt': # flux - p-et
    varlist = ['snwmlt','precip','solprec']; filetypes = ['srfc','hydro']; # 'waterflx' 
    lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'temp':
    varlist = ['T2','Tmin','Tmax']; filetypes = ['srfc','xtrm'] 
    lsum = False; leg = (2,8); ylabel = 'Temperature [K]'; ylim = (250,300)
  elif plottype == 'precip':
      varlist = ['precip','liqprec','solprec']; filetypes = ['hydro'] # 
      lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim  
  elif plottype == 'precip_types':
      varlist = ['precip','preccu','precnc']; filetypes = ['srfc'] # 
      lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim        
  elif plottype == 'p-et':
    varlist = ['p-et','precip','pet']; filetypes = ['hydro'] # 
    lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'p-et_all':
    varlist = ['p-et','precip','liqprec','solprec']; filetypes = ['hydro'] # 
    lsum = True; leg = (2,3); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'flxrof':
    varlist = ['waterflx','runoff','snwmlt','p-et','precip']; filetypes = ['srfc','hydro','lsm']; 
    lsum = True; leg = (2,1); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'runoff':
    varlist = ['snwmlt','runoff','sfroff','p-et']; filetypes = ['lsm','hydro']; # 'ugroff' 
    lsum = True; leg = (2,1); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'sfflx':
    varlist = ['waterflx','runoff','sfroff']; filetypes = ['lsm','hydro']; # 'ugroff' 
    lsum = True; leg = (2,1); ylabel = flxlabel; ylim = flxlim
  elif plottype == 'sfroff':
    varlist = ['runoff','sfroff']; filetypes = ['lsm','hydro']; # 'ugroff' 
    lsum = True; leg = (2,1); ylabel = flxlabel; ylim = flxlim
  else:
    raise TypeError('\'{}\' is not a valid plottype!'.format(plottype))
  # return values
  lCFSR = False; lNARR = False
  if mode == 'all':
    return varlist, filetypes, lsum, leg, ylabel, ylim, lCFSR, lNARR
  elif mode == 'load':
    return varlist, filetypes, lCFSR, lNARR
  elif mode == 'plot':
    return varlist, lsum, leg, ylabel, ylim, lCFSR, lNARR
  
def getDatasets(expset, titles=None):
  # linestyles
  linestyles = ('-','--','-.')
  # datasets
  if expset == '3km':
    explist = [('erai-3km','erai-max','max-3km')]
  elif expset == '1deg':
    explist = ['Ctrl','max','max-1deg','max-ens']
    explist = [(exp,'max') for exp in explist]
    titles = ['CESM-1', 'WRF-1 (10 km)', 'WRF-1 (1 deg.)', 'WRF Ensemble']  
  elif expset == 'deltas':
    explist = [('ctrl-2050','ctrl-1'),('max-2050','max'),('cam-2050','cam'),('max-ens-2050','max-ens')]
  elif expset == 'noahmp+': 
    explist = [('new','noah','max')]
    titles = 'Noah-MP vs. Noah'
  elif expset == 'ctrl-12':
    explist = [('ctrl-1-arb1', 'ctrl-2-arb1')]
  elif expset == 'newmax': 
    explist = ['gulf','new','max','noah']
    explist = [(exp,'max-ens') for exp in explist]
  elif expset == 'micro': 
    explist = ['max-kf','wdm6','ctrl','tom']
    explist = [(exp,'max-ens') for exp in explist]
  elif expset == 'cu':  
    explist = ['max', 'max-nosub', 'max-hilev', 'max-kf']
  elif expset == 'lsm': 
    explist = ['max','max-diff','max-nmp','max-nmp-old']  
  elif expset == 'mean-ens-2050': 
    explist = ['max-ens-2050','CESM-2050','seaice-2050','Seaice-2050']
  elif expset == 'max-var':
    explist = ['max','max-A','max-nofdda','max-fdda']
  elif expset == 'max-all':
    explist = ['max','max-A','max-B','max-C']
  elif expset == 'max-all-2050': 
    explist = ['seaice-2050','max-A-2050','max-B-2050','max-C-2050']
  elif expset == 'max-all-diff':
    explist = [('max-2050','max'),('max-A-2050','max-A'),('max-B-2050','max-B'),('max-C-2050','max-C')]
    titles = ['WRF-1 ({0:s})','WRF-2 ({0:s})','WRF-3 ({0:s})','WRF-4 ({0:s})'] # include basin name
  elif expset == 'max-all-var':
    explist = [('max-ens','max-ens')]
    linestyles = ('-','--')  
  elif expset == 'cesm-all': 
    explist = ['Ctrl-A','Ctrl-B','Ctrl-C','Ctrl-1']
  elif expset == 'cesm-all-2050': 
    explist = ['Ctrl-A-2050','Ctrl-B-2050','Ctrl-C-2050','Ctrl-1-2050']
  elif expset == 'cesm-all-diff': 
    explist = [('Ctrl-A-2050','Ctrl-A'),('Ctrl-B-2050','Ctrl-B'),('Ctrl-C-2050','Ctrl-C'),('Ctrl-1-2050','Ctrl-1')]
  elif expset == 'max-mid-diff':
    explist = [('max-ens-2050','max-ens')]
    titles = 'WRF Ensemble Mean (Mid-21st-Century), {0:s}' # include basin name
  elif expset == 'max-end-diff':
    explist = [('max-ens-2100','max-ens')]
    titles = 'WRF Ensemble Mean (End-21st-Century), {0:s}'
  elif expset == 'max-2100-diff':
    explist = [('max-ctrl-2100','max-ctrl')]
    titles = 'WRF Max (End-21st-Century)'
  elif expset == 'max-2050-diff':
    explist = [('max-ctrl-2050','max-ctrl')]
    titles = 'WRF Max (Mid-21st-Century)'
  elif expset == 'mean-diff-cesm':
    explist = [('CESM-2050','CESM')]  
    titles = 'CESM Ensemble Mean (Mid-21st-Century)'
  elif expset == 'max-2050-diff':
    explist = [('max-ctrl-2050','max-ctrl')]
    titles = 'WRF Max (Mid-21st-Century)'
  elif expset == 'erai-max-ens':
    explist = [('erai-max','max-ens')]
    titles = 'ERA-I & WRF vs. WRF Ensemble Mean, {:s}'
  else:
    explist = [expset]
    if expset == 'max-ens-2050': titles = 'WRF Ensemble Mean (Mid-21st-Century), {:s}'
    elif expset == 'max-ens-2100': titles = 'WRF Ensemble Mean (End-21st-Century), {:s}'
    elif expset == 'max-ens': titles = 'WRF Ensemble Mean (Historical Period), {:s}'
  # expand linestyles
  linestyles = [linestyles,]*len(explist)
  # default titles
  if titles is None:
    titles = []
    for exp in explist:
      if isinstance(exp,(list,tuple)):
        assert len(exp) > 1
        title = '' 
        for e in exp[:-1]: title += '{:s}, '.format(e)
        title = '{:s} & {:s}'.format(title[:-2],exp[-1])  
      else: title = exp
      title += ' ({:s})' # for basin name
      titles.append(title)
  # return dataset names
  return explist, titles, linestyles


## start computation
if __name__ == '__main__':
  
  ## settings
  # settings
  lprint = False; lpublication = False; lpresentation = True
  paper_folder = '/home/me/Research/Extreme Value Analysis/Report/Brewer-Wilson Talk 2015/figures/'
  loadStyleSheet('default', lpresentation=lpresentation, lpublication=lpublication)
  # experiments
#   expset = 'max-ens-2050'
#   expset = 'max-ens-2100'
#   expset = 'max-mid-diff'
#   expset = 'max-end-diff'
  expset = 'max-ens'
#   expset = 'erai-max-ens'
#   expset = '3km'
  plottypes = []
  plottypes += ['temp'] # 
#   plottypes += ['precip'] #
#   plottypes += ['sfflx']
#   plottypes += ['flux'] #
#   plottypes += ['precip_types'] #
#   plottypes += ['evap']
#   plottypes += ['snwmlt']  
#   plottypes += ['flxrof']
#   plottypes += ['runoff']#
#   plottypes += ['sfroff'] #
  lPRISM = False
  lPCIC = False
  lUnity = False
  lgage = True
  titles = None
  areas = []
  areas += ['athabasca']
  areas += ['fraser']
#   areas += ['northcoast']
#   areas += ['southcoast']
  domains = 2
#   domains = [(3,2,3)] # [0, 2, 1, 1]
  periods = []
  periods += [5]
  #periods += [10]
#   periods += [15]
#   periods += [(1979,1984)]
#   periods += [(1989,1994)]
  
  # some more settings
  tag = 'prism' if lPRISM else ''
  ljoined = True # joined legend at bottom of figure
  grid = 'arb2_d02' # make sure we are all on the same grid, since the mask is only on that grid
  varatts = None # dict(Runoff=dict(name='runoff'))
  xlabel = r'Seasonal Cycle [Month]'; xlim = (1,12)

  # loop over time periods
  for period in periods:
    
    obsprd = period
#   obsprd = (1949,2009)

    # loop over areas
    for area in areas:

      lCRU = False; lGPCC = False

      ## variable settings
#       loadlist = set(['datamask']); allfiletypes = set()
      loadlist = set(); allfiletypes = set()
      lCFSR = False; lNARR = False
      for plottype in plottypes:
        varlist, filetypes, lcfsr, lnarr = getVarSettings(plottype, area, lPRISM=lPRISM, mode='load')
        loadlist = loadlist.union(varlist)
        allfiletypes = allfiletypes.union(filetypes)
        lCFSR = lCFSR or lcfsr; lNARR = lNARR or lnarr
      
      ## load data  
      explist, titles, linestyles = getDatasets(expset, titles=titles)
      exps, titles, nlist = loadDatasets(explist, n=None, varlist=loadlist,
					                               titles=titles, periods=period, 
                                         domains=domains, grids=grid,
                                         resolutions='025', filetypes=allfiletypes,                                          
                                         lWRFnative=False, ltuple=True,
                                         lbackground=False,lautoregrid=True,
                                         WRF_exps=WRF_exps, CESM_exps=CESM_exps)
      ref = exps[0][0]; nlen = len(exps)
      # observations  
      if period == 9: period = 10 # nine is only because some experiments don't have 10 yet...
      if lCRU: cru = loadCRU(period=obsprd, grid=grid, varlist=loadlist, varatts=varatts)
      if lGPCC: gpcc = loadGPCC(period=None, grid=grid, varlist=loadlist, varatts=varatts)
      if lPRISM: prism = loadPRISM(period=None, grid=grid, varlist=loadlist, varatts=varatts)
      if lPCIC: pcic = loadPCIC(period=None, grid=grid, varlist=loadlist, varatts=varatts)
      if lUnity: unity = loadUnity(period=obsprd, grid=grid, varlist=loadlist, varatts=varatts)
      if lCFSR: cfsr = loadCFSR(period=period, grid=grid, varlist=loadlist, varatts=varatts)
      if lNARR: narr = loadNARR(period=period, grid=grid, varlist=loadlist, varatts=varatts)  
      print(ref)
      print(ref.name)
      
      ## create averaging mask
      if area == 'athabasca': 
        areaname = 'ARB'; subarea = 'WholeARB'; areatitle = 'ARB'
      elif area == 'fraser': 
        areaname = 'FRB'; subarea = 'WholeFRB'; areatitle = 'FRB'
      elif area == 'northcoast': 
        areaname = 'PSB'; subarea = 'NorthernPSB'; areatitle = 'Northern PSB'
      elif area == 'southcoast': 
        areaname = 'PSB'; subarea = 'SouthernPSB'; areatitle = 'Southern PSB'
      else: 
        raise ValueError('Have to specify a river area or other shapefile to use as mask!')
      basin = Basin(basin=areaname, subbasin=subarea)
      if lgage: maingage = basin.getMainGage()
      shp_mask = basin.rasterize(griddef=ref.griddef)
      if lPRISM: shp_mask = (shp_mask + prism.datamask.getArray(unmask=True,fillValue=1)).astype(np.bool)
      # display
    #   pyl.imshow(np.flipud(shp_mask[:,:])); pyl.colorbar(); pyl.show(block=True)
     
      ## apply area mask
      for exptpl in exps:
        for exp in exptpl:
          exp.load()
          exp.mask(mask=shp_mask, invert=False)
      # apply mask to observation datasets  
      if lCRU and len(cru.variables) > 0: 
        cru.load(); cru.mask(mask=shp_mask, invert=False)
      if lGPCC and len(gpcc.variables) > 0: 
        gpcc.load(); gpcc.mask(mask=shp_mask, invert=False)
      if lPRISM and len(prism.variables) > 0: 
        prism.load(); prism.mask(mask=shp_mask, invert=False)
      if lUnity and len(unity.variables) > 0: 
        unity.load(); unity.mask(mask=shp_mask, invert=False)  
      if lNARR and len(narr.variables) > 0: 
        narr.load(); narr.mask(mask=shp_mask, invert=False)
      if lCFSR and len(cfsr.variables) > 0: 
        cfsr.load(); cfsr.mask(mask=shp_mask, invert=False)
      # surface area scale factor
    #   asf = ( 1 - shp_mask ).sum() * (ref.atts.DY*ref.atts.DY) / 1.e6
      asf = ( 1 - shp_mask ).sum() * 100
        
      
      # display
    #   pyl.imshow(np.flipud(dataset.Athabasca_River_Basin.getArray()))
    #   pyl.imshow(np.flipud(dataset.precip.getMapMask()))
    #   pyl.colorbar(); 
    
      ## loop over plottypes
      for plottype in plottypes:
        varlist, lsum, leg, ylabel, ylim, lCFSR, lNARR = getVarSettings(plottype, area, lPRISM=lPRISM, mode='plot')
        #lCFSR = False; lNARR = False
    #     lCFSR = lCFSR and lcfsr; lNARR = lNARR and lnarr
        S = asf if lsum else 1. # apply scale factor, depending on plot type  
       
        ## setting up figure
        if not lpublication: linewidth = 1.5
        elif nlen == 1: linewidth = 1.75
        elif nlen == 2: linewidth = 1.25
        elif nlen == 4: linewidth = 0.75 
        else: linewidth = 1.
        mpl.rc('lines', linewidth=linewidth)
        if linewidth == .75: fontsize=8
        elif linewidth == 1.: fontsize=10
        elif linewidth == 1.25: fontsize=11
        elif linewidth == 1.5: fontsize=12
        elif linewidth == 1.75: fontsize=15
        else: fontsize=10
        mpl.rc('font', size=fontsize)
        # figure parameters for saving
        sf, figformat, margins, subplot, figsize = getFigureSettings(nlen, cbar=False)
        # make figure and axes
        fig, axes = pyl.subplots(*subplot, sharex=True, sharey=True, facecolor='white', figsize=figsize)
        axes = np.asanyarray(axes)
        if axes.ndim == 0: axes = axes.reshape((1,1))
        if axes.ndim == 1: axes = axes.reshape((1,len(axes)))
    #     if not isinstance(axes,(list,tuple)): axes = (axes,)
    #     if not isinstance(axes[0],(list,tuple)): axes = tuple([(ax,) for ax in axes])    
        fig.subplots_adjust(**margins) # hspace, wspace
        
        # loop over axes
        n = -1 # axes counter
        for i in range(subplot[0]):
          for j in range(subplot[1]):
            n += 1 # count up
            # select axes
            ax,exptpl,title,linestyle = axes[i,j],exps[n],titles[n],linestyles[n]
            # alignment
            if j == 0 : left = True
            else: left = False 
            if i == subplot[0]-1: bottom = True
            else: bottom = False           
          
            # make plots
            time = exptpl[0].time.coord # time axis 
            wrfplt = []; wrfleg = [] 
            obsplt = []; obsleg = []
            # loop over vars    
            for var in varlist:
              # define color
              if var == 'T2': color = 'green'
              elif var == 'precip': color = 'green'
              elif var == 'liqprec': color = 'blue'
              elif var == 'solprec': color = 'cyan'
              elif var == 'preccu': color = 'blue'
              elif var == 'precnc': color = 'cyan'
              elif var == 'evap': color = 'coral'
              elif var == 'p-et': color = 'red'
              elif var == 'pet': color = 'purple'
              elif var == 'waterflx': color = 'blue'
              elif var == 'snwmlt': color = 'coral'
              elif var == 'runoff': color = 'purple'
              elif var == 'ugroff': color = 'coral'
              elif var == 'sfroff': color = 'green'
              elif var == 'Tmax': color = 'red'
              elif var == 'Tmin': color = 'blue'
              elif var == 'hfx': color = 'red'
              elif var == 'lhfx': color = 'blue'
              # loop over datasets in plot
              if not isinstance(linestyle,tuple): linestyle = (linestyle,)*len(exptpl)
              for z,exp,ln in zip(range(len(exptpl)),exptpl,linestyle):           
                # compute spatial average
                if exp.hasVariable(var, strict=False):
                  if 'CESM' in title and var in ('Tmin','Tmax'): pass
                  else:
                    vardata = exp.variables[var].mean(x=None,y=None)                
                    if z == 0: 
                      wrfplt.append(ax.plot(time, S*vardata.getArray(), linestyle=ln, color=color, label=var)[0])
                      wrfleg.append(var)
                    else:
                      ax.plot(time, S*vardata.getArray(), linestyle=ln, color=color, label=var)
                    print()
                    print(exp.name, vardata.name, S*vardata.getArray().mean())
              # river gage
              if lgage and var in ('sfroff',): 
                vardata = maingage.variables['discharge']
                label = '%s (%s)'%('discharge','obs')
                obsplt.append(ax.plot(time, vardata.getArray()/1e6, 'o', markersize=5*linewidth, color=color, label=label)[0]) # , linewidth=1.5
                obsleg.append(label)
                print()
                print(maingage.name, vardata.name, vardata.getArray().mean()/1e6)
              # either PRISM ...
              elif lPRISM and prism.hasVariable(var, strict=False):
                # compute spatial average for CRU
                vardata = prism.variables[var].mean(x=None,y=None)
                label = '%s (%s)'%(var,prism.name)
                obsplt.append(ax.plot(time, S*vardata.getArray(), 'o', markersize=4*linewidth, color=color, label=label)[0]) # , linewidth=1.5
                obsleg.append(label)
                print()
                print(prism.name, vardata.name, S*vardata.getArray().mean())
              # .. or Unity        
              elif lUnity and unity.hasVariable(var, strict=False):
                # compute spatial average for CRU
                vardata = unity.variables[var].mean(x=None,y=None)
                label = '%s (%s)'%(var,'obs')
                obsplt.append(ax.plot(time, S*vardata.getArray(), 'o', markersize=5*linewidth, color=color, label=label)[0])
                obsleg.append(label)
                print()
                print(unity.name, vardata.name, S*vardata.getArray().mean())
              # ... or CRU, perhaps...        
              if lCRU and cru.hasVariable(var, strict=False):
                # compute spatial average for CRU
                vardata = cru.variables[var].mean(x=None,y=None)
                label = '%s (%s)'%(var,cru.name)
                obsplt.append(ax.plot(time, S*vardata.getArray(), 'x', markersize=6*linewidth, color=color, label=label)[0])
                obsleg.append(label)
                print()
                print(cru.name, vardata.name, S*vardata.getArray().mean())
              # the rest can be added at will...
              if lGPCC and gpcc.hasVariable(var, strict=False):
                # compute spatial average for GPCC
                label = '%s (%s)'%(var,gpcc.name)
                vardata = gpcc.variables[var].mean(x=None,y=None)
                obsplt.append(ax.plot(time, S*vardata.getArray(), 'o', markersize=4*linewidth, color='purple', label=label)[0])
                obsleg.append(label)
                print()
                print(gpcc.name, vardata.name, S*vardata.getArray().mean())
              if lCFSR and cfsr.hasVariable(var, strict=False):
                # compute spatial average for CRU
                if cfsr.isProjected: vardata = cfsr.variables[var].mean(x=None,y=None)
                else: vardata = cfsr.variables[var].mean(lon=None,lat=None)
                label = '%s (%s)'%(var,cfsr.name)
                obsplt.append(ax.plot(time, S*vardata.getArray(), '--', color='blue', label=label)[0])
                obsleg.append(label)
                print()
                print(cfsr.name, vardata.name, S*vardata.getArray().mean())
              if lNARR and narr.hasVariable(var, strict=False):
                # compute spatial average for GPCC
                label = '%s (%s)'%(var,narr.name)
                vardata = narr.variables[var].mean(x=None,y=None)
                obsplt.append(ax.plot(time, S*vardata.getArray(), '--', color='red', label=label)[0])
                obsleg.append(label)
                print()
                print(narr.name, vardata.name, S*vardata.getArray().mean())
              # axes
              labelpad = 3 # lambda lim: -8 if lim[0] < 0 else 3       
              ax.set_xlim(xlim[0],xlim[1])
              if left: ax.set_ylabel(ylabel, labelpad=labelpad)
              # else: ax.set_yticklabels([])          
              ax.set_ylim(ylim[0],ylim[1])
              if bottom: ax.set_xlabel(xlabel, labelpad=labelpad)
              # else: ax.set_xticklabels([])
              #ax.minorticks_on()
              ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
              # legend
              if not ljoined:
                legargs = dict(labelspacing=0.125, handlelength=1.5, handletextpad=0.5, fancybox=True)
                wrflegend = ax.legend(wrfplt, wrfleg, loc=leg[0], **legargs)       
                obslegend = ax.legend(obsplt, obsleg, loc=leg[1], **legargs)
                ax.add_artist(wrflegend); ax.add_artist(obslegend)
              # annotation
              #ax.set_title(title+' ({})'.format(exp.name))
              ax.set_title(title.format(areatitle)) # could add more stuff here
              if var in ['p-et', 'precip', 'runoff']:
                ax.axhline(620,linewidth=0.5, color='k')
                ax.axhline(0,linewidth=0.5, color='0.5')
          
        # add common legend
        if ljoined:
          leghgt = fontsize/250. + margins['hspace']
          ax = fig.add_axes([0, 0, 1,leghgt])
          ax.set_frame_on(False); ax.axes.get_yaxis().set_visible(False); ax.axes.get_xaxis().set_visible(False)
          margins['bottom'] = margins['bottom'] + leghgt; fig.subplots_adjust(**margins)
          legargs = dict(frameon=True, labelspacing=0.1, handlelength=1.3, handletextpad=0.3, fancybox=True)
#           if nlen == 1: legargs = dict(frameon=True, labelspacing=0.1, handlelength=1.3, handletextpad=0.3, fancybox=True)
#           else: legargs = dict(frameon=True, labelspacing=0.15, handlelength=2, handletextpad=0.5, fancybox=True)
          plt = wrfplt + obsplt; leg = wrfleg + obsleg
          if fontsize > 11: ncols = 3 # if len(leg) == 4 else 3
          else: ncols = 3 if len(leg) == 6 else 4            
          legend = ax.legend(plt, leg, loc=10, ncol=ncols, borderaxespad=0., **legargs)  
          
        # average discharge below Fort McMurray: 620 m^3/s
          
        # save figure to disk
        if lprint:
          if area == 'athabasca': 
            areatag='ARB'; folder = figure_folder + '/Athabasca River Basin/' 
          elif area == 'fraser': 
            areatag = 'FRB'; folder = figure_folder + '/Fraser River Basin/'
          elif area == 'northcoast': 
            areatag = 'NPSB'; folder = figure_folder + '/Northern Pacific Seaboard/'    
          elif area == 'southcoast': 
            areatag = 'SPSB'; folder = figure_folder + '/Southern Pacific Seaboard/'    
          if lpublication or lpresentation: folder = paper_folder        
          tag = '_'+tag if tag else ''
          domtag = '_d{0:02d}'.format(domains) if isinstance(domains,int) and domains != 2 else '' 
          filename = '{0:s}_{1:s}_{2:s}{3:s}{4:s}.png'.format(areatag,plottype,expset,domtag,tag)
          print(('\nSaving figure in '+filename))
          fig.savefig(folder+filename, **sf) # save figure to pdf
          print(folder)
      
  ## show plots after all iterations
  pyl.show()
