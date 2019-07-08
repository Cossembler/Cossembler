
# Cossembler - rapid prototyping tool for energy system co-simulation
# Copyright (C) 2019  M. Cvetkovic
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging

from fmpy import read_model_description

from cossembler.eng import Canvas
from cossembler.eng import WorldConnector
from cossembler.eng import VALUETYPES
from cossembler.matlaba import MATLAB
from cossembler.eng import Reflector
from cossembler.eng import Demux
from cossembler.eng import TXBuffer
from cossembler.eng import RXBuffer
from cossembler.fmpya import FMPY


class PowerFlow(Canvas,WorldConnector):

    def __init__(self, name, options):
        super().__init__(name,options)
        if (options['tool']=="MATPOWER"):
            self.myTool = MATLAB('matlabPF',VALUETYPES.MATRIX,options)
            if options['model_path'] is not "":
                self.myTool.setCommand("cd '"+options['model_path']+"'")
            self.myTool.setCommand('cs = ' + options['model'])
            if 'inputs' not in options:
                raise Exception("PowerFlow.init(): Inputs must be provided.")
            if 'outputs' not in options:
                raise Exception("PowerFlow.init(): Outputs must be provided.")
            for i in range(0, len(options['inputs'])):
                pom = options['inputs'][i]
                if pom.find("Pg")>=0:
                    if len(pom)>2:
                        s = pom[pom.find('Pg') + 3:pom.find(')')]
                        self.myTool.setCommand("cs.gen("+s+",2)=Pg"+s+";")
                        self.myTool.setCommand("Pg" + s)                        # only for the sake of output
                        self.myTool.setVar("Pg" + s)
                    else:
                        self.myTool.setCommand("Pg")                            # only for the sake of output
                        self.myTool.setCommand("cs.gen(:,2)=Pg;")
                        self.myTool.setVar("Pg")
                if pom.find("Vg")>=0:
                    if len(pom)>2:
                        s = pom[pom.find('Vg') + 3:pom.find(')')]
                        self.myTool.setCommand("cs.gen("+s+",6)=Vg"+s+";")
                        self.myTool.setCommand("Vg" + s)                        # only for the sake of output
                        self.myTool.setVar("Vg" + s)
                    else:
                        self.myTool.setCommand("cs.gen(:,6)=Vg;")
                        self.myTool.setVar("Vg")
                if pom.find("Pd")>=0:
                    if len(pom)>2:
                        s = pom[pom.find('Pd') + 3:pom.find(')')]
                        self.myTool.setCommand("cs.bus("+s+",3)=Pd"+s+";")
                        self.myTool.setCommand("Pd"+s)                          # only for the sake of output
                        self.myTool.setVar("Pd"+s)
                    else:
                        self.myTool.setCommand("cs.bus(:,3)=Pd;")
                        self.myTool.setVar("Pd")
                if pom.find("Qd")>=0:
                    if len(pom)>2:
                        s = pom[pom.find('Qd') + 3:pom.find(')')]
                        self.myTool.setCommand("cs.bus("+s+",4)=Qd"+s+";")
                        self.myTool.setCommand("Qd" + s)                        # only for the sake of output
                        self.myTool.setVar("Qd" + s)
                    else:
                        self.myTool.setCommand("cs.bus(:,4)=Qd")
                        self.myTool.setVar("Qd")
                if pom == "slack":
                    self.myTool.setCommand("cs.bus(cs.bus(:,2)==3,2)=2;")
                    self.myTool.setCommand("cs.bus(sl,2)=3;")
                    self.myTool.setVar("sl")
            self.myTool.setCommand("pfsol=runpf(cs)")
            self.myTool.output.clear()
            for i in range(0,len(options['outputs'])):
                pom = options['outputs'][i]
                if pom.find("Vm")>=0:
                    if len(pom) > 2:
                        s = pom[pom.find('Vm') + 3:pom.find(')')]
                        self.myTool.setOutCommand("pfsol.bus("+s+",8)'")
                        self.myTool.createPin('out', VALUETYPES.REAL, name + ".Vm"+s)
                    else:
                        self.myTool.setOutCommand("pfsol.bus(:,8)'")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Vm")
                if pom.find("Va")>=0:
                    if len(pom) > 2:
                        s = pom[pom.find('Va') + 3:pom.find(')')]
                        self.myTool.setOutCommand("pfsol.bus("+s+",9)'")
                        self.myTool.createPin('out', VALUETYPES.REAL, name + ".Va"+s)
                    else:
                        self.myTool.setOutCommand("pfsol.bus(:,9)'")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Va")
                if pom.find("Pd")>=0:
                    if len(pom) > 2:
                        s = pom[pom.find('Pd') + 3:pom.find(')')]
                        self.myTool.setOutCommand("pfsol.bus("+s+",3)'")
                        self.myTool.createPin('out', VALUETYPES.REAL, name + ".Pd"+s)
                    else:
                        self.myTool.setOutCommand("pfsol.bus(:,3)'")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Pd")
                if pom.find("Qd")>=0:
                    if len(pom) > 2:
                        s = pom[pom.find('Qd') + 3:pom.find(')')]
                        self.myTool.setOutCommand("pfsol.bus("+s+",4)'")
                        self.myTool.createPin('out', VALUETYPES.REAL, name + ".Qd"+s)
                    else:
                        self.myTool.setOutCommand("pfsol.bus(:,4)'")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Qd")
                if pom.find("Pg")>=0:
                    if len(pom) > 2:
                        s = pom[pom.find('Pg') + 3:pom.find(')')]
                        self.myTool.setOutCommand("pfsol.gen("+s+",2)'")
                        self.myTool.createPin('out', VALUETYPES.REAL, name + ".Pg"+s)
                    else:
                        self.myTool.setOutCommand("pfsol.gen(:,2)'")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Pg")
                if pom.find("Qg")>=0:
                    if len(pom) > 2:
                        s = pom[pom.find('Qg') + 3:pom.find(')')]
                        self.myTool.setOutCommand("pfsol.gen("+s+",3)'")
                        self.myTool.createPin('out', VALUETYPES.REAL, name + ".Qg"+s)
                    else:
                        self.myTool.setOutCommand("pfsol.gen(:,3)'")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Qg")
                if options['outputs'][i] == "Pflow":
                    self.myTool.setOutCommand("[pfsol.branch(:,14) pfsol.branch(:,16)]'")
                    self.myTool.createPin('out',VALUETYPES.MATRIX,name+".Pflow")
                if options['outputs'][i] == "Qflow":
                    self.myTool.setOutCommand("[pfsol.branch(:,15) pfsol.branch(:,17)]'")
                    self.myTool.createPin('out',VALUETYPES.MATRIX,name+".Qflow")
                if options['outputs'][i] == "PQloss":
                    self.myTool.setOutCommand("[pfsol.branch(:,14)+pfsol.branch(:,16) pfsol.branch(:,15)+pfsol.branch(:,17)]'")
                    self.myTool.createPin('out',VALUETYPES.MATRIX,name+".PQloss")

        for i in range(0,len(options['inputs'])-1):
            self.myTool.createFlexInputPin()

        self.add_element(self.myTool)

    def connect(self, right, pinout, pinin):
        super().connect(right, pinout, pinin)
        self.myTool.connect(right, pinout, pinin)

    def accept(self, pinin):
        return self.myTool

    def connectToTheWorld(self):
        self.myTool.connectToTheWorld()

    def disconnectFromTheWorld(self):
        self.myTool.disconnectFromTheWorld()

    def doFunc(self):
        super().doFunc()


