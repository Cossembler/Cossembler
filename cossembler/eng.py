
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

try:
    import Queue as Q  # ver. < 3.0
except ImportError:
    import queue as Q


class ELEMADDRESS:
    PINOUT = 0
    NEXTELEM = 1
    PININ = 2

class PRIORITY:
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6
    L7 = 7
    L8 = 8
    L9 = 9
    TOP = L1
    HIGH = L3
    MEDIUM = L5
    LOW = L7
    BOTTOM = L9
    DEFAULT = LOW

PRIORITYTABLE = {
    'Element'           : PRIORITY.LOW,
    'Canvas'            : PRIORITY.MEDIUM,
    'Addition'          : PRIORITY.LOW,
    'Interpolation'     : PRIORITY.HIGH,
    'Gain'              : PRIORITY.HIGH,
    'Source'            : PRIORITY.TOP,
    'Sink'              : PRIORITY.BOTTOM,
    'Increment'         : PRIORITY.HIGH,
    'Decrement'         : PRIORITY.HIGH,
    'inCom'             : PRIORITY.LOW,
    'outCom'            : PRIORITY.HIGH,
    'synch'             : PRIORITY.LOW,
    'Reflector'         : PRIORITY.HIGH,
    'TXBuffer'          : PRIORITY.HIGH,
    'RXBuffer'          : PRIORITY.L8,
    'acknowledge'       : PRIORITY.HIGH,
    'WhileLoop'         : PRIORITY.MEDIUM,
    'ForLoop'           : PRIORITY.MEDIUM,
    'Index'             : PRIORITY.HIGH,
    'Mux'               : PRIORITY.LOW,
    'Demux'             : PRIORITY.HIGH,
    'TypeConversion'    : PRIORITY.HIGH,
    'ValueToTime'       : PRIORITY.HIGH,
    'TimeToValue'       : PRIORITY.HIGH,
    'Ping'              : PRIORITY.BOTTOM
}


class VALUETYPES:
    NONE = "NONE"               # this is a type used by default; during config time make sure all types are changed
    BOOL = "BOOL"
    INT = "INT"
    REAL = "FLOAT"              # alternative is DOUBLE for double precision
    STRING = "STRING"
    VECTOR = "LIST"             # alternative is ARRAY as in numpy.array
    MATRIX = "LISTLIST"         # alternative is MATRIX as in numpy.matrix (must not be the same as VECTOR!)
    DEFAULT = REAL              # this is the default type for initialization of many Elements

EMPTYMSG = {'name':'', 'type':VALUETYPES.NONE, 'time':0.0, 'value':0.0}

class CheckType(object):

    def __init__(self):
        return

    def getType(self,val):
        if isinstance(val,bool):
            return VALUETYPES.BOOL
        if isinstance(val,str):
            return VALUETYPES.STRING
        if isinstance(val,int):
            return VALUETYPES.INT
        if isinstance(val,float):
            return VALUETYPES.REAL
        if isinstance(val,list):
            if any(isinstance(el, list) for el in val):
                return VALUETYPES.MATRIX
            else:
                return VALUETYPES.VECTOR

    def isType(self,val,type):
        return self.getType(val)==type

    def castToType(self,val,type):
        if type==VALUETYPES.STRING:
            return str(val)
        if type==VALUETYPES.BOOL:
            return bool(val)
        if type==VALUETYPES.INT:
            return int(val)
        if type==VALUETYPES.REAL:
            return float(val)
        if type==VALUETYPES.VECTOR:
            return list(val)
        if type==VALUETYPES.MATRIX:
            return list(list(val))
        #print("Exception! CheckType.castToType(): Provided type not supported.")
        logging.error("Exception! CheckType.castToType(): Provided type not supported.")
        return val

    def isThisType(self,type):
        if type==VALUETYPES.BOOL or type==VALUETYPES.INT or type==VALUETYPES.REAL\
                or type==VALUETYPES.STRING or type==VALUETYPES.VECTOR or type==VALUETYPES.MATRIX\
                or type==VALUETYPES.NONE or type==VALUETYPES.DEFAULT:
            return True
        else:
            return False


class CopyMessage(object):

    def __init__(self):
        return

    def copy(self,dest,source,tag=''):
        if tag=='time' or tag=='value' or tag=='name' or tag=='type':
            dest[tag] = source[tag]
        else:
            Exception("CopyMessage().copy(): Message does not contain provided keyword. Cannot copy.")

    def copyContent(self, dest, source):
        self.copy(dest, source, 'time')
        self.copy(dest, source, 'value')

    def copyAll(self,dest,source):
        self.copyContent(dest, source)
        self.copy(dest, source, 'name')
        self.copy(dest, source, 'type')


copyMachine = CopyMessage()
typeChecker = CheckType()

class Comparison(object):

    def __init__(self):
        return

    def compare(self,a,b):
        pass

