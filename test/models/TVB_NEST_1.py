from dataclasses import dataclass
import numpy as np

from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.configurations_manager import ConfigurationsManager
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories


############  MODEL  ###############

"""
# Adatper description
- TVB adapter
- NEST adapter
- Hub adapter

Adapter(init, start, end) -> Simulator(init, config, run) <- Parameter
"""


############  Launcher  ###############
class Launcher():
    def __init__(self):
        self._configurations_manager = ConfigurationsManager()
        self._logger_settings = self._configurations_manager.get_configuration_settings('log_configurations', 
                                                                                         self.__args.global_settings)
        
         
############  NEST  ###############

class Simulator_NEST_adapter():
    def __init__(self, p_configurations_manager, p_log_settings,
                 p_interscalehub_addresses,
                 is_monitoring_enabled=False,
                 sci_params_xml_path_filename=None):
        self.configurations_manager = p_configurations_manager
        self.log_settings = p_log_settings
        self.interscalehub = p_interscalehub_addresses
        
        self.logger = self._configurations_manager.load_log_configurations(
                                                    name="NEST_Adapter",
                                                    log_configurations=self._log_settings,
                                                    target_directory=DefaultDirectories.SIMULATION_RESULTS)
        self.path_to_parameters_file = self._configurations_manager.get_directory(
                                                    directory=DefaultDirectories.SIMULATION_RESULTS)
        
        self.simulator = Simulator_NEST(self.configurations_manager,self.log_settings, self.path_to_parameters_file,)
        
    def execute_init_command(self):
        self.logger.debug("INIT command is executed")
        self.simulator.configure()

    def execute_start_command(self, global_minimum_step_size):
        self.logger.debug('START command is executed')
        self.simulator.simulate()
         
    def execute_end_command(self):
        self.logger.debug('END command is executed')

@dataclass
class Simulator_NEST_Parameters():
    list_spikes= np.random.choice([0, 1], size=(10,), p=[1./3, 2./3])

class Simulator_NEST():
    def __init__(self, p_configurations_manager, p_log_settings, sci_params, path_parameter):
            self._log_settings = p_log_settings
            self._configurations_manager = p_configurations_manager
            self.__logger = self._configurations_manager.load_log_configurations(
                name="SimulatorNEST",
                log_configurations=self._log_settings,
                target_directory=DefaultDirectories.SIMULATION_RESULTS)
            
            self.__sci_params = sci_params
            self.__params = Simulator_NEST_Parameters()
            self.results_path = path_parameter

    def configure(self,NEST_to_TVB_address,TVB_to_NEST_address):
        self.__logger.info('configuration NEST done!')
    
    def simulate(self):
        self.__logger.info('start the simulation NEST')
        #TODO MPI
        self.__logger.info('exit')

############  TVB  ###############

class Simulator_TVB_adapter():
    def __init__(self, p_configurations_manager, p_log_settings,
                 p_interscalehub_addresses,
                 is_monitoring_enabled=False,
                 sci_params_xml_path_filename=None):
        self.configurations_manager = p_configurations_manager
        self.log_settings = p_log_settings
        self.interscalehub = p_interscalehub_addresses
        
        self.logger = self._configurations_manager.load_log_configurations(
                                                    name="TVB_Adapter",
                                                    log_configurations=self._log_settings,
                                                    target_directory=DefaultDirectories.SIMULATION_RESULTS)
        self.path_to_parameters_file = self._configurations_manager.get_directory(
                                                    directory=DefaultDirectories.SIMULATION_RESULTS)
        
        self.simulator = Simulator_TVB(self.configurations_manager,self.log_settings, self.path_to_parameters_file,)
        
    def execute_init_command(self):
        self.logger.debug("INIT command is executed")
        self.simulator.configure()

    def execute_start_command(self, global_minimum_step_size):
        self.logger.debug('START command is executed')
        self.simulator.simulate()
         
    def execute_end_command(self):
        self.logger.debug('END command is executed')
        
@dataclass
class Simulator_TVB_Parameters():
    regions_num = 68
    regions = np.random.uniform(low=10, high=200, size=(regions_num,))
    weights = np.random.uniform(low=0.5, high=200, size=(regions_num,))
    tract_lengths = np.random.uniform(low=0.5, high=200, size=(regions_num,))

class Simulator_TVB():
    def __init__(self, p_configurations_manager, p_log_settings, sci_params, path_parameter):
            self._log_settings = p_log_settings
            self._configurations_manager = p_configurations_manager
            self.__logger = self._configurations_manager.load_log_configurations(
                name="SimulatorTVB",
                log_configurations=self._log_settings,
                target_directory=DefaultDirectories.SIMULATION_RESULTS)
            
            self.__sci_params = sci_params
            self.__params = Simulator_TVB_Parameters()
            self.results_path = path_parameter

    def configure(self,NEST_to_TVB_address,TVB_to_NEST_address):

        self.__logger.info('configuration TVB done!')
    
    def simulate(self):
        self.__logger.info('start the simulation TVB')
        #TODO MPI

        self.__logger.info('exit')