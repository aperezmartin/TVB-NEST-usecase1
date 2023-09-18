import os, sys, pickle, base64, ast, numpy as np, time
from dataclasses import dataclass
from mpi4py import MPI

from EBRAINS_RichEndpoint.application_companion.common_enums import Response
from EBRAINS_InterscaleHUB.common.interscalehub_enums import DATA_EXCHANGE_DIRECTION
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
    
    def configure(self):
        
        try:
            #self.logger.info(f"APM B {self.interscalehub_addresses}")
            #self.logger.info(f'APM B! send to:{self.interscalehub_A_to_B_address} receive from:{self.interscalehub_B_to_A_address}')
            
            self.comm_sender = MPI.COMM_WORLD.Connect(self.interscalehub_A_to_B_address)
            self.comm_receiver = MPI.COMM_WORLD.Connect(self.interscalehub_B_to_A_address)
            
            self.logger.info('configuration B done!')
        except Exception as err:
            self.logger.error(f'APM Error Mock B: {err}')

    def simulate(self):
        self.logger.info('APM B start simulation')
        self._tvb_mpi_rcv()
        self._tvb_mpi_snd()


        self.logger.info('exit')
        return Response.OK
