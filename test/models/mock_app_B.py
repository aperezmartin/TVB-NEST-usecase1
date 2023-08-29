import os, sys, pickle, base64, ast, numpy as np
from dataclasses import dataclass
from mpi4py import MPI

from EBRAINS_InterscaleHUB.Interscale_hub.interscalehub_enums import DATA_EXCHANGE_DIRECTION
from EBRAINS_RichEndpoint.application_companion.common_enums import INTEGRATED_INTERSCALEHUB_APPLICATION as INTERSCALE_HUB
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories

from mock_app_Base import Application_Base

@dataclass
class Simulator_B_Parameters():
    list_spikes= np.random.choice([0, 1], size=(10,), p=[1./3, 2./3])

class Simulator_B(Application_Base):
    def __init__(self, p_configurations_manager,  p_log_settings, p_interscalehub_addresses):
        super().__init__("Simulator B", p_configurations_manager,  p_log_settings, p_interscalehub_addresses)

        self._init_port_names( port1=DATA_EXCHANGE_DIRECTION.TVB_TO_NEST, 
                               port2=DATA_EXCHANGE_DIRECTION.NEST_TO_TVB)

        self.params = Simulator_B_Parameters()
        self.log_message("A Initialized, rank: "+str(self.__rank))
        
    def log_message(self, msg):
        "helper function to control the log emissions as per rank"
        if self.rank == 0:        
            self.logger.info(msg)
        else:
            self.logger.debug(msg)
            
    @property
    def rank(self):
        return self.__rank
    
    @property
    def pid(self):
        return self.__my_pid
    
    def configure(self):
        
        self._init_mpi()
        self.logger.info('configuration B done!')
    
        print('Simulation B done!')
        self.logger.info('exit')

    def simulate(self):
        
        value_rcv = self._receive_mpi()
        self.logger.info('APM B received'+str(value_rcv))
        
        value_new = value_rcv * 8
        self._send_mpi(value_new)
        self.logger.info('APM B send'+str(value_new))
        
        self._end_mpi(is_mode_sending=True)
        
        print("Simulator B, receive->",value_rcv," send ->",value_new)
        
        """
        #MPI workflow
        data = {'a': 2, 'b': 4}
        i_data = self.__comm.recv(source=self.__interscalehub_A_to_B_address)
        self.__logger.info('B received'+str(i_data))
        
        i_data = i_data * 2
        self.__comm.send(i_data, dest=self.__interscalehub_B_to_A_address)
        
        self.__comm.Disconnect()
        MPI.Close_port(self.__interscalehub_nest_to_tvb_address)
        """
        

        print('Simulation B done!')
        self.__logger.info('exit')
        