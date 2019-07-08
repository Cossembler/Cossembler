
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



from fmpy import read_model_description, extract, dump
from fmpy.fmi1 import *
from fmpy.fmi2 import *
from fmpy.util import plot_result, download_test_file, auto_interval
import shutil
from fmpy.simulation import Recorder, apply_start_values
from fmpy.simulation import Input as FMPYinput
from fmpy import simulate_fmu
import numpy




from cossembler.eng import Element
from cossembler.eng import VALUETYPES
from cossembler.eng import Canvas
from cossembler.eng import Demux
from cossembler.eng import TXBuffer
from cossembler.eng import RXBuffer
from cossembler.eng import Reflector
from cossembler.eng import Sink
from cossembler.eng import PRIORITY

AUTOMVAR = 10





class FMPY(Element):

    def __init__(self,name,options):
        super().__init__(name,options)
#        self.createFlexInputPin()
#        self.createPin('out', VALUETYPES.REAL)

        self.firstRun = 1

        self.inType = VALUETYPES.REAL
        self.outType = VALUETYPES.REAL

        if options['dyn'] == "full":
            if options['inType'] == "const":
                self.inType = VALUETYPES.REAL
            elif options['inType'] == "variab":
                self.inType = VALUETYPES.VECTOR
            if options['outType'] == "const":
                self.outType = VALUETYPES.REAL
            elif options['outType'] == "variab":
                self.outType = VALUETYPES.VECTOR
        elif options['dyn'] == "step":
            self.inType = VALUETYPES.REAL
            self.outType = VALUETYPES.REAL
        else:
            Exception('Error! FMPY.init(): Unsupported value for "dyn".')

        if 'fmu' in options:
            self.myFMUid = options['fmu']
        else:
            self.myFMUid = options['model_path'] + '\\' + options['model'] + '.fmu'
        if 'interval' in options:
            if 'Tstart' in options['interval']:
                self.Tstart = options['interval']['Tstart']
            else:
                self.Tstart = 0.0
            self.time = self.Tstart
            if 'Tstep' in options['interval'] and options['interval']['Tstep']>0:
                self.Tstep = options['interval']['Tstep']
            elif 'Tstop' in options['interval']:
                if options['interval']['Tstop']-self.Tstart>0:
                    self.Tstep = options['interval']['Tstop']-self.Tstart
                else:
                    Exception('Error! FMPY.init(): Tstop must be greater than Tstart.')
            else:
                Exception('Step size Tstep must be specified and greater than 0.')
            if 'Tstop' in options['interval'] and options['interval']['Tstep']>self.Tstart:
                self.Tstop = options['interval']['Tstop']
            elif 'Tstep' in options['interval']:
                if options['interval']['Tstep']> 0:
                    self.Tstop = options['interval']['Tstep']
                else:
                    Exception('Tstep must be positive.')
            else:
                Exception('Stop time Tstop must be specified and greater than start time.')
        else:
            Exception('Interval for dynamic simulation must be specified.')

        if 'solOpt' in options:
            if 'Timeout' in options['interval']:
                self.Timeout = options['interval']['Timeout']
            else:
                self.Timeout = 100
            if 'Tolerance' in options['interval']:
                self.Tolerance = options['interval']['Tolerance']
            else:
                self.Tolerance = 1e-06

        self.t_next = self.Tstart

        self.FMUinput = []
        self.FMUoutput = []

        self.modelDescription = read_model_description(self.myFMUid, validate=True)
        self.unzipdir = extract(self.myFMUid)                                  # is this one needed or I can delete it

        logger = printLogMessage

        callbacks = None
        if options['fmu_ver'] == 1:
            callbacks = fmi1CallbackFunctions()
            callbacks.logger = fmi1CallbackLoggerTYPE(logger)
            callbacks.allocateMemory = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
            callbacks.freeMemory = fmi1CallbackFreeMemoryTYPE(freeMemory)
            callbacks.stepFinished = None
        elif options['fmu_ver'] == 2:
            callbacks = fmi2CallbackFunctions()
            callbacks.logger = fmi2CallbackLoggerTYPE(logger)
            callbacks.allocateMemory = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
            callbacks.freeMemory = fmi2CallbackFreeMemoryTYPE(freeMemory)
        else:
            Exception("Please provide an existing FMU version")

        self.vrs = {}
        for variable in self.modelDescription.modelVariables:
            self.vrs[variable.name] = variable.valueReference

