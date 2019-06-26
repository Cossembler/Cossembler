# Cossembler
Cossembler - rapid prototyping tool for energy system co-simulations

Cossembler is written in Python 3.6 and published under GPL 3.0. For the full text of the license see http://www.gnu.org/licenses/

For installation instructions, look further below.

Cossembler is intended for rapid prototying of co-simulations for energy system integration studies. Co-simulation is a combination of two or more simulation tools or computational models, and Cossembler provides easy means of their integration. Cossembler goal is not high computational performance, but instead, fast assembly of a co-simulation prototype.

Cossembler architecture is minimalistic, defining only the most relevant features. The user is welcomed to extend its capabilities as needed.

Cossembler is a block-modeling tool, and hence, it is intended to be used by defining and connecting blocks into a co-simulation. These blocks link to different tools in the background.

Cossembler architecture is developed in layers, with each layer serving a different purpose: the engine layer, the adapter layer, the functionality layer and the application layer.

Engine layer - This is the Cossembler engine which enables block modeling phylosophy. The user or developer will very likely never have to go here.

Adapter layer - Cossembler currently integrates adapters for the following tools
1) Matlab
2) FMPy
3) CERTI HLA
These adapters allow integartion of the mentioned tools.

Functionality layer - Cossembler can be used to engage different functionalities of the previously mentioned tools. The functionalities are engaged through function calls. Currently, this layer is used to engage:
1) MatPower (Matlab)
2) MatPower-MOST (Matlab)
3) Modelica-OpenIPSL (FMPy)
This layer is not indented to be used directly by the user, but it serves as a bridge between the application layer and the adapter layer. In case one needs to extend the functionalities of Cossembler, one might have to work with this layer. 

Application layer - Cossembler provides different blocks relevant for energy system co-simulations. These blocks link through the functionality layer to different simulation tools and are intended to be used for rapid prototyping. The blocks include, for example, power flow block (based currently on MatPower), dynamic simulation block (based currently on OpenIPSL), optimal power flow block, etc.

The tool can directly integrate simulation tools if they have Python 3 API and can be installed on the same operating system. If this is not possible, the user/developer has to perform integration using a co-simulation master. Currently, only CERTI HLA is supported as a master. The blocks for its integration are available in Cossembler and have to be connected with other blocks in the same way as any other two blocks.

Installation instructions

Run test_eng.py to test if Cossembler engine is running succesfully.

Matlab integration
To integrate Matlab with Cossembler, following the instructions for linking Matlab to Python should be sufficient
https://www.mathworks.com/help/matlab/matlab-engine-for-python.html
To use PowerFlow and other common steady state power system computation method, make sure to install MatPower (and optionally its extension pack MOST).
Cossembler was tested with Matlab R2017b, MatPower 6 and MOST 1.0.1.
Run test_powerflow.py to test Matlab and MatPower integration (you must install both first; MOST is not required to run the test).

FMPy integration
FMPy is an adapter for integration of FMU (Functional Mockup Units) with Python (https://fmpy.readthedocs.io/en/)
With this adapter any FMU packaged model can be simulated. Cossembler was only tested with OpenIPSL power system models (https://github.com/OpenIPSL/OpenIPSL), developed in Modelica, and compiled to FMUs using OpenModelica 1.12 development environment (https://openmodelica.org/). The FMU's are packaged as FMU for co-simulation version 2.
In order to run a co-simulation with Cossembler, only FMPy needs to be installed and operational in runtime. In addition, FMPy must be supplied with FMUs to simulate. These FMUs are packaged ahead of simulation run and their creation is out of scope of Cossembler's jurisdiction.
This distribution at the moment does not include any OpenIPSL FMUs. OpenIPSL models are published under MPL which is not compatible with GPL, and hence, OpenIPSL models will never be included as a part of Cossembler distribution. For installation testing purposes, we provide a simple first-order transfer function FMU (called transferFX.fmu). We also provide two test files, one which uses transferFX.fmu for testing and another which can be used with OpenIPSL FMUs much more easily, but we direct the user to OpenIPSL community in order to obtain the models first (Note: after obtaining the models, make sure to re-declare Modelica parameters as Modelica inputs/outputs if these are to be connected through Cossembler as interface variables).
Run test_fmpy.py to test if FMPy with transferFX.fmu models is succefully integrated (make sure you already installed FMPy).
