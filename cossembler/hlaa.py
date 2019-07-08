
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

import sys
import time
import traceback
import hla.rti as rti
from cossembler.eng import Element
from cossembler.eng import Canvas
from cossembler.eng import WorldConnector
from cossembler.eng import EMPTYMSG

class DEFAULTS:
    DEFAULT_PRECISION = 4
    RTI_VERSION = 13
    CERTI_VER = 4 # alternative is 3.5

# needed for synchronization before the start of execution of the simulation
class SynchState:
    NotInit = 0
    RegisterRequested = 1
    if (DEFAULTS.CERTI_VER==4):
        Registered = 4
        Announced = 2
    else:
        Registered = 2
        Announced = 4
    Achieved = 8
    Synched = 16


# these are the indices of values in the received message dictionaries
class RXMSG_INDEX:
    TIME = 0
    NAME = 1
    VALUE = 2


# these are the indices of values in the sent message dictionaries
class TXMSG_INDEX:
    NAME = 0
    VALUE = 1


# these are not used in the current version of the code
class TimeState:
    NotInit = 0  # the federate does not send time stamped messages
    Regulated = 1  # the federate sends time-stamped messages
    Constrained = 2  # the federate receives time-stamped messages


def setDefaults(path):
    f = open(path)
    l = f.readline()
    d = eval(l)
    if len(d) == 0:
        return

    for name, value in d.items():
        if name == "DEFAULT_PRECISION":
            DEFAULTS.DEFAULT_PRECISION = value
        elif name == "RTI_VERSION":
            DEFAULTS.RTI_VERSION = value

    f.close()


