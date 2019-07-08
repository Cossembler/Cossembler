
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
logging.basicConfig(level=logging.DEBUG)

from cossembler.eng import Canvas
from cossembler.eng import Source
from cossembler.eng import Addition
from cossembler.eng import Sink
from cossembler.eng import Reflector
from cossembler.eng import WhileLoop
from cossembler.eng import ForLoop
from cossembler.eng import PRIORITY

# only one test can be active at a time

TEST_WHILE = False      # tests while loop
TEST_FOR = False        # tests for loop
TEST_LOOP = True        # tests a custom loop created by putting a condition on any block
                        # this kind of setup can be extended in different variants to get excotic behavior
                        # in all three cases in this file, answer = 28.0

def Main():

    if not (TEST_FOR or TEST_WHILE or TEST_LOOP):
        print("At least one test has to be active at a time.")
        return
    elif (TEST_LOOP + TEST_WHILE + TEST_FOR) > 1:
        print("Only one test can be active at a time.")
        return
    else:

        wrld = Canvas('world')
        mini = 0                    # a canvas that acts as a loop
                                    # all elements inside this canvas will be looped as many times as settings declare
                                    # settings are created in different ways as described below
        elem1 = Source('const1',5.0)
        elem3 = Source('const3',3.0)
        elem4 = Addition('addit1')
        elem5 = Addition('addit2')
        elem6 = Sink('sink1')


        if TEST_LOOP:
            mini = Canvas('mini', options={'priority':PRIORITY.TOP})
            elem2 = Reflector('ref')
            mini.add_element(elem2)
            mini.add_element(elem4)
        if TEST_WHILE:
            mini = WhileLoop('mini', elem4, "addit1.y1>21", 'in', options={'priority':PRIORITY.TOP})  # 'change this to out to get 23.0'
            elem2 = 0
        if TEST_FOR:
            mini = ForLoop('mini', elem4, 5, options={'priority':PRIORITY.TOP})
            elem2 = 0

        mini.add_element(elem1)
        wrld.add_element(elem3)
        wrld.add_element(elem5)
        wrld.add_element(elem6)
        wrld.add_element(mini)

        elem1.connect(elem4, 1, 1)
        if TEST_LOOP:
            elem2.connect(elem4, 1, 2)
            elem4.connect(elem2, 1, 1)
        if TEST_WHILE:
            elem4.connect(elem4, 1, 2)
        if TEST_FOR:
            elem4.connect(elem4, 1, 2)

        elem3.connect(elem5, 1, 1)
        elem4.connect(elem5, 1, 2)
        elem5.connect(elem6, 1, 1)


        if TEST_LOOP:
            elem2.setOutputCondition("ref.y1>21")


        wrld.start()



Main()

