
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


import shutil
from cossembler.eng import Canvas
from cossembler.eng import Source
from cossembler.eng import Sink
from cossembler.fmpya import FMPY
from cossembler.app import DynamicSimulation
from cossembler.app import DynamicSimulationNoInit
from cossembler.eng import VALUETYPES


TEST = {
    'MonteCarlo'    : False,          # testing DynamicSimulation block but in a loop with random sources to create Monte Carlo stochastic simulation
    'timeSpanWithX0': True,         # testing DynamicSimulation block (dynamic simulation for entire time period with initialization at start)
    'timeSpan'      : False,        # testing DynamicSimulationNoInit block (dynamic simulation for entire time period without initialization)
    'singleStep'    : False         # testing FMPY block (single step of dynamic simulation; only tested for FMU for co-simulation version 2)
}

FMPYoptions = {
     'solOpt' : {'solver' : 'CVODE', 'fixedStep' : False, 'Timeout': 180, 'Tolerance': 1e-06},
     'dyn' : 'step', # two possibilities, step and full; only step is working for now
     'interval' : {'Tstart': 0.0, 'Tstop':1.0, 'Tstep':1.0e-02},  # if dyn=full and inType=variab or outType=variab then Tstep is used to determine the proper size of input and output vectors (user must specify these vectors of size (Tstop-Tstart)/Tstep+1)
     'fmu' : r'...\Cossembler\tests\transferFx.fmu',
     'model' : 'transferFx',
     'model_path' : r'...\Cossembler\tests',
     'fmu_ver' : 2,
     'type' : "CS"
 }

def Main():

    elemFM = None

    try:

        wrld = Canvas('world')

        if TEST['MonteCarlo']:                                  # the output is random :)

            FMPYoptions['tool'] = 'FMU'                         # 'FMU' for generic FMUs, 'IPSL' for OpenIPSL
            FMPYoptions['inputs'] = ['u_t']                     # Cossembler convention:
                                                                # '_0' or '_init' mark initialization variable and FMU will be initialized with it,
                                                                # '_time' or '_t' marks a variable signal,
                                                                # no mark means one value for input without change during FMU integration
                                                                # Note: the rest of the variable name must be the same as defined inside FMU
                                                                # Note: the variable inside FMU must be declared as "input" in order to be used as input of a block in Cossembler
            FMPYoptions['outputs'] = ['y']                      # the name must match the name of the variable inside FMU

            elemFM = DynamicSimulation('DynSim', FMPYoptions)

            wnopt = {'rand': "gauss", 'mu': 0, 'sigma': 0.1, 'len': 100, 'multistep': False}
            elemSource = Source('Source', [], VALUETYPES.VECTOR, wnopt)
            elemSink = Sink("Sink")

            elemSource.setCounterCondition(3)

            wrld.add_element(elemSource)
            wrld.add_element(elemFM)
            wrld.add_element(elemSink)

            elemSource.connect(elemFM, 1, 'u_t')
            elemFM.connect(elemSink, 1, 1)


        elif TEST['timeSpanWithX0']:                            # the output should be 5.0, but this test is not operating properly

            FMPYoptions['tool'] = 'FMU'                         # 'FMU' for generic FMUs, 'IPSL' for OpenIPSL
            FMPYoptions['inputs'] = ['u_0']                     # Cossembler convention:
                                                                # '_0' or '_init' mark initialization variable and FMU will be initialized with it,
                                                                # '_time' or '_t' marks a variable signal,
                                                                # no mark means one value for input without change during FMU integration
                                                                # Note: the rest of the variable name must be the same as defined inside FMU
                                                                # Note: the variable inside FMU must be declared as "input" in order to be used as input of a block in Cossembler
            FMPYoptions['outputs'] = ['y']                      # the name must match the name of the variable inside FMU

            elemFM = DynamicSimulation('DynSim', FMPYoptions)

            elemSource = Source('Source', 5.0)
            elemSink = Sink("Sink")

            wrld.add_element(elemSource)
            wrld.add_element(elemFM)
            wrld.add_element(elemSink)

            elemSource.connect(elemFM, 1, 'u_0')                # tried with firstOrder1.y_start instead of u but it still does not work
            elemFM.connect(elemSink, 1, 1)

        elif TEST['timeSpan']:                                  # output of this simulation run should be 1.6339676587267702

            FMPYoptions['tool'] = 'FMU'                         # 'FMU' for generic FMUs, 'IPSL' for OpenIPSL
            FMPYoptions['inputs'] = ['u_t']                     # Cossembler convention:
                                                                # '_0' or '_init' mark initialization variable and FMU will be initialized with it,
                                                                # '_time' or '_t' marks a variable signal,
                                                                # no mark means one value for input without change during FMU integration
                                                                # Note: the rest of the variable name must be the same as defined inside FMU
                                                                # Note: the variable inside FMU must be declared as "input" in order to be used as input of a block in Cossembler
            FMPYoptions['outputs'] = ['y']                      # the name must match the name of the variable inside FMU

            elemFM = DynamicSimulationNoInit('DynSimNoInit', FMPYoptions)

            import numpy as np
            elemSource = Source('Source', np.linspace(2.0, 2.99, 100), VALUETYPES.VECTOR)
            elemSink = Sink("Sink")

            wrld.add_element(elemSource)
            wrld.add_element(elemFM)
            wrld.add_element(elemSink)

            elemSource.connect(elemFM, 1, 'u_t')
            elemFM.connect(elemSink,1,1)


        elif TEST['singleStep']:                                # this should make one step but the test does not go through for some reason

            FMPYoptions['tool'] = 'FMU'                         # 'FMU' for generic FMUs, 'IPSL' for OpenIPSL
            FMPYoptions['inputs'] = ['u']                       # Cossembler convention:
                                                                # '_0' or '_init' mark initialization variable and FMU will be initialized with it,
                                                                # '_time' or '_t' marks a variable signal,
                                                                # no mark means one value for input without change during FMU integration
                                                                # Note: the rest of the variable name must be the same as defined inside FMU
                                                                # Note: the variable inside FMU must be declared as "input" in order to be used as input of a block in Cossembler
            FMPYoptions['outputs'] = ['y']                      # the name must match the name of the variable inside FMU


            elemFM = FMPY('FMPY', FMPYoptions)

            elemSource = Source('Source', 5.0)
            elemSink = Sink("Sink")

            wrld.add_element(elemSource)
            wrld.add_element(elemFM)
            wrld.add_element(elemSink)

            elemSource.connect(elemFM, 1, 'u')
            elemFM.connect(elemSink, 1, 1)


        wrld.start()

    except Exception as e:
        if elemFM:
            if TEST['MonteCarlo']:
                elemFM.myTool.myTool.myFMU.terminate()
                elemFM.myTool.myTool.myFMU.freeInstance()
                shutil.rmtree(elemFM.myTool.myTool.unzipdir)
            else:
                elemFM.myTool.myFMU.terminate()
                elemFM.myTool.myFMU.freeInstance()
                shutil.rmtree(elemFM.myTool.unzipdir)
        print(e)

Main()
