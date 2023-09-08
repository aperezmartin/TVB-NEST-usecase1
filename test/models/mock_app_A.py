import os, sys, pickle, base64, ast, numpy as np
from dataclasses import dataclass
from mpi4py import MPI

from EBRAINS_RichEndpoint.application_companion.common_enums import Response
from EBRAINS_InterscaleHUB.common.interscalehub_enums import DATA_EXCHANGE_DIRECTION
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

        #NEST_TO_TVB (RECEIVER), TVB_TO_NEST (SENDER)
        self._init_port_names( port1=DATA_EXCHANGE_DIRECTION.NEST_TO_TVB, 
                               port2=DATA_EXCHANGE_DIRECTION.TVB_TO_NEST)

        self.params = Simulator_A_Parameters()
        
    def configure(self):
        
        #self._init_mpi()
        try:
            #self.logger.info(f"APM A {self.interscalehub_addresses}")
            #self.logger.info(f'APM A! send to:{self.interscalehub_A_to_B_address} receive from:{self.interscalehub_B_to_A_address}')
            
            self.comm_sender = MPI.COMM_WORLD.Connect(self.interscalehub_B_to_A_address)
            self.comm_receiver = MPI.COMM_WORLD.Connect(self.interscalehub_A_to_B_address)
            
            self.logger.info('configuration A done!')
        except Exception as err:
            self.logger.error(f'APM Error Mock A: {err}')

    def simulate(self):
        self.logger.info('APM A start simulation')

        self._nest_mpi_snd()
        self._nest_mpi_rcv()

        self.logger.info('exit')
        return Response.OK

        