class SCUC(Canvas,WorldConnector):

    def __init__(self, name, options):
        super().__init__(name,options)
        if (options['tool']=="MATPOWER"):
            self.myTool = MATLAB('matlabSCUC',VALUETYPES.MATRIX,options)
            if options['model_path'] is not "":
                self.myTool.setCommand("cd '"+options['model_path']+"'")
            self.myTool.setCommand('cs = ' + options['model']+';')
            self.myTool.setCommand('mpc = loadcase(cs);')
            self.myTool.setCommand('indout = mpc.gen(:,1);')
            self.myTool.setCommand('xgd = loadxgendata('+options['model']+'_ex_xgd_uc, mpc);')
            self.myTool.setCommand('pom = '+options['model']+'_ex_wind_uc;')
            self.myTool.setCommand('pom = pom.gen(:, 1);')
            self.myTool.setCommand('[iwind, mpc, xgd] = addwind('+options['model']+'_ex_wind_uc, mpc, xgd);')
            self.myTool.setCommand('profiles = getprofiles('+options['model']+'_ex_wind_profile, iwind);')
            self.myTool.setCommand('profiles = getprofiles('+options['model']+'_ex_load_profile, profiles);')
            self.myTool.setCommand("indin = extractfield(profiles,'rows');")
            self.myTool.setCommand('indin(size(pom)) = pom;')
            self.myTool.setCommand('Pren12')
            if 'inputs' not in options:
                raise Exception("PowerFlow.init(): Inputs must be provided.")
            if 'outputs' not in options:
                raise Exception("PowerFlow.init(): Outputs must be provided.")
            for i in range(0, len(options['inputs'])):
                pom = options['inputs'][i]
                if pom.find("Pd")>=0:
                    if len(pom)>2:
                        s = pom[pom.find('Pd') + 3:pom.find(')')]
                        self.myTool.setCommand("profiles(indin=="+s+").values=Pd"+s+";")
                        self.myTool.setVar("Pd" + s)
                    else:
                        self.myTool.setCommand("profiles(length(iwind)+1:length(profiles)).values=Pd;")
                        self.myTool.setVar("Pd")
                if pom.find("Pren")>=0:
                    if len(pom)>4:
                        s = pom[pom.find('Pren') + 5:pom.find(')')]
                        self.myTool.setCommand("profiles(indin=="+s+").values=Pren"+s+";")
                        self.myTool.setVar("Pren" + s)
                    else:
                        self.myTool.setCommand("profiles(1:length(iwind)).values=Pren;")
                        self.myTool.setVar("Pren")
                if pom == "slack":
                    self.myTool.setCommand("cs.bus(cs.bus(:,2)==3,2)=2;")
                    self.myTool.setCommand("cs.bus(sl,2)=3;")
                    self.myTool.setVar("sl")
            self.myTool.setCommand("nt = size(profiles(1).values, 1);")
            self.myTool.setCommand("mdi = loadmd(mpc, nt, xgd, [], [], profiles);")
            self.myTool.setCommand("mdo = most(mdi);")
            self.myTool.output.clear()
            for i in range(0,len(options['outputs'])):
                pom = options['outputs'][i]
                if pom.find("Pg") >= 0:
                    if len(pom) > 2:
                        s = pom[pom.find('Pg') + 3:pom.find(')')]
                        self.myTool.setOutCommand("mdo.results.Pc(indout=="+s+",:)")
                        self.myTool.createPin('out',VALUETYPES.VECTOR,name+".Pg"+s)
                    else:
                        self.myTool.setOutCommand("mdo.results.Pc(1:length(indout),:)")
                        self.myTool.createPin('out',VALUETYPES.MATRIX,name+".Pg")

        for i in range(0,len(options['inputs'])-1):
            self.myTool.createFlexInputPin()

        self.add_element(self.myTool)

    def connect(self, right, pinout, pinin):
        super().connect(right, pinout, pinin)
        self.myTool.connect(right, pinout, pinin)

    def accept(self, pinin):
        return self.myTool

    def connectToTheWorld(self):
        self.myTool.connectToTheWorld()

    def disconnectFromTheWorld(self):
        self.myTool.disconnectFromTheWorld()

    def doFunc(self):
        super().doFunc()