##################################################################################################################
## This class is a base class for an HLA federate
## It hides the HLA specific calls and callbacks from the user
class BaseFederate(object):
    '''
    classdocs
    '''

    def __init__(self, federateName):
        '''
        Constructor
        '''

        self.synchState = SynchState.NotInit
        self.granted = False
        self.time = 0.0
        self.timeState = TimeState.NotInit      # these are set but not used in the code

        # object registration
        self.regObjects = []                    # stores handles to registered message object instances (for sending)
        self.otherObjects = []                  # stores handles on message objects registered by other federates (for receiving)

        self.opObjectNames = []                 # stores names of registered object instances (one to one mapping with previous) the names are not used for anything
        self.nameReserved = False               # not used

        # class declaration
        self.opClassHandles = []                # contains handles on class declarations that are set during publish and used during registerObjectInstance
        self.ipClassHandle = None               # used locally in subscribe and thus shown here only for symmetry sake (not really needed as a class property)

        # class declaration
        # and message passing
        self.ipHandles = {}                     # contains handles on attribute declarations and is used for subscribe and reflectAttributeValues
        self.opHandles = {}                     # contains handles on attribute declarations and is used for publish and updateAttributes

        # self.quantizers = {}
        self.subscriptions = {}
        self.publications = {}

        print("Create ambassador")
        self.rtiaReference = rti.RTIAmbassador()
        print(self.rtiaReference)

        self.federateName = federateName
        self.federationName = None              # needed to start/destroy federation
        self.creator = False                    # needed to synchronize the start of co-simulation execution
        self.lookAhead = 0                      # ???

        self.pendingUpdates = []                # message buffer for incoming messages
        self.TsoMsgReceived = False             # true if time stamped message is received (not used)

        self.test = False

    ###########################################################################################################################
    # the setter and getter of myObject are only used when calling updateAttributeValues and their use is not really clear
    # regObjects are used directly on many places

    @property
    def myObject(self):
        if len(self.regObjects) == 0:
            return None
        return self.regObjects[0]

    @myObject.setter
    def myObject(self, value):
        if len(self.regObjects) == 0:
            self.regObjects.append(value)
        else:
            self.regObjects[0] = value

    @myObject.getter
    def myObject(self):
        if len(self.regObjects) == 0:
            return None
        return self.regObjects[0]

    ###########################################################################################################################
    # the setter and getter of opObjectName are never used
    # opObjectNames are used directly on many places

    @property
    def opObjectName(self):
        if len(self.opObjectNames) == 0:
            return None
        return self.opObjectNames[0]

    @opObjectName.setter
    def opObjectName(self, value):
        if len(self.opObjectNames) == 0:
            self.opObjectNames.append(value)
        else:
            self.opObjectNames[0] = value

    @opObjectName.getter
    def opObjectName(self):
        if len(self.opObjectNames) == 0:
            return None
        return self.opObjectNames[0]

    ###########################################################################################################################
    # the setter and getter of opClassHandle are only used when calling publish
    # opClassHandles are used directly on many places

    @property
    def opClassHandle(self):
        if len(self.opClassHandles) == 0:
            return None
        return self.opClassHandles[0]

    @opClassHandle.setter
    def opClassHandle(self, value):
        if len(self.opClassHandles) == 0:
            self.opClassHandles.append(value)
        else:
            self.opClassHandles[0] = value

    @opClassHandle.getter
    def opClassHandle(self):
        if len(self.opClassHandles) == 0:
            return None
        return self.opClassHandles[0]

    ###########################################################################################################################
    ###########################################################################################################################
    ###########################################################################################################################

    # Federation management

    # join the federation and, if it does not exist yet, create it first
    def joinFederationExecution(self, FEDERATION_NAME, FEDERATION_PATH):
        try:
            self.rtiaReference.createFederationExecution(FEDERATION_NAME, FEDERATION_PATH)
            self.creator = True
            print("Federation created.")
        except Exception as e:
            print("Federation exists: %s" % repr(e))
        finally:
            print ('Federation done.')
        try:
            self.rtiaReference.joinFederationExecution(self.federateName, FEDERATION_NAME, self)
            self.federationName = FEDERATION_NAME
        except Exception as e:
            print("Could not join federation execution: %s" % repr(e))
        finally:
            print ('Joining federation done.')

    # leave the federation and terminate it if the last one to leave
    def terminate(self):
        if self.regObjects is not None and len(self.regObjects) > 0:
            for i in range(0, len(self.regObjects)):
                self.rtiaReference.deleteObjectInstance(self.regObjects[i], self.opObjectNames[i])

        try:
            self.rtiaReference.resignFederationExecution(2)
        except Exception as e:
            print("Could not do, exception: %s" % repr(e))

        try:
            # this line can only execute correctly if this is the last federate that is leaving the federation
            # otherwise, an exception is thrown
            self.rtiaReference.destroyFederationExecution(self.federationName)
        except Exception as e:
            print("Could not destroy Federation, exception: %s" % repr(e))
            print("There are still some federates in the federation.")

    ###########################################################################################################################
    ###########################################################################################################################
    # Declaration management

    #####################################################################################
    ## Publishes the messages it would like to communicate to other RTIs (message consistes of class name and attribute names)
    def publish(self, className, attribNames):
        if className is None or attribNames is None:
            return
        if len(attribNames) == 0:
            return
        if type(attribNames) is not dict:
            raise Exception("attribNames must be a dictionary")

        self.opClassHandle = self.rtiaReference.getObjectClassHandle(className)
        handleSet = []
        self.publications = attribNames
        for k, n in attribNames.items():
            if DEFAULTS.RTI_VERSION == 13:
                self.opHandles[k] = self.rtiaReference.getAttributeHandle(k, self.opClassHandle)
            else:
                self.opHandles[k] = self.rtiaReference.getAttributeHandle(self.opClassHandle, k)
            handleSet.append(self.opHandles[k])

        if DEFAULTS.RTI_VERSION == 13:
            self.rtiaReference.publishObjectClass(self.opClassHandle, handleSet)
        else:
            self.rtiaReference.publishObjectClassAttributes(self.opClassHandle, handleSet)

    #####################################################################################
    ## Subscribes to the messages it would like to receive from other RTIs (message consistes of class name and attribute names)   
    def subscribe(self, className, attribNames):
        if className is None or attribNames is None:
            return
        if len(attribNames) == 0:
            return
        if type(attribNames) is not dict:
            raise Exception("attribNames must be a dictionary")
        self.ipClassHandle = self.rtiaReference.getObjectClassHandle(className)
        handleSet = []
        self.subscriptions = attribNames
        for k, v in attribNames.items():
            if DEFAULTS.RTI_VERSION == 13:
                self.ipHandles[k] = self.rtiaReference.getAttributeHandle(k, self.ipClassHandle)
            else:
                self.ipHandles[k] = self.rtiaReference.getAttributeHandle(self.ipClassHandle, k)

            handleSet.append(self.ipHandles[k])

        self.rtiaReference.subscribeObjectClassAttributes(self.ipClassHandle, handleSet)

    ###########################################################################################################################
    ###########################################################################################################################
    # Time management

    # blocking function for the simulation-loop execution (this is where a step forward is evoked)
    def requestPermissionToProceed(self, timeT):
        self.granted = False
        #self.rtiaReference.nextEventRequest(timeT)
        self.rtiaReference.timeAdvanceRequest(timeT)
        while self.granted == False:
            if DEFAULTS.RTI_VERSION == 13:
                self.rtiaReference.tick()
            else:
                self.rtiaReference.evokeCallback(1.0)
            #print ("time:" + repr(timeT))

    # CALLBACK is made when the federate is allowed to proceed
    def timeAdvanceGrant(self, time):
        self.granted = True
        self.time = round(time, DEFAULTS.DEFAULT_PRECISION)
        print("time:" + repr(self.time))

    # specify the lookahead value used through the simulation
    def enableTimeSwitches(self, lookahead):
        if DEFAULTS.RTI_VERSION == 13:
            self.enableTimeSwitches_13(lookahead)
        else:
            self.enableTimeSwitches_1516(lookahead)

    def enableTimeSwitches_13(self, lookahead):
        self.lookAhead = lookahead
        self.rtiaReference.enableTimeConstrained()
        t = self.rtiaReference.queryFederateTime()
        self.rtiaReference.enableTimeRegulation(t + 1, self.lookAhead)

    def enableTimeSwitches_1516(self, lookahead):
        self.rtiaReference.setLogicalTimeFactory("certiFedTime1516")
        self.lookAhead = lookahead
        self.rtiaReference.enableTimeConstrained()
        self.rtiaReference.enableTimeRegulation(self.lookAhead)

    # CALLBACK is made in response to enableTimeRegulation
    def timeRegulationEnabled(self, time):
        self.timeState |= TimeState.Regulated

    # CALLBACK is made in response to enableTimeConstrained
    def timeConstrainedEnabled(self, time):
        self.timeState |= TimeState.Constrained

    ###########################################################################################################################
    ###########################################################################################################################
    #  Object management (registration)

    # create and register message objects before using them
    def registerAllInstances(self, names):
        for i in range(0, len(names)):
            self.registerInstance(names[i], self.opClassHandles[i])

    def registerInstance(self, name, classHandle=None):
        if DEFAULTS.RTI_VERSION == 13:
            self.registerInstance_13(name, classHandle)
        else:
            self.registerInstance_1516(name, classHandle)

    def registerInstance_1516(self, name, classHandle=None):

        if classHandle is None:
            classHandle = self.opClassHandles[-1]

        t = self.rtiaReference.queryLogicalTime()
        self.rtiaReference.evokeMultipleCallbacks(0, t + 1.0)

        self.opObjectNames.append(name)
        self.rtiaReference.reserveObjectInstanceName(name)

        while self.nameReserved == False:
            self.rtiaReference.evokeCallback(1.0)

        self.regObjects.append(self.rtiaReference.registerObjectInstance(classHandle, name))

    def registerInstance_13(self, name, classHandle=None):
        if classHandle is None:
            classHandle = self.opClassHandles[-1]
        self.opObjectNames.append(name)
        self.regObjects.append(self.rtiaReference.registerObjectInstance(classHandle, name))

    # CALLBACK is made when registering if the proposed object name is unique
    def objectInstanceNameReservationSucceeded(self, name):
        if name in self.opObjectNames:
            self.nameReserved = True
            return
        raise Exception('objectInstanceNameReservationSucceeded: Name is not same as reserved')

    # CALLBACK is made when another federate has created a message object that this federate is subscribed to receive
    def discoverObjectInstance(self, object, objectclass, name):
        if object not in self.otherObjects and object not in self.regObjects:
            self.otherObjects.append(object)

    # CALLBACK is made to remove all discovered object instances
    def removeObjectInstance(self, object, userSuppliedTag, theTime=None, retractionHandle=None):
        if object in self.otherObjects:
            self.otherObjects.remove(object)

    # CALLBACK ???
    def startRegistrationForObjectClass(self, params):
        pass

    # CALLBACK ???
    def provideAttributeValueUpdate(self, *params):
        pass

    #  Object management (receive message)

    # CALLBACK is made when new messages are available for this federate (It only works for timed updates)
    def reflectAttributeValues(self, object, attributes, tag, order, transport, logicalTime=None, receiveOrder=None,
                               regionHandleSet=None, sentRegionHandleSet=None):
        if logicalTime is not None:
            self.TsoMsgReceived = True
            logicalTime = round(logicalTime, DEFAULTS.DEFAULT_PRECISION)

        if object in self.otherObjects:
            for ah in attributes.keys():
                for n in self.ipHandles.keys():
                    if ah == self.ipHandles[n]:
                        self.pendingUpdates.append([logicalTime, n, attributes[ah]])

    ###########################################################################################################################
    ###########################################################################################################################
    #   Synchronization point management

    # CALLBACK is made to let the federate know that the synchronization point has been registered
    def synchronizationPointRegistrationSucceeded(self, label):
        # if label == self.synchLabel:
        self.synchState = SynchState.Registered
        print("synchronizationPointRegistrationSucceeded  %s" % repr(label))

    # CALLBACK is made to let the federate know that the synchronization point has not been registered
    def synchronizationPointRegistrationFailed(self, label, reason):
        # if label == self.synchLabel and self.creator == False:
        self.synchState = SynchState.Registered
        print("synchronizationPointRegistrationFailed  %s" % repr(reason))

    # CALLBACK is made as soon as the synchronization point is successfully registered to let all federates know that this synchronization point is comming up next
    def announceSynchronizationPoint(self, label, tag):
        # if label == self.synchLabel:
        self.synchState = SynchState.Announced
        print("announceSynchronizationPoint  %s" % repr(label))

    # CALLBACK is made after all federates in the federation have called synchronization point achieved to unblock them
    def federationSynchronized(self, label):
        # if label == self.synchLabel:
        self.synchState = SynchState.Synched
        print("federationSynchronized  %s" % repr(label))

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation.
    def waitReadyToPopulate(self):
        self.synchState = SynchState.NotInit
        self.waitWorker("Init")

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation.
    def waitReadyToRun(self):
        if DEFAULTS.RTI_VERSION == 13:
            self.waitReadyToRun_13()
        else:
            self.waitReadyToRun_1516()

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation. This implementation specific function when we are using HLA_13
    def waitReadyToRun_13(self):
        t = self.rtiaReference.queryFederateTime()
        count = 0
        while len(self.otherObjects) == 0 and count < 2:
            self.rtiaReference.tick()
            count += 1
        self.synchState = SynchState.NotInit
        self.waitWorker("Run")

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation. This implementation specific function when we are using HLA_1516
    def waitReadyToRun_1516(self):
        t = self.rtiaReference.queryLogicalTime()
        count = 0
        # when you are sure there is going to be other objects, then put a more strict check and put the
        # the exact number of objects instead of == 0, of course remove count < 5
        while len(self.otherObjects) == 0 and count < 2:
            self.rtiaReference.evokeCallback(1.0)
            count += 1
        self.synchState = SynchState.NotInit
        self.waitWorker("Run")

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation. It hides specific function implementations of HLA_13 or HLA_1516
    def waitWorker(self, label):
        if DEFAULTS.RTI_VERSION == 13:
            self.waitWorker_13(label)
        else:
            self.waitWorker_1516(label)

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation. This implementation specific function when we are using HLA_1516
    def waitWorker_1516(self, label):
        self.synchLabel = label
        # clear up anything left
        t = self.rtiaReference.queryLogicalTime()
        self.rtiaReference.evokeCallback(1.0)

        if self.creator == True:
            self.rtiaReference.registerFederationSynchronizationPoint(self.synchLabel, "Waiting for all players")
            self.synchState = SynchState.RegisterRequested
            # necessary to ensure that the registration is succeeded
            t = self.rtiaReference.queryLogicalTime()
            while self.synchState < SynchState.Registered:
                self.rtiaReference.evokeCallback(1.0)

        t = self.rtiaReference.queryLogicalTime()
        while self.synchState < SynchState.Announced:
            self.rtiaReference.evokeCallback(1.0)

        if self.creator == True:
            if not self.test:
                print ("Press ENTER to start execution...")
                c = sys.stdin.read(1)
            else:
                time.sleep(3)

        self.rtiaReference.synchronizationPointAchieved(self.synchLabel)
        self.synchState = SynchState.Achieved

        while self.synchState < SynchState.Synched:
            self.rtiaReference.evokeCallback(1.0)
        print ("Synchronization achieved for label:%s" % self.synchLabel)
        return True

    #######################################################################################################################
    ## This is one of group of functions which provide the control over starting all the federates at the same clock time.
    ## It is only used in the beginning of the simulation. This implementation specific function when we are using HLA_13
    def waitWorker_13(self, label):
        self.synchLabel = label
        # clear up anything left
        t = self.rtiaReference.queryFederateTime()
        self.rtiaReference.tick()

        if self.creator == True:
            if not self.test:
                print ("Press ENTER when sure that other federate has started Synchronization...")
                c = sys.stdin.read(1)
            else:
                time.sleep(3)

            self.rtiaReference.registerFederationSynchronizationPoint(self.synchLabel, "Waiting for all players")
            self.synchState = SynchState.RegisterRequested
            # necessary to ensure that the registration is succeeded
            while self.synchState < SynchState.Registered:
                self.rtiaReference.tick()

        print ("Waiting for Synchronization point to be announced")
        print (self.synchState)
        print (SynchState.Announced)
        while self.synchState < SynchState.Announced:
            self.rtiaReference.tick()

        if self.creator == True:
            if not self.test:
                print ("Press ENTER to start execution...")
                c = sys.stdin.read(1)
            else:
                time.sleep(3)

        self.rtiaReference.synchronizationPointAchieved(self.synchLabel)
        self.synchState = SynchState.Achieved

        while self.synchState < SynchState.Synched:
            self.rtiaReference.tick()

        print ("Synchronization achieved for label:%s" % self.synchLabel)
        return True

    ###########################################################################################################################
    ###########################################################################################################################
    # Should be defined by the inherited classes

    def getNextEventTime(self):
        pass

    def updateAttributes(self):
        pass

