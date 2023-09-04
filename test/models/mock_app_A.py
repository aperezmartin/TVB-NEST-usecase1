import os, sys, pickle, base64, ast, numpy as np
from dataclasses import dataclass
from mpi4py import MPI

from EBRAINS_InterscaleHUB.Interscale_hub.interscalehub_enums import DATA_EXCHANGE_DIRECTION
from EBRAINS_RichEndpoint.application_companion.common_enums import INTEGRATED_INTERSCALEHUB_APPLICATION as INTERSCALE_HUB
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories

from mock_app_Base import Application_Base

@dataclass
class Simulator_A_Parameters():
    regions_num = 68
    regions = np.random.uniform(low=10, high=200, size=(regions_num,))
    weights = np.random.uniform(low=0.5, high=200, size=(regions_num,))
    tract_lengths = np.random.uniform(low=0.5, high=200, size=(regions_num,))
    
class Simulator_A(Application_Base):
    def __init__(self, p_configurations_manager,  p_log_settings, p_interscalehub_addresses):
        super().__init__("Simulator A", p_configurations_manager,  p_log_settings, p_interscalehub_addresses)

        self._init_port_names( port1=DATA_EXCHANGE_DIRECTION.NEST_TO_TVB, 
                               port2=DATA_EXCHANGE_DIRECTION.TVB_TO_NEST)

        self.params = Simulator_A_Parameters()
        #self.log_message("A Initialized, rank: "+str(self.__rank))
        
    def log_message(self, msg):
        "helper function to control the log emissions as per rank"
        if self.rank == 0:        
            self.logger.info(msg)
        else:
            self.logger.debug(msg)

    def configure(self):
        
        self._init_mpi()
        self.logger.info('configuration A done!')

    def simulate(self):
        self.logger.info('APM A start simulation')
        
        origin_value=2.8
        self._send_mpi(origin_value)
        self.logger.info('APM A send'+str(origin_value))
        
        value = self._receive_mpi()
        self.logger.info('APM A received'+str(value))
        
        self._end_mpi(is_mode_sending=False)

        print("APM Simulator A, send->",origin_value," receive ->",value)


    """
    def configure(self):
        self.__comm = MPI.COMM_WORLD.Connect(self.__interscalehub_A_to_B_address)
    
    def simulate(self):
        self.__logger.info('start the simulation A')
        
        
        #MPI workflow
        data = {'a': 2, 'b': 4}
        self.__comm.send(data, dest=self.__interscalehub_A_to_B_address)
        i_data = self.__comm.recv(source=self.__interscalehub_B_to_A_address)
        
        self.__logger.info('A received'+str(i_data))
        
        self.__comm.Disconnect()
        MPI.Close_port(self.__interscalehub_nest_to_tvb_address)
    """

        
        