class FMPYtranslator(object):

    # '_0' or '_init' mark initialization variable,
    # '_time' or '_t' marks a signal,
    # no mark means one value for input that is not an initial value and is not a signal either but a constant input throughout the run

    def __init__(self,myLib,type="DEFAULT"):

        self.myType = type
        self.myVarLibrary = myLib

    def isInit(self,varName):
        if not isinstance(varName,str):
            #print("Error! IPSLTranslate.isInit(): varName must be a string")
            logging.error("Error! IPSLTranslate.isInit(): varName must be a string")
            return
        init = False
        if varName.find("_0")>=0 or varName.find("_init")>=0:
            init = True
        return init

    def isSignal(self,varName):
        if not isinstance(varName,str):
            #print("Error! IPSLTranslate.isSignal(): varName must be a string")
            logging.error("Error! IPSLTranslate.isSignal(): varName must be a string")
            return
        sig = False
        if varName.find("_time")>=0 or varName.find("_t")>=0:
            sig = True
        return sig


    def translate(self, varName):
        if not self.myVarLibrary:
            #print("Error! IPSLTranslate.translate(): myVarLibrary must be specified")
            logging.error("Error! IPSLTranslate.translate(): myVarLibrary must be specified")
            return
        if not isinstance(varName, str):
            #print("Error! IPSLTranslate.translate(): varName must be a string")
            logging.error("Error! IPSLTranslate.translate(): varName must be a string")
            return

        if varName.find("_0")!=-1:
            varName = varName.replace("_0","")
        if varName.find("_init")!=-1:
            varName = varName.replace("_init","")
        if varName.find("_time")!=-1:
            varName = varName.replace("_time","")
        if varName.find("_t")!=-1:
            varName = varName.replace("_t","")

        outNames = []
        for variable in self.myVarLibrary:
            if variable.name == varName:
                outNames.append(variable.name)
                return outNames