class HLAPort(rti.FederateAmbassador, BaseFederate):
    def __init__(self, federateName, options):
        super(HLAPort, self).__init__(federateName)
        self.step = options['step']
        self.test = options['UNIT_TESTS']

    ## Receives attributes from the RTI
    def get_message(self, name=None):
        #msg = []
        msg = {}
        if name is None:
            updt = list(self.pendingUpdates)
            self.pendingUpdates.clear()
            print("received:" + repr(updt))
            #msg.append(int(updt[2]))
            msg['time'] = updt[0]
            msg['name'] = updt[1]
            msg['value'] = float(updt[2])
            return msg                                             # this line returns only the value that has been received (time and name are neglected)
        else:
            print('len of penUpd = ' + str(len(self.pendingUpdates)))
            while len(self.pendingUpdates) > 0:
                updt = self.pendingUpdates.pop(0)
                print("received:" + repr(updt))
                if (self.subscriptions[updt[RXMSG_INDEX.NAME]] == name):
                    #msg.append(int(updt[2]))
                    msg['time'] = updt[0]
                    msg['name'] = updt[1]
                    msg['value'] = float(updt[2])                   # TODO: change this so that it supports all types
                    return msg                                     # this line returns only the value that has been received (time and name are neglected)
            return []


    ## Sends attributes to the RTI
    def set_message(self, msg):
        while len(msg) > 0:
            updtDict = {}

            # if msg[0][TXMSG_INDEX.NAME] in self.opHandles:
            #     updtDict[self.opHandles[msg[0][TXMSG_INDEX.NAME]]] = repr(msg[0][TXMSG_INDEX.VALUE])
            #     print("sending:" + repr(updtDict))

            if msg[0]['name'] in self.opHandles:
                updtDict[self.opHandles[msg[0]['name']]] = repr(msg[0]['value'])
                print("sending:" + repr(updtDict))

            if len(updtDict) > 0:
                try:
                    h = self.rtiaReference.updateAttributeValues(self.myObject, updtDict, "update", self.time+self.step)
                except Exception as e:
                    print("Update exception :" + repr(e) + "Federation time :" + repr(
                        self.rtiaReference.queryFederateTime()) + "self.time:" + repr(self.time))
                    print("object:" + repr(self.myObject))
                    print("updtDict:" + repr(updtDict))
                    print("opHandles:" + repr(self.opHandles))
            msg.pop(0)

    def connect(self,options):

        try:
            self.joinFederationExecution(options['FEDERATION_NAME'], options['FOM_PATH'])
            self.enableTimeSwitches(0.0)

            # publish the message type
            self.publish(options['PUB_CLASS'], options['PUBLISH_DICT'])

            # subscribe to message types
            self.subscribe(options['SUB_CLASS'], options['SUBSCRIBE_DICT'])

            # wait for all simulators before registering their objects with the federation
            self.waitReadyToPopulate()

            # register federate with federation
            self.registerInstance(self.federateName)  # can be different than federate name

            # wait for all simulators before starting the simulation
            self.waitReadyToRun()

        except Exception as e:
            print("Could not do, exception: %s" % repr(e))
            traceback.print_exc()

    def disconnect(self,options):

        try:
            self.terminate()

        except Exception as e:
            print("Could not do, exception: %s" % repr(e))
            traceback.print_exc()