class AgteqB(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return a>=b

class AgtB(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return a>b

class AlteqB(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return a<=b

class AltB(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return a<b

class AeqB(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return a==b

class AneqB(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return a!=b

class EdgeCompare(Comparison):

    def __init__(self):
        super().__init__()
        self.myOld = 0.0

    def compare(self,a,b=0.0):
        pom = (a!=self.myOld)
        self.myOld = a
        return pom

class EmptyCompare(Comparison):

    def __init__(self):
        super().__init__()
        return

    def compare(self,a,b):
        return False

class ActionOnCondition(object):
    def __init__(self,elem):
        self.myElem = elem
        return

    def action(self):
        pass

class StopOnCondition(ActionOnCondition):
    def __init__(self,elem):
        super().__init__(elem)
        return

    def action(self):
        self.myElem.active = False

class StartOnCondition(ActionOnCondition):
    def __init__(self,elem):
        super().__init__(elem)
        return

    def action(self):
        self.myElem.active = True

class InitOnCondition(ActionOnCondition):
    def __init__(self,elem):
        super().__init__(elem)
        return

    def action(self):
        self.myElem.init = True

class DeInitOnCondition(ActionOnCondition):
    def __init__(self,elem):
        super().__init__(elem)
        return

    def action(self):
        self.myElem.init = False

class EmptyActionOnCondition(ActionOnCondition):
    def __init__(self,elem):
        super().__init__(elem)
        return

    def action(self):
        return

class Condition(object):

    def __init__(self,elem):
        self.myElem = elem
        self.myAction = EmptyActionOnCondition(elem)
        self.myNegAction = EmptyActionOnCondition(elem)
        self.condIn = False                         # is there a condition on input pins
        self.condOut = False                        # is there a condition on output pins
        self.condRep = False                        # is there a condition on number of evaluations of condition (repetitions of execution)
        self.condInit = False                       # is there an initialization condition active; if yes, the element will first call compile before doFunc
        self.myInComp = EmptyCompare()
        self.myOutComp = EmptyCompare()
        self.tIn = 'value'                        # alternative is 'time' if condition applies to time
        self.msgIn = EMPTYMSG.copy()
        self.valIn = 0
        self.tOut = 'value'                       # alternative is 'time' if condition applies to time
        self.msgOut = EMPTYMSG.copy()
        self.valOut = 0
        self.cnt = 0                                # repetition counter
        self.valRep = 0                             # max number of repetitions

    def setCondition(self,s,io,a='stop',ar='no'):
        if io=='in':
            self.condIn = True
        elif io =='out':
            self.condOut = True
        else:
            Exception("Condition.setCondition(): Condition can either be 'in' or 'out'. Incorrect string provided.")

        if a=='init' and s.find('edge')>=0:
            ar = 'deinit'

        self._setAction(a,ar)

        s1 = ""
        s2 = ""
        pc = EmptyCompare()

        if s.find('>')>=0:
            if s.find('>')+1==s.find('='):
                pc = AgteqB()
                s1 = s[:s.find('>')]
                s2 = s[s.find('=')+1:]
            else:
                pc = AgtB()
                s1 = s[:s.find('>')]
                s2 = s[s.find('>')+1:]
        elif s.find('<')>=0:
            if s.find('<') + 1 == s.find('='):
                pc = AlteqB()
                s1 = s[:s.find('<')]
                s2 = s[s.find('=')+1:]
            else:
                pc = AltB()
                s1 = s[:s.find('<')]
                s2 = s[s.find('<')+1:]
        elif s.find('==')>=0:
            pc = AeqB()
            s1 = s[:s.find('=')]
            s2 = s[s.find('=') + 2:]
        elif s.find('!=')>=0:
            pc = AneqB()
            s1 = s[:s.find('!')]
            s2 = s[s.find('=') + 1:]
        elif s.find("edge")>=0:
            a = EMPTYMSG.copy()
            b = 0
            pc = EdgeCompare()
            s1 = s[s.find('{') + 1:s.find('}')]
            if io == 'in':
                #for i in self.myElem.input:
                #    if i['name'].find(s1)>=0:
                #        a = i
                for i in self.myElem.options['inputs']:
                    if i.find(s1) >= 0:
                        pom = self.myElem.translate(i,'in')
                        if pom == -1:
                            pom = self.myElem.myCanvas.translate(i, 'in')
                        if len(self.myElem.input)>0:
                            a = self.myElem.input[pom-1]
                        else:
                            a = self.myElem.elem_list[pom-1].input[0]
                self.myInComp = pc
                self.msgIn = a
                self.valIn = a['value']
            else:
                for i in self.myElem.output:
                    if i['name'].find(s1)>=0:
                        a = i
                self.myOutComp = pc
                self.msgOut = a
                self.valOut = a['value']
            return
        else:
            Exception("Condition.setCondition(): Incorrect condition provided.")

        if s1.find('(time)')>=0 or s2.find('(time)')>=0:
            if io=='in':
                self.tIn = 'time'
            else:
                self.tOut = 'time'

        if s1.find('(time)')>=0:
            s1 = s1.replace('(time)','')
        if s1.find('(value)')>=0:
            s1 = s1.replace('(value)', '')
        if s2.find('(time)')>=0:
            s2 = s2.replace('(time)','')
        if s2.find('(value)')>=0:
            s2 = s2.replace('(value)', '')

        a = EMPTYMSG.copy()
        b = 0

        err = False
        if s1!="" and s2!="":
            if io=='in':
                pom = self.myElem.input
            else:
                pom = self.myElem.output

            for i in range(0,len(pom)):
                if pom[i]['name'].find(s1)>=0:
                    a = pom[i]
                    b = typeChecker.castToType(s2,pom[i]['type'])
                    err = False
                    break
                else:
                    err = True
                if pom[i]['name'].find(s2)>=0:
                    a = pom[i]
                    b = typeChecker.castToType(s1, pom[i]['type'])
                    if isinstance(pc,AgtB):
                        pc = AltB
                    elif isinstance(pc,AltB):
                        pc = AgtB
                    elif isinstance(pc,AgteqB):
                        pc = AlteqB
                    elif isinstance(pc,AlteqB):
                        pc = AgteqB
                    err = False
                    break
                else:
                    err = True

            if err:
                Exception("Condition.setCondition(): Incorrect pin name provided.")

            if io == 'in':
                self.myInComp = pc
                self.msgIn = a
                self.valIn = b
            else:
                self.myOutComp = pc
                self.msgOut = a
                self.valOut = b

        else:
            Exception("Condition.setCondition(): Incorrect pin name or comparative value provided.")


    def _setAction(self,a,ar='no'):
        if a=='stop':
            self.myAction = StopOnCondition(self.myElem)
            if ar=='start':
                self.myNegAction = StartOnCondition(self.myElem)
        elif a=='init':
            self.myAction = InitOnCondition(self.myElem)
            if ar=='deinit':
                self.myNegAction = DeInitOnCondition(self.myElem)
        else:
            Exception("Condition.setCondition(): Incorrect action string provided.")

    def setRepCondition(self,val,a='stop'):
        self.valRep = val
        self._setAction(a)
        self.condRep = True

    def setInitCondition(self):
        self.condInit = True

    def stateCond(self,s):                          # returns True if condition is satisfied and False otherwise without incrementing condition along the way (important for counter)
        if self.condRep and s == 'rep':
            if self.cnt<self.valRep:
                return False
            else:
                return True
        if self.condIn and s=='in':
            return self.myInComp.compare(self.msgIn[self.tIn], self.valIn)
        if self.condOut and s=='out':
            return self.myOutComp.compare(self.msgOut[self.tOut], self.valOut)
        if s=='init':
            return self.condInit
        return False

    def evaluate(self,s):                           # evaluates the action if condition is satisfied and returns True; otherwise it does not evaluate action and returns False
        if self.condRep and s=='rep':
            if self.cnt<self.valRep:
                self.cnt += 1
                self.myNegAction.action()
                return False
            else:
                self.myAction.action()
                return True

        if s=='in':
            if self.myInComp.compare(self.msgIn[self.tIn], self.valIn):
                self.myAction.action()
                return True
            else:
                self.myNegAction.action()
                return False
        if s=='out':
            if self.myOutComp.compare(self.msgOut[self.tOut], self.valOut):
                self.myAction.action()
                return True
            else:
                self.myNegAction.action()
                return False
        if s=='init':
            pom = self.condInit
            if pom:
                self.myAction.action()
            self.condInit = False
            return pom
        return False

    def isCondition(self):
        if self.condIn or self.condOut or self.condRep or self.condInit:
            return True
        else:
            return False

    def resetCondition(self, s=None):
        if s:
            if s=='in':
                self.condIn = False
                self.myInComp = EmptyCompare()
                self.tIn = 'value'  # alternative is 'time' if condition applies to time
                self.msgIn = EMPTYMSG.copy()
                self.valIn = 0
            if s=='out':
                self.condOut = False
                self.myOutComp = EmptyCompare()
                self.tOut = 'value'  # alternative is 'time' if condition applies to time
                self.msgOut = EMPTYMSG.copy()
                self.valOut = 0
            if s=='init':
                self.condInit = False
            if s=='rep':
                self.condRep = False
                self.cnt = 0  # repetition counter
                self.valRep = 0
        else:
            self.condIn = False
            self.myInComp = EmptyCompare()
            self.tIn = 'value'  # alternative is 'time' if condition applies to time
            self.msgIn = EMPTYMSG.copy()
            self.valIn = 0
            self.condOut = False
            self.myOutComp = EmptyCompare()
            self.tOut = 'value'  # alternative is 'time' if condition applies to time
            self.msgOut = EMPTYMSG.copy()
            self.valOut = 0
            self.condInit = False
            self.condRep = False
            self.cnt = 0  # repetition counter
            self.valRep = 0
        self.myAction = EmptyActionOnCondition(self.myElem)




class UniqueObject(object):

    name_list = [] # unique list of names for all elements in the environment

    def __init__(self,name):
        if not isinstance(name, str):
            raise Exception("Name attribute must be a string.")

        if name not in self.name_list:
            self.name = name
            self.name_list.append(name)
        else:
            raise Exception("Name must be unique.")

    def __lt__(self, other):
        return False

    def __gt__(self, other):
        return False


class Element(UniqueObject):

    def __init__(self,name,options = None):
        super().__init__(name)
        self.input = []
        self.output = []
        self.nextElem = []                                                          # The list of all elements connected to this one. The list contains entries of [#pinout, &Element, #pinin]
        self.active = True
        self.init = False
        self.myCondition = Condition(self)
        self.options = options
        if options and 'priority' in self.options:
            self.setPriority(self.options['priority'])
        elif self.__class__.__name__ in PRIORITYTABLE:
            self.setPriority(PRIORITYTABLE[self.__class__.__name__])
        elif super.__class__.__name__ in PRIORITYTABLE:
            self.setPriority(PRIORITYTABLE[super.__class__.__name__])
        else:
            self.setPriority(PRIORITY.DEFAULT)
        # self.priority = self.options['priority']
        self.myCanvas = None


    def createPin(self,io,type=VALUETYPES.DEFAULT,name="",cmd=""):
        if io=='in':
            self.input.append(EMPTYMSG.copy())
            if name=="":
                name = "u" + str(len(self.input))
            name = self.name + "." + name
            self._set_name(len(self.input), 'in', name)
            self._set_type(len(self.input), 'in', type)
#            self._set_cmd(len(self.input), 'in', cmd)
        elif io=='out':
            self.output.append(EMPTYMSG.copy())
            if name=="":
                name = "y" + str(len(self.output))
            name = self.name + "." + name
            self._set_name(len(self.output), 'out', name)
            self._set_type(len(self.output), 'out', type)
 #           self._set_cmd(len(self.output), 'out', cmd)
        else:
            Exception("Element.createPin(): A pin must be either 'in' or 'out'.")

    def createFlexInputPin(self,cmd=""):                                   # These can only be created as input pins. If pin is flex, then its type and name are defined by the output pin of the element connected to it.
        self.input.append(EMPTYMSG.copy())
#        self._set_cmd(len(self.input), 'in', cmd)

    def translate(self,pin,io):                                        # translate pin name given as string into a pin number
        if isinstance(pin,int):
            return pin
        if self.options:
            if io=='in' and 'inputs' in self.options:
                for i in range(0,len(self.options['inputs'])):
                    if self.options['inputs'][i].find(pin)>=0:
                        return i+1
                    pom = self.options['inputs'][i].replace('(',"")
                    pom = pom.replace(')', "")
                    if pom.find(pin)>=0:
                        return i+1
            if io=='out' and 'outputs' in self.options:
                for i in range(0,len(self.options['outputs'])):
                    if self.options['outputs'][i]==pin:
                        return i+1
                    pom = self.options['outputs'][i].replace('(',"")
                    pom = pom.replace(')', "")
                    if pom == pin:
                        return i+1
        return -1                                                   # If -1 is returned that means that this Element does not have rules for translation. However, it's canvas might have.

    def connect(self, right, pinout, pinin):

        if not isinstance(right,Element):
            Exception("Element.connect(): Provided argument is not a subclass of Element.")
        if not isinstance(self.myCanvas,Canvas):
            Exception("Element.connect(): Element " + self.name + " must be added to canvas before it can be connected.")
        if not isinstance(right.myCanvas,Canvas):
            Exception("Element.connect(): Element " + right.name + " must be added to canvas before it can be connected.")
        if isinstance(pinout,str):
            pom = self.translate(pinout,'out')
            if pom==-1:
                pinout = self.myCanvas.translate(pinout,'out')
            else:
                pinout = pom
        if isinstance(pinin,str):
            pom = right.translate(pinin,'in')
            if pom==-1:
                pinin = right.myCanvas.translate(pinin,'in')
            else:
                pinin = pom
        if pinout>0 and pinin>0:
            da = right.accept(pinin)                                               # This line is used to support Canvases. Because Canvas wants its internal element as the next one to receive the message
            if isinstance(da,dict):
                pom = da['elem']                                                    # this is the same as pom = da
                pinin = da['pin']                                                   # this is needed if Canvas has multiple elements within and then the pins need to remap as well
            else:
                pom = da
            if pom._get_type(pinin, 'in') == VALUETYPES.NONE:
                #print("Warning! Element.connect(): Assigning type " + self._get_type(pinout,'out') + " to input Pin " + str(pinin) + " of Element " + pom.name + ".")
                logging.info("Warning! Element.connect(): Assigning type " + self._get_type(pinout,'out') + " to input Pin " + str(pinin) + " of Element " + pom.name + ".")
                pom._set_type(pinin, 'in', self._get_type(pinout, 'out'))
                #print("Warning! Element.connect(): Assigning name " + self._get_name(pinout,'out') + " to input Pin " + str(pinin) + " of Element " + pom.name + ".")
                logging.info("Warning! Element.connect(): Assigning name " + self._get_name(pinout,'out') + " to input Pin " + str(pinin) + " of Element " + pom.name + ".")
                pom._set_name(pinin, 'in', self._get_name(pinout, 'out'))
            if self._get_type(pinout, 'out') != pom._get_type(pinin, 'in'):
                #print("Element.connect(): Pins of " + self.name + " and " + right.name + " cannot be connected since they are not of the same type.")
                logging.error("Element.connect(): Pins of " + self.name + " and " + right.name + " cannot be connected since they are not of the same type.")
            self.nextElem.append([pinout, pom, pinin])
            if (pom!=right) or pom.myCanvas!=self.myCanvas:
                try:
                    self.myCanvas._add_neighbor(pom)
                except:
                    #print("Element.connect(): It is very likely that the element to connect to is not added to any canvas.")
                    logging.warning("Element.connect(): It is very likely that the element to connect to is not added to any canvas.")

    def forward(self):                                                              # Announce to the next element that there is a message for it
        if self.active:
            for i in range(0, len(self.nextElem)):
                pom = self.nextElem[i]
                if len(pom[ELEMADDRESS.NEXTELEM].input)>0 and len(self.output)>0:       # Check if the next element has any inputs and if this element has any outputs
                    # (pom[ELEMADDRESS.NEXTELEM]).input[pom[ELEMADDRESS.PININ] - 1] = self.output[pom[ELEMADDRESS.PINOUT] - 1]                      # Copy the value of the output pin to the value of the input pin of the next element
                    copyMachine.copyAll((pom[ELEMADDRESS.NEXTELEM]).input[pom[ELEMADDRESS.PININ] - 1],self.output[pom[ELEMADDRESS.PINOUT] - 1])  # Copy the value of the output pin to the value of the input pin of the next element
            return True
        else:
            return False
			

    def accept(self, pinin):                                            # This function is used to accept connection. This is needed for Canvas since many internal components can be the one.
        return self

    def setInputCondition(self,s,a='stop'):
        self.myCondition.setCondition(s,'in',a)

    def setOutputCondition(self,s,a='stop'):
        self.myCondition.setCondition(s,'out',a)

    def setCounterCondition(self,val,a='stop'):
        self.myCondition.setRepCondition(val,a='stop')

    def setInitializationCondition(self):
        self.myCondition.setInitCondition()

    def resetCondition(self,s=None):
        self.myCondition.resetCondition(s)

    def setPriority(self,level):
        self.priority = level

    def execute(self):
        if self.myCondition.condRep:
            self.myCondition.evaluate('rep')
#            if self.myCondition.evaluate('rep'):
#                self.active = False
#            else:
#                self.active = True
        if self.myCondition.condIn:
            self.myCondition.evaluate('in')
#            if self.myCondition.evaluate('in'):
#                self.active = False
#            else:
#                self.active = True
        if self.active:
#            if self.myCondition.evaluate('init'):
            if self.init:
                self.compile()
            self.doFunc()
        if self.myCondition.condOut:
            self.myCondition.evaluate('out')
#            if self.myCondition.evaluate('out'):
#                self.active = False
#            else:
#                self.active = True

    def doFunc(self):
        pass

    def compile(self):
        pass

    def decompile(self):
        pass

    def restart(self):
        self.decompile()
        self.compile()

    def _get_type(self,pinID,io):
        if io == 'in' and (len(self.input) >= pinID):
            return self.input[pinID - 1]['type']
        elif io == 'out' and (len(self.output) >= pinID):
            return self.output[pinID - 1]['type']
        else:
            Exception("Element._get_type(): Provided Pin ID is higher than the existing number of pins.")

    def _set_type(self,pinID,io,type):
        if not typeChecker.isThisType(type):
            Exception("Element._set_type(): Provided type is not supported.")
            return
        if io == 'in' and (len(self.input) >= pinID):
            self.input[pinID - 1]['type'] = type
            if type == VALUETYPES.VECTOR:
                self.input[pinID - 1]['value'] = []
        elif io == 'out' and (len(self.output) >= pinID):
            self.output[pinID - 1]['type'] = type
            if type == VALUETYPES.VECTOR:
                self.output[pinID - 1]['value'] = []
        else:
            Exception("Element._set_type(): Provided Pin ID is higher than the existing number of pins.")


    def _get_name(self, pinID, io):
        if io == 'in' and (len(self.input) >= pinID):
            return self.input[pinID - 1]['name']
        elif io == 'out' and (len(self.output) >= pinID):
            return self.output[pinID - 1]['name']
        else:
            Exception("Element._get_name(): Provided Pin ID is higher than the existing number of pins.")


    def _set_name(self, pinID, io, name):
        if io == 'in' and (len(self.input) >= pinID):
            self.input[pinID - 1]['name'] = name
        elif io == 'out' and (len(self.output) >= pinID):
            self.output[pinID - 1]['name'] = name
        else:
            Exception("Element._set_name(): Provided Pin ID is higher than the existing number of pins.")


class Addition(Element):

    def __init__(self,name,Nin=2,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)
        for i in range(0,Nin):
            self.createFlexInputPin()
        self.createPin('out',type)

    def doFunc(self):
        if self.output[0]['type']==VALUETYPES.REAL or self.output[0]['type']==VALUETYPES.INT \
            or self.output[0]['type']==VALUETYPES.STRING or self.output[0]['type']==VALUETYPES.BOOL:
            self.output[0]['value'] = self.input[0]['value'] + self.input[1]['value']
        elif self.output[0]['type'] == VALUETYPES.VECTOR and \
                        self.input[0]['type'] == VALUETYPES.VECTOR and \
                        self.input[1]['type'] == VALUETYPES.VECTOR and \
                        len(self.input[0]['value'])==len(self.input[1]['value']):
            self.output[0]['value'] = [x + y for x, y in zip(self.input[0]['value'],self.input[1]['value'])]
        elif self.output[0]['type'] == VALUETYPES.MATRIX and len(self.input[0]['value'][0])==len(self.input[1]['value'][0]):
            for i in range(0,len(self.input[0]['value'])):
                pom1 = self.input[0]['value'][i]
                pom2 = self.input[1]['value'][i]
                self.output[0]['value'][i] = [x + y for x, y in zip(pom1,pom2)]
        elif self.output[0]['type'] == VALUETYPES.VECTOR:
            gd = True
            ll = 0
            for i in range(0, len(self.input)):
                if self.input[i]['type'] != VALUETYPES.VECTOR and self.input[i]['type'] != VALUETYPES.REAL:
                    gd = False
                    break
                elif self.input[i]['type'] == VALUETYPES.VECTOR:
                    ll = len(self.input[i]['value'])
            if not gd:
                Exception("Error! Addition.doFunc(): Tried to add uncompatible formats.")
            pom = []
            for i in range(0, len(self.input)):
                if self.input[i]['type'] == VALUETYPES.REAL:
                    pp = [self.input[i]['value']]*ll
                else:
                    pp = self.input[i]['value']
                pom.append(pp)
            self.output[0]['value'] = list(map(sum, zip(*pom)))

        #print(self.name + ' : ' + str(self.output[0]['value']))
        logging.debug("Addition element " + self.name + ' : ' + str(self.output[0]['value']))

class Interpolation(Element):

    def __init__(self,name,options=None):
        super().__init__(name,options)
        self.createPin('in',VALUETYPES.VECTOR,name+'.t')
        self.createPin('in', VALUETYPES.VECTOR,name+'.v')
        self.createPin('out',VALUETYPES.VECTOR)
        self.intpoints = None
        if options and 'inter_points' in options:
            if typeChecker.isType(options['inter_points'],VALUETYPES.VECTOR): # check also for asscending order
                self.intpoints = options['inter_points']

    def doFunc(self):
        if self.intpoints:
            import numpy as np
            self.output[0]['value'] = list(np.interp(self.intpoints, self.input[0]['value'], self.input[1]['value']))

        #print(self.name + ' : ' + str(self.input[0]['value']) + '+' + str(self.input[1]['value']) + '=' + str(self.output[0]['value']))
        logging.debug("Interpolation element " + self.name + ' : ' + str(self.input[0]['value']) + '+' + str(self.input[1]['value']) + '=' + str(self.output[0]['value']))

class Gain(Element):

    def __init__(self,name,val=1.0,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)

        if typeChecker.isThisType(type):
            if type==VALUETYPES.STRING or type==VALUETYPES.BOOL:
                Exception("Error! Gain.init(): Provided type is not supported.")
            else:
                self.createFlexInputPin()
                self.createPin('out',type)
                if ~typeChecker.isType(val, type):
                    self.myG = typeChecker.castToType(val, type)

    def doFunc(self):
        if self.output[0]['type']==VALUETYPES.REAL or self.output[0]['type']==VALUETYPES.INT:
            self.output[0]['value'] = self.input[0]['value'] * self.myG
        if self.output[0]['type']==VALUETYPES.VECTOR:
            for i in range(0,len(self.input[0]['value'])):
                self.output[0]['value'][i] = self.input[0]['value'][i] * self.myG
        if self.output[0]['type']==VALUETYPES.MATRIX:
            for i in range(0,len(self.input[0]['value'])):
                pom = self.input[0]['value'][i]
                for j in range(0, len(pom)):
                    self.output[0]['value'][i][j] = self.input[0]['value'][i][j] * self.myG

        #print(self.name + ' = ' + str(self.output[0]['value']))
        logging.debug("Gain element " + self.name + ' = ' + str(self.output[0]['value']))



class Source(Element):                  # works with many types and variants; see test_source.py

    def __init__(self,name,val,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)
        self.myStream = None
#        self.cnt = 0
        self.myVal = None


        if typeChecker.isThisType(type):                        # check if the specified type is type at all

            if options and 'file' in options:  # if source should read from a file, val variable is ignored
                import csv
                with open(options['file'], 'rt') as csvfile:
                    csvR = csv.reader(csvfile, delimiter=' ', quotechar='|')
                    self.myStream = []
                    row_count = sum(1 for row in csvR)
                    csvfile.seek(0)
                    for row in csvR:
                        print(row)
                        if len(row)==1:
                            self.myStream.append(row[0])
                        else:
                            if row_count==1:
                                self.myStream = row
                            else:
                                self.myStream.append(row)
                    print(self.myStream)

                    if typeChecker.isType(self.myStream[0],VALUETYPES.STRING) and type == VALUETYPES.STRING or \
                                        typeChecker.isType(self.myStream[0],VALUETYPES.BOOL) and type == VALUETYPES.BOOL or \
                                        typeChecker.isType(self.myStream[0],VALUETYPES.INT) and type == VALUETYPES.INT or \
                                        typeChecker.isType(self.myStream[0],VALUETYPES.REAL) and type == VALUETYPES.REAL:  # and if the value from the file belongs to one of the types
                        val = self.myStream[0]  # then assign that value to the source output
                    else:
                        Exception("Source.init(): The specified type does not match with the type of the value in the file.")

                    if typeChecker.isType(self.myStream,VALUETYPES.VECTOR) and type == VALUETYPES.VECTOR:
                        val = self.myStream
                    if typeChecker.isType(self.myStream,VALUETYPES.VECTOR) and type == VALUETYPES.REAL:
                        val = self.myStream[0]
                        self.setCounterCondition(len(self.myStream))
                    if typeChecker.isType(self.myStream,VALUETYPES.MATRIX) and type == VALUETYPES.MATRIX:
                        val = self.myStream
                    if typeChecker.isType(self.myStream,VALUETYPES.MATRIX) and type == VALUETYPES.VECTOR:
                        val = self.myStream[0]
                        self.setCounterCondition(len(self.myStream))

            elif options and 'rand' in options:
                if options['rand']=='gauss':
                    import random
                    if type==VALUETYPES.REAL:
                        val = random.gauss(options['mu'],options['sigma'])
                    if (type==VALUETYPES.VECTOR or type==VALUETYPES.REAL) and 'len' in options:
                        self.myStream = []
                        for i in range(0,options['len']):
                            self.myStream.append(random.gauss(options['mu'],options['sigma']))
                        if 'multistep' in options and options['multistep']:
                            val = self.myStream[0]
                            self.setCounterCondition(len(self.myStream))
                        else:
                            val = self.myStream
                    else:
                        #print("Error! Source.init(): If VECTOR output is desired, specify its lenght as 'len' in options")
                        logging.error("Error! Source.init(): If VECTOR output is desired, specify its lenght as 'len' in options")


            elif ~typeChecker.isType(val,type):                   # val must be the same type as type
                if typeChecker.isType(val,VALUETYPES.VECTOR) and type==VALUETYPES.REAL or \
                                        typeChecker.isType(val, VALUETYPES.MATRIX) and type == VALUETYPES.VECTOR: # val is vector but output should be real, with every time output is new value
                    self.myStream = val
                    val = self.myStream[0]                      # myStream contains full vector, val contains only the first value to output
                else:
                    val = typeChecker.castToType(val, type)
                if self.myStream:
                    self.setCounterCondition(len(self.myStream))

            self.createPin('out', type)
            self.myVal = val

        else:
            Exception("Error! Source.init(): Provided type is not supported.")

    def doFunc(self):
#        if self.output[0]['type']==VALUETYPES.REAL and isinstance(self.myStream,list):
#            self.output[0]['value'] = self.myStream[self.cnt]
#            self.cnt += 1
#        else:
        if self.options and self.options['rand'] == 'gauss':
            import random
            if self.output[0]['type'] == VALUETYPES.REAL:
                val = random.gauss(self.options['mu'], self.options['sigma'])
            if self.output[0]['type'] == VALUETYPES.VECTOR and 'len' in self.options:
                self.myStream = []
                for i in range(0, self.options['len']):
                    self.myStream.append(random.gauss(self.options['mu'], self.options['sigma']))
                if 'multistep' in self.options and self.options['multistep']:
                    val = self.myStream[0]
                    self.setCounterCondition(len(self.myStream))
                else:
                    val = self.myStream
            self.myVal = val

        self.output[0]['value'] = self.myVal
        #print(self.name + ' = ' + str(self.output[0]))
        logging.debug("Source element " + self.name + ' = ' + str(self.output[0]))

class TXBuffer(Element):

    def __init__(self,name,type=VALUETYPES.DEFAULT,direct="vertical",options=None):  # direct can be 1 or 2; it stands for direction if input is matrix
        super().__init__(name,options)
        self.cnt = 0
        self.direct = direct
        self.myOutType = type
        self.myStream = None
        self.createFlexInputPin()
        self.createPin('out',type)

    def doFunc(self):
        self.myStream = self.input[0]['value']

        if self.myOutType == VALUETYPES.REAL:

            if self.cnt>=len(self.myStream):
                self.cnt = 0

            self.output[0]['value'] = self.myStream[self.cnt]
            self.cnt+=1

        elif self.myOutType == VALUETYPES.VECTOR:

            if self.direct == "vertical":
                if self.cnt >= len(self.myStream):
                    self.cnt = 0
                self.output[0]['value'] = self.myStream[self.cnt]
            elif self.direct == "horizontal":
                if self.cnt >= len(self.myStream[0]):
                    self.cnt = 0
                pom = []
                for i in range(0,len(self.myStream)):
                    pom.append(self.myStream[i][self.cnt])
                self.output[0]['value'] = pom

            self.cnt += 1

        #print(self.name + ' = ' + str(self.output[0]))
        logging.debug("TXBuffer element " + self.name + ' = ' + str(self.output[0]))

    def compile(self):
        self.cnt = 0

class RXBuffer(Element):

    def __init__(self,name):
        super().__init__(name)
        self.myStream = []
        self.createPin('in',VALUETYPES.REAL)
        self.createPin('out',VALUETYPES.VECTOR)

    def doFunc(self):
        self.myStream.append(self.input[0]['value'])

        self.output[0]['value'] = self.myStream

        #print(self.name + ' = ' + str(self.output[0]))
        logging.debug("RXBuffer element " + self.name + ' = ' + str(self.output[0]))


    def compile(self):
        self.myStream = []


class Sink(Element):

    def __init__(self,name,size=0,Nin=1,options=None):
        super().__init__(name,options)
        for i in range(0,Nin):
            self.createFlexInputPin()

        self.myFile = None

        if options and 'file' in options:
            self.myFile = options['file']
            open(options['file'], 'w').close()

        self.knt = 0
        self.size = size
        self.myStream = []

    def doFunc(self):


        if len(self.input)>1:
            for i in range(0,len(self.input)):
                self.myStream.append(self.input[i]["value"])
        else:
            self.myStream = self.input[0]['value']

        self.knt += 1

        if self.myFile:
            import csv
            with open(self.myFile, 'a') as csvfile:
                #csvW = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_NONE, lineterminator='\n', dialect='excel')
                #csvW = csv.writer(csvfile, quoting=csv.QUOTE_NONE, escapechar=" ") #quotechar = " ", delimiter=' ', lineterminator='\n', dialect='excel')
                csvW = csv.writer(csvfile, dialect='excel', delimiter=' ', lineterminator='\n')
                # for i in self.myStream:
                #     csvfile.write(str(i)+" ")
                # csvfile.write("\n")
                csvW.writerow(self.myStream)
            #print(self.name + " " + str(self.knt) + ' = ' + str(self.input[0]))
            logging.debug("Sink element " + self.name + " " + str(self.knt) + ' = ' + str(self.input[0]))
            self.myStream.clear()
            self.myStream = []

        else:
            print(self.name + " " + str(self.knt) + ' = ' + str(self.input[0]))

class Ping(Element):
    def __init__(self,name,elem,options=None):
        super().__init__(name,options)
        if isinstance(elem,Element):
            self.myPingEl = elem
        else:
            raise Exception("Ping.init(): Provided argument must be a subclass of Element.")

    def doFunc(self):
        self.myPingEl.myCanvas._add_to_queue(self.myPingEl)


class Increment(Element):

    def __init__(self,name,val=1.0,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)

        if typeChecker.isThisType(type):
            if type==VALUETYPES.STRING or type==VALUETYPES.BOOL:
                Exception("Increment.init(): Provided type is not supported.")
            else:
                self.createFlexInputPin()
                self.createPin('out',type)
                if ~typeChecker.isType(val, type):
                    self.myInc = typeChecker.castToType(val, type)

    def doFunc(self):
        if self.output[0]['type']==VALUETYPES.REAL or self.output[0]['type']==VALUETYPES.INT:
            self.output[0]['value'] = self.input[0]['value'] + self.myInc
        if self.output[0]['type']==VALUETYPES.VECTOR:
            for i in range(0,len(self.input[0]['value'])):
                self.output[0]['value'][i] = self.input[0]['value'][i] + self.myInc
        if self.output[0]['type']==VALUETYPES.MATRIX:
            for i in range(0,len(self.input[0]['value'])):
                pom = self.input[0]['value'][i]
                for j in range(0, len(pom)):
                    self.output[0]['value'][i][j] = self.input[0]['value'][i][j] + self.myInc

        #print(self.name + ' = ' + str(self.output[0]['value']))
        logging.debug("Increment element " + self.name + ' = ' + str(self.output[0]['value']))


class Decrement(Element):

    def __init__(self, name,val=1.0,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)

        if typeChecker.isThisType(type):
            if type == VALUETYPES.STRING or type == VALUETYPES.BOOL:
                Exception("Increment.init(): Provided type is not supported.")
            else:
                self.createFlexInputPin()
                self.createPin('out', type)
                if ~typeChecker.isType(val, type):
                    self.myInc = typeChecker.castToType(val, type)

    def doFunc(self):
        if self.output[0]['type']==VALUETYPES.REAL or self.output[0]['type']==VALUETYPES.INT:
            self.output[0]['value'] = self.input[0]['value'] - self.myInc
        if self.output[0]['type']==VALUETYPES.VECTOR:
            for i in range(0,len(self.input[0]['value'])):
                self.output[0]['value'][i] = self.input[0]['value'][i] - self.myInc
        if self.output[0]['type']==VALUETYPES.MATRIX:
            for i in range(0,len(self.input[0]['value'])):
                pom = self.input[0]['value'][i]
                for j in range(0, len(pom)):
                    self.output[0]['value'][i][j] = self.input[0]['value'][i][j] - self.myInc

        #print(self.name + ' = ' + str(self.output[0]['value']))
        logging.debug("Decrement element " + self.name + ' = ' + str(self.output[0]['value']))



class Canvas(Element):

    def __init__(self,name,options = None):
        super().__init__(name, options)
        self.elem_list = []                                         # contains the list of all elements inside Canvas
        # self.priority_list = []                                     # contains the list of priorities of elements
        self.queue = Q.PriorityQueue()                              # the execution queue with priorities
        self.not_my_elem_list = []                                  # contains the neighboring elements
        self.not_my_elem_canvases = []                              # Canvases containing the neighbor elements
        self.start_list = []                                        # contains the starting elements
        self.queueElem = []                                         # contains all the elements that are inside the queue (only unsorted)


    def add_element(self, elem):
        if elem:
            if elem in self.elem_list:
                #print("Warning! Canvas.add_element(): Element is already in the canvas.")
                logging.warning("Warning! Canvas.add_element(): Element is already in the canvas.")
                return
            if elem in self.not_my_elem_list:
                raise Exception("Canvas.add_element(): Element cannot be inside and outside of a Canvas at the same time.")
#            if elem.priority<self.priority:
#                self.priority = elem.priority
            elem.myCanvas = self
            self.elem_list.append(elem)
            # self.priority_list.append(elem.priority)

            # add elements with highest priority to be executed first
            if len(self.start_list)>0:
                if self.start_list[0].priority>elem.priority:
                    self.start_list.clear()
                    self.start_list.append(elem)
                elif self.start_list[0].priority==elem.priority:
                    self.start_list.append(elem)
            else:
                self.start_list.append(elem)

    def connect(self, right, pinout, pinin):
        if not isinstance(right, Element):
            Exception("Provided argument is not an element. Cannot connect.")
        self._add_neighbor(right)

    def _add_neighbor(self, elem):
        if elem:
            if elem in self.elem_list:
                raise Exception("Element cannot be inside and outside of a canvas at the same time.")
            self.not_my_elem_list.append(elem)
            self.not_my_elem_canvases.append(elem.myCanvas)

    def _add_to_queue(self, elem):
        if elem in self.not_my_elem_list:                                               # adding to the neighbor Canvas
            #time.sleep(1)
            #print('my name ' + self.name + ' and elem name ' + elem.name)
            #print("give token to neighbor : " + (self.not_my_elem_canvases[self.not_my_elem_list.index(elem)]).name + "." + elem.name)
            logging.debug("give token to neighbor : " + (self.not_my_elem_canvases[self.not_my_elem_list.index(elem)]).name + "." + elem.name)
            self.not_my_elem_canvases[self.not_my_elem_list.index(elem)]._add_to_queue(elem)
            self._add_to_queue(self.not_my_elem_canvases[self.not_my_elem_list.index(elem)])
            #self.queue.put((self.priority_list[self.elem_list.index(elem)], elem))
            #time.sleep(1)
            return
        if elem not in self.elem_list:                                                  # something is wrong, this should not happen
            return
        if elem not in self.queueElem:                                                  # add to my own Canvas processing queue
            #print("Adding element " + elem.name + " to processing queue of canvas " + self.name)
            logging.debug("Adding element " + elem.name + " to processing queue of canvas " + self.name)
            # self.queue.put((self.priority_list[self.elem_list.index(elem)],elem))
            self.queue.put((elem.priority, elem))                                       # double bracket here is not an error
            self.queueElem.append(elem)

    def _get_from_queue(self):
        if (~self.queue.empty()):
            elem = self.queue.get()
            elem = elem[1]
            self.queueElem.remove(elem)
            return elem
        else:
            return 0

    def compile(self):
        for i in range(0,len(self.start_list)):
            self._add_to_queue(self.start_list[i])
        for i in range(0, len(self.elem_list)):
            self.elem_list[i].compile()

    def decompile(self):
        for i in range(0, len(self.elem_list)):
            self.elem_list[i].decompile()

    def doFunc(self):

        while True:
            if self.queue.empty():
                pom = True
                for i in range(0, len(self.start_list)):
                    self._add_to_queue(self.start_list[i])
                    if self.start_list[i].myCondition.isCondition() and not self.start_list[i].myCondition.stateCond('rep'):
                        #self._add_to_queue(self.start_list[i])
                        pom = False
                if pom:
                    break
                # else:
                #     for i in range(0, len(self.start_list)):
                #         self._add_to_queue(self.start_list[i])

            elem = self._get_from_queue()
            #print('Now processing element: ' + elem.name)
            logging.debug('Now processing element: ' + elem.name)
            elem.execute()
            if elem.forward():                                                  # this one just copies outputs to the next elements inputs
                for i in range(0, len(elem.nextElem)):                          # this one puts these next elements into the queue for execution
                    pom = elem.nextElem[i]
                    # map the output of elem to the input of nextElem
                    #(pom[ELEMADDRESS.NEXTELEM]).input[pom[ELEMADDRESS.PININ]-1] = elem.output[pom[ELEMADDRESS.PINOUT]-1]
                    # add the nextElem to the execution queue
                    self._add_to_queue(pom[ELEMADDRESS.NEXTELEM])

        for i in range(0, len(self.start_list)):                            # this one is much needed. It is there to initialize for the next start of the canvas (useful for HLA and other components)
            self._add_to_queue(self.start_list[i])

        #print('exit ' + self.name)
        logging.debug('exit ' + self.name)

    def start(self):
        self.compile()
        self.execute()
        self.decompile()



# This class is created as an interface to the world.
# Any Element that has a connection to an external process should implement this.
class WorldConnector(object):

    def __init__(self):
        return

    def connectToTheWorld(self):
        return

    def disconnectFromTheWorld(self):
        return



class Reflector(Element):

    def __init__(self,name,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)
        self.createFlexInputPin()
        self.createPin('out', type)

    def doFunc(self):
        copyMachine.copyContent(self.output[0], self.input[0])
        #print(self.name + ' : ' + str(self.input[0]))
        logging.debug("Reflector element " + self.name + ' : ' + str(self.input[0]))


class Acknowledge(Element):

    def __init__(self,name,type,options=None):
        super().__init__(name,options)
        self.createFlexInputPin()
        self.createPin('out', type)

    def doFunc(self):
        if self.input[0] != EMPTYMSG.copy():
            self.output[0]['value'] = 1.0           # TODO: change this to string type (HLA must support it)
        #print(self.name + ' : ' + str(self.input[0]))
        logging.debug("Acknowledge element " + self.name + ' : ' + str(self.input[0]))


EMPTYCMD = {'cmd':'', 'out':False}      # if 'out' is True, the output of the command will be mapped onto output of Element


class TypeConversion(Element):

    def __init__(self,name,type,options=None):
        super().__init__(name,options)
        if type==VALUETYPES.VECTOR or type==VALUETYPES.MATRIX:
            Exception("TypeConversion.init(): Type conversion to/from VECTOR or MATRIX is not possible.")
        else:
            self.createFlexInputPin()
            self.createPin('out', type)

    def doFunc(self):

        if self.output[0]['type'] == self.input[0]['type']:
            self.output[0]['value'] = self.input[0]['value']
            return

        elif self.output[0]['type']==VALUETYPES.INT:                                # convert into INT
            if self.input[0]['type']==VALUETYPES.BOOL:
                self.output[0]['value'] = int(self.input[0]['value'] == 'True')
            elif self.input[0]['type']==VALUETYPES.REAL:
                self.output[0]['value'] = int(round(self.input[0]['value']))
            elif self.input[0]['type']==VALUETYPES.STRING:
                self.output[0]['value'] = int(self.input[0]['value'])
            elif self.input[0]['type']==VALUETYPES.VECTOR:
                Exception("Cannot convert VECTOR to INT.")
            #     for i in self.input[0]['value']:
            #         self.output[0]['value'].append(int(round(self.input[0]['value'][i])))
            elif self.input[0]['type'] == VALUETYPES.MATRIX:
                Exception("Cannot convert MATRIX to INT.")
            #     for i in self.input[0]['value']:
            #         pom = []
            #         for j in self.input[0]['value'][i]:
            #             pom.append(int(round(self.input[0]['value'][i][j])))
            #         self.output[0]['value'].append(pom)

        elif self.output[0]['type']==VALUETYPES.BOOL:                               # convert into BOOL
            if self.input[0]['type']==VALUETYPES.INT:
                self.output[0]['value'] = ~(self.input[0]['value'] == 0)
            elif self.input[0]['type']==VALUETYPES.REAL:
                self.output[0]['value'] = ~(self.input[0]['value'] == 0.0)
            elif self.input[0]['type']==VALUETYPES.STRING:
                self.output[0]['value'] = ~(self.input[0]['value'] == '')
            elif self.input[0]['type']==VALUETYPES.VECTOR or self.input[0]['type']==VALUETYPES.MATRIX:
                self.output[0]['value'] = ~(len(self.input[0]['value']) == 0)

        elif self.output[0]['type']==VALUETYPES.REAL:                               # convert into REAL
            if self.input[0]['type']==VALUETYPES.BOOL:
                self.output[0]['value'] = float(self.input[0]['value'] == 'True')
            elif self.input[0]['type']==VALUETYPES.INT:
                self.output[0]['value'] = float(self.input[0]['value'])
            elif self.input[0]['type']==VALUETYPES.STRING:
                self.output[0]['value'] = float(self.input[0]['value'])
            elif self.input[0]['type']==VALUETYPES.VECTOR:
                return
#                for i in self.input[0]['value']:
#                    self.output[0]['value'].append(float(round(self.input[0]['value'][i])))
            elif self.input[0]['type'] == VALUETYPES.MATRIX:
                return
#                for i in self.input[0]['value']:
#                    pom = []
#                    for j in self.input[0]['value'][i]:
#                        pom.append(int(round(self.input[0]['value'][i][j])))
#                    self.output[0]['value'].append(pom)

        elif self.output[0]['type']==VALUETYPES.STRING:                             # convert into STRING
            if self.input[0]['type']==VALUETYPES.BOOL or \
                            self.input[0]['type']==VALUETYPES.INT or \
                            self.input[0]['type']==VALUETYPES.REAL:
                self.output[0]['value'] = str(self.input[0]['value'])
            elif self.input[0]['type'] == VALUETYPES.VECTOR:
                Exception("Cannot convert VECTOR to STRING.")
            elif self.input[0]['type'] == VALUETYPES.MATRIX:
                Exception("Cannot convert MATRIX to STRING.")

class Index(Element):

    def __init__(self,name,x,y=0,type=VALUETYPES.REAL,options=None):        # if matrix comes in and y=0 that is the same as pulling out the last column
        super().__init__(name,options)
        self.createFlexInputPin()
        if x == []:
            self.x = "all"
            type = VALUETYPES.VECTOR
        else:
            self.x = x-1
        if y == []:
            self.y = "all"
            type = VALUETYPES.VECTOR
        else:
            self.y = y-1

        if x==[] and y==[]:
            type = VALUETYPES.MATRIX

        self.createPin('out', type)

    def doFunc(self):
        if self.input[0] != EMPTYMSG:
            pom = self.input[0]['value']

            if self.input[0]['type'] == VALUETYPES.VECTOR:
                if self.x == 'all':
                    self.output[0]['value'] = pom
                else:
                    self.output[0]['value'] = pom[self.x]
            elif self.input[0]['type'] == VALUETYPES.MATRIX:
                if self.y == 'all':
                    self.output[0]['value'] = pom[self.x]
                elif self.x == 'all':
                    pp = []
                    for i in range(0,len(pom)):
                        pp.append(pom[i][self.y])
                    self.output[0]['value'] = pp
                elif self.y == 'all' and self.x == 'all':
                    self.output[0]['value'] = pom
                else:
                    self.output[0]['value'] = pom[self.x][self.y]
            else:
                Exception("Unrecognized input type. Demux must have VECTOR or MATRIX as input.")

        #print(self.name + ' : ' + str(self.input[0]))
        logging.debug("Index element " + self.name + ' : ' + str(self.input[0]))

class Mux(Element):

    def __init__(self,name,size,type=VALUETYPES.VECTOR,options=None):
        super().__init__(name,options)
        self.createPin('out', type)
        for i in range(0,size):
            self.createFlexInputPin()
        self.type = type


    def doFunc(self):

        outVar = None
        allRight = True
        if self.type == VALUETYPES.VECTOR:
            for i in range(0,len(self.input)):
                if self.input[i]['type'] != VALUETYPES.VECTOR and self.input[i]['type'] != VALUETYPES.REAL:
                    allRight = False
                    break
        elif self.type == VALUETYPES.MATRIX:
            l = len(self.input[0]['value'])
            for i in range(0, len(self.input)):
                if self.input[i]['type'] != VALUETYPES.VECTOR:
                    allRight = False
                    break
                if len(self.input[i]) != l:
                    allRight = False
                    break
        elif self.type == VALUETYPES.STRING:
            for i in range(0, len(self.input)):
                if self.input[i]['type'] != VALUETYPES.STRING:
                    allRight = False
                    break
        else:
            allRight = False

        if not allRight:
            Exception("Error! Mux.doFunc(): Inputs are not compatible.")


        if self.type == VALUETYPES.REAL or self.type == VALUETYPES.VECTOR:
            outVar = []
            for i in range(0,len(self.input)):
                pom = []
                if self.input[i]['type'] == VALUETYPES.VECTOR:
                    pom = self.input[i]['value']
                if self.input[i]['type'] == VALUETYPES.REAL:
                    pom.append(self.input[i]['value'])
                outVar.append(pom)
            outVar = [item for sublist in outVar for item in sublist]

        if self.type == VALUETYPES.STRING:
            outVar = ""
            for i in range(0, len(self.input)):
                outVar += self.input[i]['value']

        self.output[0]['value'] = outVar

        #print(self.name + ' : ' + str(self.output[0]))
        logging.debug("Mux element " + self.name + ' : ' + str(self.output[0]))


class Demux(Element):

    def __init__(self,name,size,type=VALUETYPES.REAL,options=None):
        super().__init__(name,options)
        self.createFlexInputPin()
        for i in range(0,size):
            self.createPin('out', type)
        if options and options['ind']:
            self.myInd = options['ind']
        else:
            self.myInd = None


    def doFunc(self):
        if self.input[0] != EMPTYMSG:
            pom = self.input[0]['value']

            if self.input[0]['type'] == VALUETYPES.VECTOR and self.output[0]['type'] == VALUETYPES.REAL:
                if self.myInd:
                    for i in range(0,len(self.output)):
                        self.output[i]['value'] = pom[self.myInd[i]-1]
                else:
                    for i in range(0,len(self.output)):
                        self.output[i]['value'] = pom[i]
            elif self.input[0]['type'] == VALUETYPES.MATRIX and self.output[0]['type'] == VALUETYPES.VECTOR:
                if self.myInd:
                    for i in range(0, len(self.output)):
                        self.output[i]['value'] = pom[self.myInd[i]-1]
                else:
                    for i in range(0,len(self.output)):
                        self.output[i]['value'] = pom[i]
            elif self.input[0]['type'] == VALUETYPES.MATRIX and self.output[0]['type'] == VALUETYPES.REAL:
                if self.myInd:
                    for i in range(0,len(self.output)):
                        for j in range(0, len(pom)):
                            self.output[i]['value'] = pom[self.myInd[i]-1][j]
                else:
                    for i in range(0, len(self.output)):
                        for j in range(0, len(pom)):
                            self.output[i]['value'] = pom[i][j]
            else:
                Exception("Error! Demux.doFunc(): Unrecognized input type. Demux must have VECTOR or MATRIX as input.")

        #print(self.name + ' : ' + str(self.input[0]))
        logging.debug("Demux element " + self.name + ' : ' + str(self.input[0]))
        for i in range(0,len(self.output)):
            #print(self.name + ' : ' + str(self.output[i]))
            logging.debug("Demux element " + self.name + ' : ' + str(self.output[i]))



class ValueToTime(Element):

    def __init__(self, name, options=None):
        super().__init__(name,options)
        self.createFlexInputPin()
        self.createPin('out', VALUETYPES.REAL)

    def doFunc(self):
        self.output[0]['value'] = self.input[0]['time']


class TimeToValue(Element):
    def __init__(self, name, options=None):
        super().__init__(name,options)
        self.createPin('in', VALUETYPES.REAL, 't')                  # pin 1 (list index 0) is time pin
        self.createFlexInputPin()
        self.createPin('out', VALUETYPES.REAL)

    def doFunc(self):
        self.output[0]['time'] = self.input[0]['value']
        self.output[0]['value'] = self.input[1]['value']


class WhileLoop(Canvas):
    def __init__(self, name, el, cnd, io, options=None):
        super().__init__(name, options)
        if isinstance(el,Element):
            self.myCndElem = el
            self.add_element(self.myCndElem)

        self.myCnd = cnd
        self.myIO = io

    def compile(self):
        super().compile()
        if self.myIO=='in':
            self.myCndElem.setInputCondition(self.myCnd)
        elif self.myIO=='out':
            self.myCndElem.setOutputCondition(self.myCnd)
        else:
            Exception("Condition.setCondition(): Condition can either be 'in' or 'out'. Incorrect string provided.")

    def doFunc(self):
        super().doFunc()
        self.compile()

class ForLoop(Canvas):
    def __init__(self, name, el, cnt, options=None):
        super().__init__(name,options)
        if isinstance(el,Element):
            self.myCndElem = el
            self.add_element(self.myCndElem)

        self.myCnt = cnt
        self.myCndElem.setCounterCondition(self.myCnt)

    def doFunc(self):
        super().doFunc()

        #print(self.name + ' : Performed ' + str(self.myCnt) + " runs." )
        logging.debug("ForLoop element " + self.name + ' : Performed ' + str(self.myCnt) + " runs.")
        self.compile()

    def compile(self):
        super().compile()

        self.myCndElem.resetCondition()
        self.myCndElem.setCounterCondition(self.myCnt)

class GenericElement(Element):

    def __init__(self,name,Nin,Nout,func=None,type=VALUETYPES.DEFAULT,options=None):
        super().__init__(name,options)
        for i in range(0,Nin):
            if 'notflexpin' in options:
                self.createPin('in',type)
            else:
                self.createFlexInputPin()
        for i in range(0,Nout):
            self.createPin('out', type)

        self.myFunc = func

    def doFunc(self):
        if self.myFunc:
            self.myFunc()



