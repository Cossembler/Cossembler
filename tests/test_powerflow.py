
from cossembler.eng import Canvas
from cossembler.eng import Source
from cossembler.eng import Sink
from cossembler.app import PowerFlow
from cossembler.eng import Index


# this file tests MatPower integration. The result observed at sink is the phase angle of the third bus = -12.759

PFoptions = {
    'tool': "MATPOWER",
    'model': "case14",
    'model_path' : "",
    'inputs': ['Pd(2)'],  #     'inputs' can be : ['Pd', 'Qd', 'Pg', 'Vg', 'oltc', 'slack', 'elAct'],
    'outputs': ['Vm', 'Va', 'Pd', 'Qd', 'Pg', 'Qg', 'Pflow', 'Qflow', 'PQloss']     # 'outputs' can be : ['Vm', 'Va', 'Pd', 'Qd', 'Pg', 'Qg', 'Pflow', 'Qflow', 'PQloss']
}

def Main():

    wrld = Canvas('world')

    elemPF = PowerFlow('PowerFlow',PFoptions)

    elem1 = Source('const1',23.0)
    elem2 = Sink('sink1')
    elemI = Index("Index", 3)

    wrld.add_element(elem1)
    wrld.add_element(elem2)
    wrld.add_element(elemPF)
    wrld.add_element(elemI)

    elem1.connect(elemPF,1,'Pd')
    elemPF.connect(elemI,'Va',1)
    elemI.connect(elem2, 1, 1)

    wrld.start()

Main()