#############################################################################################
######## Here start the classes which are inheriting classes from Cossembler engine

class inCom(Element):

    def __init__(self,name,port,msgName,msgType,options=None):
        super().__init__(name,options)
        self.myPort = port
        self.msgName = msgName
        self.output.append(EMPTYMSG.copy())
        self.output[0]['name'] = name + ".y1"
        self.msgType = msgType

    def doFunc(self):
        msg = self.myPort.get_message(self.msgName)
        if len(msg)>0:
            #self.output[0] = msg[0]
            self.output[0] = msg
            self.output[0]['type'] = self.msgType

class outCom(Element):

    def __init__(self,name,port,msgName,options=None):
        super().__init__(name,options)
        self.myPort = port
        self.msgName = msgName
        self.input.append(EMPTYMSG.copy())

    def doFunc(self):
        print(self.name + ' : ' + self.msgName + str(self.input[0]))
#        print(self.msgName)
#        print(self.input[0])
        #self.myPort.set_message([[self.msgName,self.input[0]]])
        self.input[0]['name'] = self.msgName                                    # TODO: check if this is the best way to handle it (see dev doc)
        self.myPort.set_message([self.input[0]])

class synch(Element):

    def __init__(self,name,port,step,end,options=None):
        super().__init__(name,options)
        self.myPort = port
        self.step = step
        self.end = end
        self.nextT = 0

    def doFunc(self):
        self.nextT += self.step
        self.myPort.requestPermissionToProceed(self.nextT)
        if (self.nextT) > self.end:
            self.nextElem = []

