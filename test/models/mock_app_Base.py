import os, sys, pickle, base64, ast, numpy as np
from dataclasses import dataclass
from mpi4py import MPI

from action_adapters_alphabrunel.resource_usage_monitor_adapter import ResourceMonitorAdapter

from EBRAINS_RichEndpoint.application_companion.common_enums import Response
from action_adapters_alphabrunel.nest_simulator.utils_function import get_data
from action_adapters_alphabrunel.parameters import Parameters
from EBRAINS_RichEndpoint.application_companion.common_enums import SteeringCommands, COMMANDS
from EBRAINS_RichEndpoint.application_companion.common_enums import INTEGRATED_SIMULATOR_APPLICATION as SIMULATOR
from EBRAINS_RichEndpoint.application_companion.common_enums import INTEGRATED_INTERSCALEHUB_APPLICATION as INTERSCALE_HUB
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.default_directories_enum import DefaultDirectories
from EBRAINS_ConfigManager.global_configurations_manager.xml_parsers.configurations_manager import ConfigurationsManager
from EBRAINS_ConfigManager.workflow_configurations_manager.xml_parsers.xml2class_parser import Xml2ClassParser
from EBRAINS_InterscaleHUB.common.interscalehub_enums import DATA_EXCHANGE_DIRECTION
from EBRAINS_Launcher.common.utils.security_utils import check_integrity


# Define MPI message tags
#tags = enum('READY', 'DONE', 'EXIT', 'START')

class Application_Base():
    def __init__(self, p_simulator_name, p_configurations_manager,  p_log_settings, p_interscalehub_addresses):
            
        self.simulator_name = p_simulator_name
        self.comm_sender = None
        self.comm_receiver = None
        
        self.interscalehub_A_to_B_address = None
        self.interscalehub_B_to_A_address = None
        
        self.configurations_manager = p_configurations_manager
        self.logger = self.configurations_manager.load_log_configurations(
            name=self.simulator_name,
            log_configurations= p_log_settings,
            target_directory=DefaultDirectories.SIMULATION_RESULTS)
        
        # MPI rank
        #self.comm = MPI.COMM_WORLD
        #self.rank = self.comm.Get_rank()
        self.my_pid = os.getpid()
        #self.logger.info(f"size: {self.comm.Get_size()}, my rank: {self.rank}, "
        #                   f"host_name:{os.uname()}")
        
        self.interscalehub_addresses = p_interscalehub_addresses
        
    #@property
    #def rank(self):
    #    return self.__rank
    
    @property
    def pid(self):
        return self.my_pid
    
    def _init_port_names(self, port1:DATA_EXCHANGE_DIRECTION, port2:DATA_EXCHANGE_DIRECTION):
        
        for mpi_address in self.interscalehub_addresses:
            if mpi_address.get(DATA_EXCHANGE_DIRECTION.__name__) == port1.name:
                self.interscalehub_A_to_B_address = mpi_address.get(INTERSCALE_HUB.MPI_CONNECTION_INFO.name)
                #print("APM _init_port_names ",self.__class__.__name__,"interscalehub_A_to_B_address",self.interscalehub_A_to_B_address)
                
            elif mpi_address[str(DATA_EXCHANGE_DIRECTION.__name__)] == port2.name:
                self.interscalehub_B_to_A_address = mpi_address.get(INTERSCALE_HUB.MPI_CONNECTION_INFO.name)
                #print("APM _init_port_names ",self.__class__.__name__,"interscalehub_B_to_A_address",self.interscalehub_B_to_A_address)
            #else:
                #print("APM Error _init_port_names ",mpi_address[str(DATA_EXCHANGE_DIRECTION.__name__)], port1.name, INTERSCALE_HUB.MPI_CONNECTION_INFO.name)

    def _init_mpi(self):
        try:
            if self.interscalehub_A_to_B_address and self.interscalehub_B_to_A_address:
                """sets up MPI communicators"""
                # create receiver communicator
                self.comm_receiver = MPI.COMM_WORLD.Connect(self.interscalehub_A_to_B_address)
                self.logger.debug("receiver is connected")
                self.logger.debug(f"receiver communicators: {self.comm_receiver} {self.interscalehub_A_to_B_address}")
                
                # create sender communicator
                self.comm_sender = MPI.COMM_WORLD.Connect(self.interscalehub_B_to_A_address)
                self.logger.debug("sender is connected")
                self.logger.debug(f"sender communicators: {self.comm_sender}  {self.interscalehub_B_to_A_address}")
            else:
                self.logger.debug("APM interscalehub_A_to_B_address error")
                
        except Exception as err:
            self.logger.error("The error in init_mpi,: " + str(err))
    
        
    def _send_mpi(self, data:float):
        #print("APM "+ str(self.__class__.__name__), "_send_mpi")
        self.logger.info("APM start send "+ str(self.__class__.__name__))
        status_ = MPI.Status()
        
        # wait until the transformer accept the connections
        accept = False 
        while not accept:
            req = self.comm_sender.irecv(source=0, tag=0)
            accept = req.wait(status_)
            self.logger.info("APM send accept")
        
        source = status_.Get_source()  # the id of the excepted source
        self.logger.info("APM get source"+str(vars(source)))

        self.comm_sender.Send([data, MPI.DOUBLE], dest=source, tag=0)
        self.logger.info("end send")
        
    def _receive_mpi(self): 
        #TODO checkwhile

        self.logger.info("start receive")
        status_ = MPI.Status()
        # send to the transformer : I want the next part
        req = self.comm_receiver.isend(True, dest=0, tag=0)
        req.wait()
        obj_rcv = 0.0 #np.empty(2, dtype='d')
        self.comm_receiver.Recv([obj_rcv, 2, MPI.DOUBLE], source=0, tag=MPI.ANY_TAG, status=status_)
        # get the size of the rate
        #size = np.empty(1, dtype='i')
        #self.comm_receiver.Recv([size, MPI.INT], source=0, tag=0)
        # get the rate
        #rates = np.empty(size, dtype='d')
        #self.comm_receiver.Recv([rates, size, MPI.DOUBLE], source=0, tag=MPI.ANY_TAG, status=status_)
        self.logger.info("end receive " + str(obj_rcv))
        # print the summary of the data
        if status_.Get_tag() == 0:
            return obj_rcv
        else:
            return None
        
    def _end_mpi(self, is_mode_sending):

        # different ending of the transformer
        if is_mode_sending:
            self.logger.info(str(self.simulator_name)+" close connection send "+ self.interscalehub_B_to_A_address)
            self._close_connection(self.comm_sender, self.interscalehub_B_to_A_address)
        else:
            self.logger.info(str(self.simulator_name)+" close connection receive " + self.interscalehub_A_to_B_address)
            self._close_connection(self.comm_receiver, self.interscalehub_A_to_B_address)
        return Response.OK
    
    def _close_connection(self, comm, address):
        # closing the connection at this end
        self.logger.info(str(self.simulator_name)+"disconnect communication")
        comm.Disconnect()
        self.logger.info(str(self.simulator_name)+" close " + address)
        MPI.Close_port(address)
        self.logger.info(str(self.simulator_name)+" close connection " + address)