class IPSLtranslator(FMPYtranslator):

    def __init__(self,myLib):
        super().__init__(myLib,"IPSL")

    def _myLen(self,e):
        return len(e)

    def getIndex(self,tranIn):
        import re
        spk = []
        for j in tranIn:
            k = re.findall("\d+", j)
            spk.append(int(k[0]))
        return spk

    def translate(self, varName):
        if not self.myVarLibrary:
            #print("Error! IPSLTranslate.translate(): myVarLibrary must be specified")
            logging.error("Error! IPSLTranslate.translate(): myVarLibrary must be specified")
            return
        if not isinstance(varName,str):
            #print("Error! IPSLTranslate.translate(): varName must be a string")
            logging.error("Error! IPSLTranslate.translate(): varName must be a string")
            return

        outNames = []
        for variable in self.myVarLibrary:
            if variable.name==varName:
                outNames.append(variable.name)
                return outNames


        init = False
        signal = False
        # remove additions for initialization or for signal
        if varName.find("_0")!=-1:
            varName = varName.replace("_0","")
            init = True
        if varName.find("_init")!=-1:
            varName = varName.replace("_init","")
            init = True
        if varName.find("_time")!=-1:
            varName = varName.replace("_time","")
            signal = True
        if varName.find("_t")!=-1:
            varName = varName.replace("_t","")
            signal = True



