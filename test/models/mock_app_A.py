import os, sys, pickle, base64, ast, numpy as np
from dataclasses import dataclass
from mpi4py import MPI

from EBRAINS_InterscaleHUB.Interscale_hub.interscalehub_enums import DATA_EXCHANGE_DIRECTION
from EBRAINS_RichEndpoint.application_companion.common_enums import INTEGRATED_INTERSCALEHUB_APPLICATION as INTERSCALE_HUB
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories

@dataclass
class Simulator_A_Parameters():
    regions_num = 68
    regions = np.random.uniform(low=10, high=200, size=(regions_num,))
    weights = np.random.uniform(low=0.5, high=200, size=(regions_num,))
    tract_lengths = np.random.uniform(low=0.5, high=200, size=(regions_num,))
    
class Simulator_A():
    def __init__(self, p_configurations_manager,  p_log_settings, p_interscalehub_addresses):
            
        self._configurations_manager = p_configurations_manager
        self.__logger = self._configurations_manager.load_log_configurations(
            name="Simulator_A",
            log_configurations= p_log_settings,
            target_directory=DefaultDirectories.SIMULATION_RESULTS)

        self.__params = Simulator_A_Parameters()
            
        # MPI rank
        self.__comm = MPI.COMM_WORLD
        self.__rank = self.__comm.Get_rank()
        self.__my_pid = os.getpid()
        self.__logger.info(f"size: {self.__comm.Get_size()}, my rank: {self.__rank}, "
                           f"host_name:{os.uname()}")
        self.__interscalehub_A_to_B_address ="endpoint_address:"+str(DATA_EXCHANGE_DIRECTION.NEST_TO_TVB.name)
        self.__interscalehub_B_to_A_address ="endpoint_address:"+str(DATA_EXCHANGE_DIRECTION.TVB_TO_NEST.name)
        
        self.__log_message("A Initialized")
        
    def __log_message(self, msg):
        "helper function to control the log emissions as per rank"
        if self.rank == 0:        
            self.__logger.info(msg)
        else:
            self.__logger.debug(msg)
            
    @property
    def rank(self):
        return self.__rank
    
    @property
    def pid(self):
        return self.__my_pid
    
    def configure(self):
        
        self.__comm = MPI.COMM_WORLD.Connect(self.__interscalehub_A_to_B_address)
        self.__logger.info('configuration A done!')
    
    def simulate(self):
        self.__logger.info('start the simulation A')
        
        #MPI workflow
        data = {'a': 2, 'b': 4}
        self.__comm.send(data, dest=self.__interscalehub_A_to_B_address)
        i_data = self.__comm.recv(source=self.__interscalehub_B_to_A_address)
        
        self.__logger.info('A received'+str(i_data))
        
        self.__comm.Disconnect()
        MPI.Close_port(self.__interscalehub_nest_to_tvb_address)
        
        print('Simulation A done!')
        self.__logger.info('exit')
        


