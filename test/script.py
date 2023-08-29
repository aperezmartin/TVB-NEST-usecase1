import EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers
# Co-Simulator imports
from EBRAINS_Launcher.common import args
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import enums
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import variables
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import comm_settings_xml_manager
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import services_deployment_xml_manager
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import plan_xml_manager
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import xml_tags
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers.variables import CO_SIM_EXECUTION_ENVIRONMENT
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import variables_manager
# from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import parameters_xml_manager
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import actions_xml_manager
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers import arranger
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers import configurations_manager
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories
#from EBRAINS_Launcher.launching_manager import LaunchingManager


import os, sys, copy, pytest, argparse, json, subprocess, shutil, logging
from dataclasses import dataclass

#import test.models.TVB_NEST_1 as usc_1

os.environ["mylocalbranch"] = "myremotefork"
os.environ["global_settings"] = "EBRAINS_WorkflowConfigurations/general/global_settings.xml"

os.environ["action-plan-Mock_1"] = "test/XML/mock_1_plan.xml"
os.environ["action-plan-Mock_2"] = " "
os.environ["action-plan-TVB_NEST_1"] = "userland/configs/local/plans/cosim_alpha_brunel_local.xml"

"""
GLOBAL_DICT={"global_settings":os.environ["CO_SIM_TEST_GENERAL_SETTINGS"],
             "action_plan":os.environ["CO_SIM_TEST_ACTION_PLAN"],
             "interactive":False}
class MyARGS:
    def __init__(self, d):
        self.__dict__.update(d)
        #for k, v in d.items():
            #setattr(self,k,v)
            #self.__dict__[k] = v
            #if isinstance(k, (list, tuple)):
            #    setattr(self, k, [MyARGS(x) if isinstance(x, dict) else x for x in v])
            #else:
            #    setattr(self, k, MyARGS(v) if isinstance(v, dict) else v)

    def __getitem__(self, v):
        return self.__dict__[v]
"""

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
EBRAINS_MODULE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")) 

def remove_old_simulations(simulations_paths):
    try:
        print(">>",len(simulations_paths))
        if len(simulations_paths) > 0:
            for old_path in simulations_paths:
                shutil.rmtree(old_path)
        return True
    except Exception as e:
        print("Error Deleting old test simulations")
        return False

def get_output_path():

    output_path = os.path.join(EBRAINS_MODULE_PATH, "test", "Cosimulation_outputs")

    dirlist = []
    for filename in os.listdir(output_path):
        path = os.path.join(output_path,filename)
        if os.path.isdir(path) and filename.lower().startswith("vagrant_outputs_"):
            dirlist.append(path)
    
    return dirlist

########################

class TestCoSimulator():

    def test_list_outputs(self):
        simulations_paths = get_output_path()
        print(simulations_paths)

        assert len(simulations_paths) >= 0
        
    #@pytest.hookimpl(hookwrapper=True)
    def test_cosim_Mock_1_MPIcommunication(self):
        simulations_paths = get_output_path()
        assert remove_old_simulations(simulations_paths)
        
        cmd = "./setup.sh "+os.environ["mylocalbranch"]+" "+os.environ["global_settings"]+" "+os.environ["action-plan-Mock_1"]+" "
        print(cmd)
        
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)
        out, err = process.communicate()
        process.wait()
        #Check normal Standart Error

        assert len(out) == 0 and len(err) == 0
        """
        """
    
"""
class TestUseCase():
    def test_cosim_NEST_TVB(self):

        simulations_paths = get_output_path()
        assert remove_old_simulations(simulations_paths)
        
        #Launchin the simulation
        print("Launching CoSimulation")
        cmd = "./setup.sh "+os.environ["mylocalbranch"]+" "+os.environ["global_settings"]+" "+os.environ["action-plan-TVB_NEST_1"]+" "
        print(cmd)

        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)
        out, err = process.communicate()
        process.wait()
        #Check normal Standart Error
        #assert len(out) == 0 and len(err) == 0
        
        #Check if simulation created the folder
        paths = get_output_path()
        assert len(paths) >= 0
        print("Current Test Cosimulation path", paths)

    def test_NEST_TVB_2(self):
        #TODO
        assert True
    
    def test_Arbor(self):
        #TODO
        assert True
    
    def test_LFPy(self):
        #TODO
        assert True
    
    def test_NEST_Desktop_Insite(self):
        #TODO
        assert True

        """