#        outBusNum = []
        if init:
            if varName=="Pg":
                for variable in self.myVarLibrary:
                    if (variable.name.find("gen")>=0 or variable.name.find("Gen")>=0) and variable.name.find("P_0")>=0:
                        outNames.append(variable.name)
                for pom in outNames:                                            # remove all gen1.gen.P_0 enteries
                    if pom.find(".gen.")>=0:
                        outNames.remove(pom)
                outNames.sort()                                                 # sort by number:  load1, load11, load12, load2, load3
                outNames.sort(key=self._myLen)                                  # sort by length:  load1, load2, load3, load11, load12
            elif varName=="Qg":
                for variable in self.myVarLibrary:
                    if (variable.name.find("gen")>=0 or variable.name.find("Gen")>=0) and variable.name.find("Q_0")>=0:
                        outNames.append(variable.name)
                for pom in outNames:                                            # remove all gen1.gen.P_0 enteries
                    if pom.find(".gen.") >= 0:
                        outNames.remove(pom)
                outNames.sort()                                                 # sort by number:  load1, load11, load12, load2, load3
                outNames.sort(key=self._myLen)                                  # sort by length:  load1, load2, load3, load11, load12
            elif varName=="Pd":
                for variable in self.myVarLibrary:
                    if (variable.name.find("Load")>=0 or variable.name.find("load")>=0) and variable.name.find("P_0")>=0:
                        outNames.append(variable.name)
    #                    s = variable[4:variable.find('.')]
    #                    outBusNum.append(int(s))
                utol = outNames.copy()
                for i in range(0,len(outNames)):
                    if outNames[i][0]=="L":
                        outNames[i] = outNames[i].replace("L","l")
                outNames.sort()                                               # sort by number:  load1, load11, load12, load2, load3
                outNames.sort(key=self._myLen)                                # sort by length:  load1, load2, load3, load11, load12
                for i in range(0,len(outNames)):
                    captrep = True
                    for j in utol:
                        if outNames[i]==j:
                            captrep = False
                            break
                    if captrep:
                        outNames[i] = outNames[i].replace("l","L")
            elif varName=="Qd":
                for variable in self.myVarLibrary:
                    if (variable.name.find("Load")>=0 or variable.name.find("load")>=0) and variable.name.find("Q_0")>=0:
                        outNames.append(variable.name)
                utol = outNames.copy()
                for i in range(0,len(outNames)):
                    if outNames[i][0]=="L":
                        outNames[i] = outNames[i].replace("L", "l")
                outNames.sort()                                               # sort by number:  load1, load11, load12, load2, load3
                outNames.sort(key=self._myLen)                                # sort by length:  load1, load2, load3, load11, load12
                for i in range(0,len(outNames)):
                    captrep = True
                    for j in utol:
                        if outNames[i]==j:
                            captrep = False
                            break
                    if captrep:
                        outNames[i] = outNames[i].replace("l", "L")
    #        if varName=="Vm":
    #            for variable in modelVariables:
    #                if variable.find("load") and variable.find("Q_0"):
    #                    outNames.append(variable)
        else:
            import re
            s1 = varName
            s2 = varName
            if varName.find('Pg')>=0 or varName.find('Qg')>=0:
                s1 = 'gen'
                s2 = 'Gen'
                k = re.findall("\d+", varName)
                if len(k)>0:
                    s1 = s1+k[0]
                    s2 = s2+k[0]
            if varName.find('Pd')>=0 or varName.find('Qd')>=0:
                s1 = 'load'
                s2 = 'Load'
                k = re.findall("\d+", varName)
                if len(k)>0:
                    s1 = s1+k[0]
                    s2 = s2+k[0]
            for variable in self.myVarLibrary:
                if variable.causality=="input":
                    if variable.name.find(s1)>=0 or variable.name.find(s2)>=0:
                        outNames.append(variable.name)
            if not outNames:
                for variable in self.myVarLibrary:
                    if variable.name.find(s1) >= 0 or variable.name.find(s2) >= 0:
                        outNames.append(variable.name)

        return outNames


