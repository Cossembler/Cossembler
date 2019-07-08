
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


import matlab.engine
from cossembler.eng import Element
from cossembler.eng import WorldConnector
from cossembler.eng import VALUETYPES

class MATLAB(Element,WorldConnector):

    def __init__(self,name,type,options=None):
        super().__init__(name,options)
        self.createFlexInputPin()
        self.createPin('out', type)
        self.cmd = []
        self.var = []

    def setCommand(self, cmd):  # sets a command to be ran in the tool
        self.cmd.append({'cmd': cmd, 'out': False})

    def setOutCommand(self, cmd):  # sets a command to be ran in the tool + retrieves the output
        self.cmd.append({'cmd': cmd, 'out': True})

    def setVar(self, var):  # sets variables to be initialized with the Element inputs
        self.var.append(var)

    def doFunc(self):
        for i in range(0, len(self.var)):
            self.eng.workspace[self.var[i]] = self.input[i]['value']
            if self.input[i]['type'] == VALUETYPES.VECTOR:                                  # TODO: this might not work for matrices
                y = self.eng.evalc(self.var[i]+"=double(cell2mat("+self.var[i]+"))'")

        cnt = 0

        for i in range(0, len(self.cmd)):
            print(self.cmd[i])
            pom = []
            if self.cmd[i]['out']:
                y = self.eng.eval(self.cmd[i]['cmd'])
                if isinstance(y,complex) or isinstance(y,dict) or isinstance(y,list):
                    raise Exception("MATLAB.doFunc(): MATLAB returned a type that is not supported by the platform.")
                if 'size' in dir(y):
                    k = len(y.size)
                else:
                    k = 0
                if k>0:
                    for i in range(0,y.size[0]):
                        pp = []
                        for j in range(0,y.size[1]):
                            pp.append(y[i][j])
                        if y.size[0]==1:
                            pom = pp
                        else:
                            pom.append(pp)
                else:
                    pom = y
                print(y)
                if (cnt>=len(self.output)):
                    print("Error! Trying to assign a value to a nonexisting output pin. Create a new output pin to communicate this value.")
                if isinstance(pom,float):
                    self.output[cnt]['value'] = pom
                else:
                    if len(pom)==1:
                        self.output[cnt]['value'] = pom[0]
                    else:
                        self.output[cnt]['value'] = pom
                cnt += 1
            else:
                y = self.eng.evalc(self.cmd[i]['cmd'])
                print(y)


    def connectToTheWorld(self):
        self.eng = matlab.engine.start_matlab()

    def disconnectFromTheWorld(self):
        self.eng.quit()

    def compile(self):
        self.connectToTheWorld()

    def decompile(self):
        self.disconnectFromTheWorld()
