#!/usr/bin/env python
import os,sys
import json
import optparse
import commands
import math
import ROOT
from ROOT import TFile, TH1F, TH2F, THStack, TCanvas, TPad, TPaveText, TLegend

# a wrapper for the plots
from UserCode.sm_cms_das.PlotUtils import *

"""
Gets the value of a given item
(if not available a default value is returned)
"""
def getByLabel(desc,key,defaultVal=None) :
    try :
        return desc[key]
    except KeyError:
        return defaultVal


"""
Loop over file to find all histograms
"""
def getAllPlotsFrom(dir):
    toReturn=[]
    allKeys=dir.GetListOfKeys()
    for tk in allKeys:
        k=tk.GetName()
        obj=dir.Get(k)
        if obj.InheritsFrom('TDirectory') :
            allKeysInSubdir = getAllPlotsFrom(obj)
            for kk in allKeysInSubdir : toReturn.append( k+'/'+kk )
        elif obj.InheritsFrom('TH1') :
            toReturn.append( k )
    return toReturn
        

"""
Loop over the inputs and launch jobs
"""
def runPlotter(inDir, jsonUrl, lumi ):

    jsonFile = open(jsonUrl,'r')
    procList=json.load(jsonFile,encoding='utf-8').items()

    #make a survey of *all* existing plots
    plots=[]
    for proc in procList :
    
        for desc in proc[1] :
            data = desc['data']
            for d in data :
                dtag = getByLabel(d,'dtag','')
                split=getByLabel(d,'split',1)
            
                for segment in range(0,split) :
                    eventsFile=dtag
                    if split>1: eventsFile=dtag + '_' + str(segment)
                    rootFileUrl=inDir+'/'+eventsFile+'.root'
                    if(rootFileUrl.find('/store/')==0)  :
                        rootFileUrl = commands.getstatusoutput('cmsPfn ' + rootFileUrl)[1]
                    rootFile=TFile.Open(rootFileUrl)
                    try:
                        if rootFile.IsZombie() : continue
                    except:
                        continue
                    iplots=getAllPlotsFrom(dir=rootFile)
                    rootFile.Close()
                    plots=list(set(plots+iplots))

    #now plot them
    plots.sort()
    for p in plots:

        pName=p.replace('/','')
        newPlot=Plot(pName)
        
        for proc in procList :
            for desc in proc[1] :
                title=getByLabel(desc,'tag','unknown')
                isData=getByLabel(desc,'isdata',False)
                color=int(getByLabel(desc,'color',1))
                data = desc['data']
                
                h=None
                for d in data :
                    dtag = getByLabel(d,'dtag','')
                    split=getByLabel(d,'split',1)
                    
                    for segment in range(0,split) :
                        eventsFile=dtag
                        if split>1: eventsFile=dtag + '_' + str(segment)
                        rootFileUrl=inDir+'/'+eventsFile+'.root'
                        if(rootFileUrl.find('/store/')==0)  :
                            rootFileUrl = commands.getstatusoutput('cmsPfn ' + rootFileUrl)[1]
                        
                        rootFile=TFile.Open(rootFileUrl)
                        try:
                            if rootFile.IsZombie() : continue
                        except:
                            continue
                        ih=rootFile.Get(p)
                        try:
                            if ih.Integral()<=0 : continue
                        except:
                            continue
                        if h is None :
                            h=ih.Clone(pName+'_'+dtag)                    
                            h.SetDirectory(0)
                        else:
                            h.Add(ih)
                        rootFile.Close()
                if h is None: continue
                if not isData: h.Scale(lumi)
                newPlot.add(h,title,color,isData)
        newPlot.show(inDir+'/plots')

        
                    
def main():

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-i', '--in'         ,    dest='inDir'              , help='Input directory'                        , default=None)
    parser.add_option('-j', '--json'       ,    dest='json'               , help='A json file with the samples to analyze', default=None)
    parser.add_option('-l', '--lumi'       ,    dest='lumi'               , help='Re-scale to integrated luminosity [pb]',  default=1.0, type='float')
    (opt, args) = parser.parse_args()

    if opt.inDir is None or opt.json is None:
        parser.print_help()
        sys.exit(1)

    customROOTstyle()
  
    os.system('mkdir -p %s/plots'%opt.inDir)
    runPlotter(inDir=opt.inDir, jsonUrl=opt.json, lumi=opt.lumi)
    print 'Plots have been saved to %s/plots'%opt.inDir

if __name__ == "__main__":
    main()