#        tIPSL = IPSLtranslator(self.modelDescription.modelVariables)

        self.FMUoutput = []
        for i in self.options['outputs']:
            self.FMUoutput.append(self.vrs[i])
            self.createPin('out', self.outType, i)

        self.FMUinput = []
        for i in self.options['inputs']:
            self.FMUinput.append(self.vrs[i])
            self.createPin('in', self.inType, i)

        self.FMUinit = []
        for i in self.options['x0']:
            self.FMUinit.append(self.vrs[i])
            self.createPin('in', self.inType, i, "init")
            self.setInputCondition("edge{"+i+"}",'init')


        if options['type'] == 'CS':
            if options['fmu_ver'] == 1:
                self.myFMU = FMU1Slave(guid=self.modelDescription.guid,
                                       unzipDirectory=self.unzipdir,
                                       modelIdentifier=self.modelDescription.coSimulation.modelIdentifier,
                                       instanceName=options['model'])
                self.myFMU.instantiate(functions=callbacks)

            elif options['fmu_ver'] == 2:
                self.myFMU = FMU2Slave(guid=self.modelDescription.guid,
                                     unzipDirectory=self.unzipdir,
                                     modelIdentifier=self.modelDescription.coSimulation.modelIdentifier,
                                     instanceName=options['model'])
                self.myFMU.instantiate(callbacks=callbacks)
                self.myFMU.setupExperiment(startTime=self.Tstart, tolerance=self.Tolerance)
            else:
                Exception("Please provide an existing FMU version")


        elif options['type'] == 'ME':
            if options['fmu_ver'] == 1:
                self.myFMU = FMU1Model(guid=self.modelDescription.guid,
                                     unzipDirectory=self.unzipdir,
                                     modelIdentifier=self.modelDescription.modelExchange.modelIdentifier,
                                     instanceName=options['model'])
                # instantiate FMU
                self.myFMU.instantiate(functions=callbacks)
                self.myFMU.setTime(self.Tstart)
            elif options['fmu_ver'] == 2:
                self.myFMU = FMU2Model(guid=self.modelDescription.guid,
                                     unzipDirectory=self.unzipdir,
                                     modelIdentifier=self.modelDescription.modelExchange.modelIdentifier,
                                     instanceName=options['model'])
                # instantiate FMU
                self.myFMU.instantiate(callbacks=callbacks)
                self.myFMU.setupExperiment(startTime=self.Tstart)
            else:
                Exception("Please provide an existing FMU version")

            if 'fixedStep' in options['solOpt']:
                self.fixed_step = options['solOpt']['fixedStep']
            else:
                self.fixed_step = False

        self.inEvent = FMPYinput(self.myFMU, self.modelDescription, None)


    def doFunc(self):

        inputValues = []
        FMUinputRefs = []
        if self.inType == VALUETYPES.REAL:
#            for i in range(0, len(self.input)):
#                if self.options['inmask'][i] == 0:  # The mask vector is used to separate initialization inputs (inmask=1) from regular causality="input" (inmask=0)
            for i in range(0, len(self.options['inputs'])):
                inputValues.append(self.input[i]['value'])
                FMUinputRefs.append(self.FMUinput[i])

        else:
            print("This function is not supported yet!") # figure out how to initialize fmu when the entire input vector is given

        self.myFMU.setReal(list(FMUinputRefs), list(inputValues))