class DynamicSimulationNoInit(Canvas):

    def __init__(self, name, options):
        super().__init__(name, options)
        if (options['tool'] == "IPSL") or (options['tool'] == "FMU"):
            if 'inputs' not in options:
                raise Exception("DynamicSimulationNoInit.init(): Inputs must be provided.")
            if 'outputs' not in options:
                raise Exception("DynamicSimulationNoInit.init(): Outputs must be provided.")

            if 'fmu' in options:
                myFMUid = options['fmu']
            else:
                myFMUid = options['model_path'] + '\\' + options['model'] + '.fmu'
            modelDescription = read_model_description(myFMUid, validate=True)

            if options['tool'] == "IPSL":
                tIPSL = IPSLtranslator(modelDescription.modelVariables)
            else:
                tIPSL = FMPYtranslator(modelDescription.modelVariables)

            actualInputs = []
            actualx0s = []
            self.inBuffList = []
            for i in self.options['inputs']:
                tranIn = tIPSL.translate(i)
                if tIPSL.isSignal(i):
                    # create buffer for each input
                    pom = TXBuffer(name + "->" + i)
                    pom.setCounterCondition(
                        (options['interval']['Tstop'] - options['interval']['Tstart']) / options['interval'][
                            'Tstep'])
                    self.add_element(pom)
                    self.inBuffList.append(pom)
                    actualInputs.append(tranIn)
                elif tIPSL.isInit(i):
                    actualx0s.append(tranIn)
                else:
                    pom = Reflector(name + "->" + i)
                    self.add_element(pom)
                    self.inBuffList.append(pom)
                    actualInputs.append(tranIn)

            l = len(self.options['inputs'])
            i = 0
            for j in range(0,l):
                if tIPSL.isInit(self.options['inputs'][i]):
                    pom = self.options['inputs'].pop(i)
                    self.options['inputs'].append(pom)
                else:
                    i+=1


            actualInputsList = [item for sublist in actualInputs for item in sublist]
            actualx0List = [item for sublist in actualx0s for item in sublist]

            actualOutputs = []
            self.outBuffList = []
            for i in self.options['outputs']:
                tranIn = tIPSL.translate(i)
                if tIPSL.isSignal(i):
                    # create buffer for each output
                    pom = RXBuffer(name + "->" + i)
                    self.add_element(pom)
                    self.outBuffList.append(pom)
                    actualOutputs.append(tranIn)
                else:
                    pom = Reflector(name + "->" + i)
                    self.add_element(pom)
                    self.outBuffList.append(pom)
                    actualOutputs.append(tranIn)

            actualOutputsList = [item for sublist in actualOutputs for item in sublist]

            FMPYopt = options.copy()
            FMPYopt['inputs'] = actualInputsList
            FMPYopt['x0'] = actualx0List
            FMPYopt['outputs'] = actualOutputsList

            self.myTool = FMPY(name + '->FMPYdyn', FMPYopt)
            self.add_element(self.myTool)

            for i in range(0,len(self.inBuffList)):
                self.inBuffList[i].connect(self.myTool,1,i+1)

            for i in range(0,len(self.outBuffList)):
                self.myTool.connect(self.outBuffList[i],i+1,1)


            # self.inBuffList = []
            # for i in range(0, len(options['inputs'])):
            #     if tIPSL.isSignal(options['inputs'][i]):
            #         # create buffer for each input
            #         pom = TXBuffer(name + "->" + options['inputs'][i])
            #         pom.setCounterCondition(
            #             (options['interval']['Tstop'] - options['interval']['Tstart']) / options['interval'][
            #                 'Tstep'])
            #         self.add_element(pom)
            #         self.inBuffList.append(pom)
            #         for j in range(0, spi[i]):
            #             pom.connect(self.myTool, j + 1, cntTool)
            #             cntTool += 1
            #     else:
            #         pom = Reflector(name + "->" + options['inputs'][i])
            #         self.add_element(pom)
            #         self.inBuffList.append(pom)
            #         for j in range(0, spi[i]):
            #             pom.connect(self.myTool, j + 1, cntTool)
            #             cntTool += 1

            # self.outBuffList = []
            # for i in range(0, len(options['outputs'])):
            #     if tIPSL.isSignal(options['outputs'][i]):
            #         # create buffer for each input
            #         pom = RXBuffer(name + "->" + options['outputs'][i])
            #         self.add_element(pom)
            #         self.outBuffList.append(pom)
            #         self.myTool.connect(pom,cntout,1)
            #         cntout +=1
            #     else:
            #         pom = Reflector(name + "->" + options['outputs'][i])
            #         self.add_element(pom)
            #         self.outBuffList.append(pom)
            #         self.myTool.connect(pom, cntout, 1)
            #         cntout += 1

    def connect(self, right, pinout, pinin):
        super().connect(right, pinout, pinin)
        if isinstance(pinout,str):
            pom = self.translate(pinout,'out')
            if pom==-1:
                pinout = self.myCanvas.translate(pinout,'out')
            else:
                pinout = pom
        self.outBuffList[pinout-1].connect(right, 1, pinin)


    def accept(self, pinin):