class HLA(Canvas,WorldConnector):

    def __init__(self,name,type,options):
        super().__init__(name,options)
        self.myHLA = HLAPort(name,options)
        self.myInCom = inCom(name + '.inCom',self.myHLA,options['SUBSCRIBE_MSG'],type)
        self.myOutCom = outCom(name + '.outCom',self.myHLA,options['PUBLISH_MSG'])
        self.mySynch = synch(name + '.synch',self.myHLA,options['step'],options['end'])

        # self.add_element(self)
        self.add_element(self.myInCom)
        self.add_element(self.myOutCom)
        self.add_element(self.mySynch)

        if options['SERIAL']:
            self.myOutCom.connect(self.mySynch, 1, 1)
            self.mySynch.connect(self.myInCom, 1, 1)
        else:
            self.myOutCom.connect(self.myInCom, 1, 1)
            self.myInCom.connect(self.mySynch, 1, 1)

        # TODO: check if these two lines below are needed. I think not.
        self.input.append(EMPTYMSG.copy())
        self.input.append(EMPTYMSG.copy())


    def connect(self, right, pinout, pinin):

        super().connect(right, pinout, pinin)

        if self.options['SERIAL']:
            self.myInCom.connect(right, pinout, pinin)
        else:
            self.mySynch.connect(right, pinout, pinin)

    def accept(self, pinin):
        return self.myOutCom

    def connectToTheWorld(self):
        self.myHLA.connect(self.options)

    def disconnectFromTheWorld(self):
        self.myHLA.disconnect(self.options)

    def doFunc(self):
        super().doFunc()

    def compile(self):
        super().compile()                                       # when inheriting from Canvas, super().compile() and .decompile() must be called
        self.connectToTheWorld()

    def decompile(self):
        super().decompile()
        self.disconnectFromTheWorld()