#        self.myFMU.setReal(list(self.FMUinput), list(inputValues))


        if self.options['dyn'] == 'full':       #TODO: probably need to change all self.options['inputs'] into combination of self.options['inputs'] and self.options['x0']

            # setup the numpy format for specifying input variables
            dt = [('time', np.float64)]
            dt += zip(self.options['inputs'], [np.float64] * len(self.options['inputs']))

            # print the numpy format for specifying input variables just to make sure it's ok
            print(dt)

            # assign the input to input variables
        #    pom = numpy.empty(len(inputValues),dtype=dt)
            if self.options['type']=="ME":
                pom = numpy.empty(2, dtype=dt)                          # with ME it is necessary to assign first step value and last step value
                pom['time'] = [self.Tstart, self.Tstop]
            elif self.options['type']=='CS':
                pom = numpy.empty(1, dtype=dt)                          # with CS it is necessary just to assign one value for the entire period
                pom['time'] = self.Tstart

            for i in range(0,len(self.options['inputs'])):
                pom[self.options['inputs'][i]] = inputValues[i]         # assign all input values, time has been assigned previously


            print(pom)
            inputValues = pom

            result = simulate_fmu(self.options['fmu'],
                                  start_time=self.Tstart,
                                  stop_time=self.Tstop,
                                  timeout=self.Timeout,
                                  step_size=self.Tstep,
                                  input=inputValues,
                                  output=self.options['outputs'])
            print("result of simulate_fmu is "+str(result))
            print("dtype is "+str(result.dtype))

            for i in range (0,len(self.options['outputs'])):
                pom = result[self.options['outputs'][i]]
                print(pom)
                if self.outType==VALUETYPES.REAL:
                    self.output[i]['value'] = pom[-1]
                elif self.outType==VALUETYPES.VECTOR:
                    self.output[i]['value'] = pom



        elif self.options['dyn'] == 'step':

            time = self.time
            if self.options['type'] == 'CS':
                self.inEvent.apply(time)
                self.myFMU.doStep(currentCommunicationPoint=time, communicationStepSize=self.Tstep)
                self.time +=self.Tstep
            elif self.options['type'] == 'ME':
                eps = 1.0e-13
                # step ahead in time
                if self.fixed_step:
                    if time + self.Tstep < self.Tstop + eps:
                        self.t_next = time + self.Tstep
                        #            else:
                        #                break
                else:
                    if time + eps >= self.t_next:  # t_next has been reached
                        # integrate to the next grid point
                        self.t_next = round(time / self.Tstep) * self.Tstep + self.Tstep

                # gets the time of input event
                t_input_event = self.inEvent.apply(time)

                # check for input event
                input_event = t_input_event <= self.t_next

                if input_event:
                    self.t_next = t_input_event

                # check the time of next event.
                time_event = None
                if self.options['fmu_ver'] == 1:
                    time_event = self.myFMU.eventInfo.upcomingTimeEvent != fmi1False and self.myFMU.eventInfo.nextEventTime <= self.t_next
                elif self.options['fmu_ver'] == 2:
                    time_event = self.myFMU.eventInfo.nextEventTimeDefined != fmi2False and self.myFMU.eventInfo.nextEventTime <= self.t_next
                else:
                    Exception("Please provide an existing FMU version")


                if time_event and not self.fixed_step:
                    self.t_next = self.myFMU.eventInfo.nextEventTime

                state_event = None
                if self.t_next - time > eps:
                    # do one step
                    state_event, time = self.solver.step(time, self.t_next)
                else:
                    # skip
                    time = self.t_next

                # set the time
                self.myFMU.setTime(time)

                # check for step event, e.g.dynamic state selection
                step_event = None
                if self.options['fmu_ver'] == 1:
                    step_event = self.myFMU.completedIntegratorStep()
                elif self.options['fmu_ver'] == 2:
                    step_event, _ = self.myFMU.completedIntegratorStep()
                    step_event = step_event != fmi2False
                else:
                    Exception("Please provide an existing FMU version")

                # handle events
                if input_event or time_event or state_event or step_event:

                    # recorder.sample(time, force=True)

                    if input_event:
                        self.inEvent.apply(time=time, after_event=True)

                    # handle events
                    if self.options['fmu_ver'] == 1:
                        self.myFMU.eventUpdate()
                    elif self.options['fmu_ver'] == 2:
                        # handle events
                        self.myFMU.enterEventMode()

                        self.myFMU.eventInfo.newDiscreteStatesNeeded = fmi2True
                        self.myFMU.eventInfo.terminateSimulation = fmi2False

                        # update discrete states
                        while self.myFMU.eventInfo.newDiscreteStatesNeeded != fmi2False and self.myFMU.eventInfo.terminateSimulation == fmi2False:
                            self.myFMU.newDiscreteStates()

                        self.myFMU.enterContinuousTimeMode()
                    else:
                        Exception("Please provide an existing FMU version")

                    self.solver.reset(time)
            else:
                Exception("Please provide either 'ME' or 'CS' type.")

            pom = self.myFMU.getReal(list(self.FMUoutput))
            for i in range(0, len(self.FMUoutput)):
                self.output[i]['value'] = pom[i]

            print(pom)
        else:
            Exception("Simulation option 'dyn' can be either 'step' or 'full'.")




    def compile(self):

        if self.firstRun==0:
            inputValues = []
            FMUinputRefs = []
            if self.inType == VALUETYPES.REAL:
#                for i in range(0, len(self.input)):
#                    if self.options['inmask'][i] == 1:                      # The mask vector is used to separate initialization inputs (inmask=1) from regular causality="input" (inmask=0)
                for i in range(0, len(self.options['x0'])):
                    inputValues.append(self.input[i+len(self.options['inputs'])]['value'])
                    FMUinputRefs.append(self.FMUinit[i])
            else:
                print("This function is not supported yet!")  # figure out how to initialize fmu when the entire input vector is given

#            self.myFMU.setReal(list(self.FMUinput), list(inputValues))
            self.myFMU.setReal(list(FMUinputRefs), list(inputValues))


        self.firstRun -= 1
        if self.firstRun<0:
            self.firstRun = 0

        self.time = self.Tstart
        self.t_next = self.Tstart
        self.myFMU.reset()

        if self.options['type'] == 'CS':
            if self.options['fmu_ver'] == 1:
                self.myFMU.initialize()
            elif self.options['fmu_ver'] == 2:
                self.myFMU.setupExperiment(startTime=self.Tstart, tolerance=self.Tolerance)
                self.myFMU.enterInitializationMode()
                self.myFMU.exitInitializationMode()
            else:
                Exception("Please provide an existing FMU version")

        elif self.options['type'] == 'ME':
            if self.options['fmu_ver'] == 1:
                self.myFMU.initialize()
            elif self.options['fmu_ver'] == 2:
                self.myFMU.setupExperiment(startTime=self.Tstart)
                self.myFMU.enterInitializationMode()
                self.myFMU.exitInitializationMode()

                # event iteration
                self.myFMU.eventInfo.newDiscreteStatesNeeded = fmi2True
                self.myFMU.eventInfo.terminateSimulation = fmi2False

                while self.myFMU.eventInfo.newDiscreteStatesNeeded == fmi2True and self.myFMU.eventInfo.terminateSimulation == fmi2False:
                    # update discrete states
                    self.myFMU.newDiscreteStates()

                self.myFMU.enterContinuousTimeMode()
                # self.fmu.initialize()
            else:
                Exception("Please provide an existing FMU version")

            solver_args = {
                'nx': self.modelDescription.numberOfContinuousStates,
                'nz': self.modelDescription.numberOfEventIndicators,
                'get_x': self.myFMU.getContinuousStates,
                'set_x': self.myFMU.setContinuousStates,
                'get_dx': self.myFMU.getDerivatives,
                'get_z': self.myFMU.getEventIndicators
            }

            if 'solver' in self.options['solOpt']:
                if self.options['solOpt']['solver'] == 'CVODE':
                    from fmpy.sundials import CVodeSolver
                    self.solver = CVodeSolver(set_time=self.myFMU.setTime,
                                          startTime=self.Tstart,
                                          maxStep=(self.Tstop - self.Tstart) / 50.,
                                          relativeTolerance=0.001,
                                          **solver_args)

        else:
            Exception("Please provide either 'ME' or 'CS' type.")


    def decompile(self):
        self.firstRun = 1
        self.myFMU.terminate()
        self.myFMU.freeInstance()
        if self.options['type'] == 'ME':
            del self.solver
        shutil.rmtree(self.unzipdir)