#        return {'elem': self.inBuffList[pinin - 1], 'pin': 1}
        if pinin<=len(self.inBuffList):
            return {'elem': self.inBuffList[pinin - 1], 'pin': 1}
        else:
            return {'elem': self.myTool, 'pin': pinin}


    def compile(self):
        super().compile()
        for i in self.inBuffList:
            i.resetCondition()
            i.setCounterCondition((self.options['interval']['Tstop'] - self.options['interval']['Tstart']) / self.options['interval']['Tstep'])

#            self.myBuffers[i].compile()  # really not needed since Canvas.compile() calls all elements to compile


    def doFunc(self):
#        if self.initMyTool:
#            self.myTool.setInitializationCondition()
        super().doFunc()



class DynamicSimulation(Canvas):

    def __init__(self, name, options):
        super().__init__(name, options)

        if (options['tool'] == "IPSL") or (options['tool'] == "FMU"):
            if 'inputs' not in options:
                raise Exception("DynamicSimulation.init(): Inputs must be provided.")
            if 'outputs' not in options:
                raise Exception("DynamicSimulation.init(): Outputs must be provided.")

            if 'fmu' in options:
                myFMUid = options['fmu']
            else:
                myFMUid = options['model_path'] + '\\' + options['model'] + '.fmu'
            modelDescription = read_model_description(myFMUid, validate=True)

            if options['tool'] == "IPSL":
                tIPSL = IPSLtranslator(modelDescription.modelVariables)
            else:
                tIPSL = FMPYtranslator(modelDescription.modelVariables)

            import copy
            DSnoInitopt = copy.deepcopy(options)

            self.inElemList = []
            for i in options['inputs']:
                tranIn = tIPSL.translate(i)
                if len(tranIn)>1:
                    ind = DSnoInitopt['inputs'].index(i)
                    DSnoInitopt['inputs'].pop(ind)
                    for j in reversed(tranIn):
                        DSnoInitopt['inputs'].insert(ind,j)
                    #pom = Demux(name + '->' + i, len(tranIn))

                    if i.find("Pg")>=0 or i.find("Qg")>=0:
                        pom = Demux(name + '->' + i, len(tranIn))
                    elif i.find("Pd")>=0 or i.find("Qd")>=0:
                        ind = tIPSL.getIndex(tranIn)
                        pom = Demux(name + '->' + i, len(tranIn), VALUETYPES.REAL, {'ind' : ind})

                    self.add_element(pom)
                    self.inElemList.append(pom)
                else:
                    pom = Reflector(name + '->' + i)
                    self.add_element(pom)
                    self.inElemList.append(pom)
                    if tIPSL.isSignal(i):
                        self.setInputCondition("edge{" + i + "}", 'init')

            actualOutputs = DSnoInitopt['inputs'].copy()


            self.myTool = DynamicSimulationNoInit(name + '->DSnoInit', DSnoInitopt)
            self.add_element(self.myTool)

            cnt = 0
            for i in range(0,len(self.inElemList)):
                for j in range(0,len(self.inElemList[i].output)):
                    self.inElemList[i].connect(self.myTool,j+1,actualOutputs[cnt])
                    cnt += 1






    def connect(self, right, pinout, pinin):
        super().connect(right, pinout, pinin)
        self.myTool.connect(right, pinout, pinin)

    def accept(self, pinin):
        return {'elem': self.inElemList[pinin - 1], 'pin': 1}

    def compile(self):
        super().compile()
        # for i in range(0, len(self.myBuffers)):
        #     self.myBuffers[i].resetCondition()
        #     self.myBuffers[i].compile()
        #     self.myBuffers[i].setCounterCondition(
        #         (self.options['interval']['Tstop'] - self.options['interval']['Tstart']) / self.options['interval'][
        #             'Tstep'])

    def doFunc(self):
        # if self.initMyTool:
        #     self.myTool.setInitializationCondition()
        super().doFunc()
