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
        
        self.my_pid = os.getpid()
        self.interscalehub_addresses = p_interscalehub_addresses
        
    def _init_port_names(self, port1:DATA_EXCHANGE_DIRECTION, port2:DATA_EXCHANGE_DIRECTION):

        for mpi_address in self.interscalehub_addresses:
            if mpi_address.get(DATA_EXCHANGE_DIRECTION.__name__) == port1.name:
                self.interscalehub_A_to_B_address = mpi_address.get(INTERSCALE_HUB.MPI_CONNECTION_INFO.name)
                
            elif mpi_address[str(DATA_EXCHANGE_DIRECTION.__name__)] == port2.name:
                self.interscalehub_B_to_A_address = mpi_address.get(INTERSCALE_HUB.MPI_CONNECTION_INFO.name)
    
    def _nest_mpi_snd(self):
        #Simulator A
        self.min_delay=1
        
        #super().simulate()
        # NOTE: the mock NEST OUTPUT simulation
        starting = 0.0 # the begging of each time of synchronization
        status_ = MPI.Status() # status of the different message
        check = np.empty(1,dtype='b') # needed?
        while True:
            self.logger.info("NEST_OUTPUT: wait for ready signal")
            # NOTE: seems like a handshake..needed?
            self.comm_sender.Send([np.array([True],dtype='b'), 1, MPI.CXX_BOOL], dest=0, tag=0)
            self.comm_sender.Recv([check, 1, MPI.CXX_BOOL], source=MPI.ANY_SOURCE, tag=0,status=status_)
            
            self.logger.info("NEST_OUTPUT: simulate next step...")
            # create random data
            size= np.random.randint(0,1000)
            times = starting+np.random.rand(size)*(self.min_delay-0.2)
            times = np.around(np.sort(np.array(times)),decimals=1)
            id_neurons = np.random.randint(0,10,size)
            id_detector = np.random.randint(0,10,size)
            data = np.ascontiguousarray(np.swapaxes([id_detector,id_neurons,times],0,1),dtype='d')
            
            # send data one by one like spike generator
            self.comm_sender.Send([np.array([size*3],dtype='i'),1, MPI.INT], dest=status_.Get_source(), tag=0)
            self.comm_sender.Send([data,size*3, MPI.DOUBLE], dest=status_.Get_source(), tag=0)
            # results and go to the next run
            self.logger.info("NEST_OUTPUT: Rank {} sent data of size {}".format(self.comm_sender.Get_rank(),size))
            
            # ending the simulation step
            self.comm_sender.Send([np.array([True],dtype='b'), 1, MPI.CXX_BOOL], dest=0, tag=1)
            starting+=self.min_delay
            if starting > 10000:
                break
        # end of nest out
        self.comm_sender.Send([np.array([True], dtype='b'), 1, MPI.CXX_BOOL], dest=0, tag=2)
        self.logger.info("NEST_OUTPUT: end of simulation" )
    
    def _nest_mpi_rcv(self):
        #Simulator A
        status_ = MPI.Status() # status of the different message
        #NOTE: hardcoded...
        ids=np.arange(0,10,1) # random id of spike detector
        while(True):
            # Send start simulation
            self.logger.info("NEST_INPUT: send ready to receive next step")
            self.comm_receiver.Send([np.array([True], dtype='b'), MPI.CXX_BOOL], dest=1, tag=0)
            self.logger.info("NEST_INPUT: send spike detector info")
            self.comm_receiver.Send([np.array(10,dtype='i'), MPI.INT], dest=1, tag=0)
            self.comm_receiver.Send([np.array(ids,dtype='i'), MPI.INT], dest=1, tag=0)
            
            # receive the number of spikes
            size=np.empty(11,dtype='i')
            self.comm_receiver.Recv([size,11, MPI.INT], source=1, tag=ids[0],status=status_)
            self.logger.info("NEST_INPUT ({}):receive size : {}".format(ids[0],size))
            
            # receive the spikes for updating the spike detector
            data = np.empty(size[0], dtype='d')
            self.comm_receiver.Recv([data,size[0], MPI.DOUBLE],source=1,tag=ids[0],status=status_)
            self.logger.info ("NEST_INPUT ({}):receive size : {}".format(ids[0],np.sum(data)))
            
            # send end of sim step
            # NOTE: why?
            self.logger.info("NEST_INPUT: send end of simulation step")
            self.comm_receiver.Send([np.array([True], dtype='b'), MPI.CXX_BOOL], dest=1, tag=1)

            if np.any(data > 10000):
                break

        # closing the connection at this end
        self.logger.info("NEST_INPUT: end of simulation")
        self.comm_receiver.Send([np.array([True], dtype='b'), MPI.CXX_BOOL], dest=1, tag=2)
        
    
    def _tvb_mpi_snd(self):
        #Simulator B

        self.min_delay=1

        self.logger.info("TVB_OUTPUT: start of simulation")
        starting = 0.0 # the beginning of each time of synchronization
        status_ = MPI.Status() # status of the different message
        while True:
            # wait for InterscaleHub ready signal
            accept = False
            self.logger.info("TVB_OUTPUT: wait for ready signal")
            while not accept:
                req = self.comm_sender.irecv(source=0,tag=0)
                accept = req.wait(status_)
            self.logger.info("TVB_OUTPUT: simulate next step")
            # TODO: the irecv above is from source 0, so 'source = status_.Get_source()' will be 0.
            # TODO: If the goal was to send from multiple TVB ranks to multiple sources, this needs some work.
            # TODO: essentially this would be an M:N coupling then
            source = status_.Get_source() # the id of the excepted source
            # create random data
            size= int(self.min_delay/0.1 )
            rate = np.random.rand(size)*400
            data = np.ascontiguousarray(rate,dtype='d') # format the rate for sending
            shape = np.array(data.shape[0],dtype='i') # size of data
            times = np.array([starting,starting+self.min_delay],dtype='d') # time of stating and ending step
            
            self.logger.info("TVB_OUTPUT: sending timestep {}".format(times))
            self.comm_sender.Send([times,MPI.DOUBLE],dest=source,tag=0)
            
            self.logger.info("TVB_OUTPUT: sending shape : {}".format(shape))
            self.comm_sender.Send([shape,MPI.INT],dest=source,tag=0)
            
            self.logger.info("TVB_OUTPUT: sending data : {}".format(np.sum(np.sum(data))))
            self.comm_sender.Send([data, MPI.DOUBLE], dest=source, tag=0)
            
            starting+=self.min_delay
            if starting > 10000:
                break
        
        accept = False
        self.logger.info("TVB_OUTPUT: ending...sending last timestep")
        while not accept:
            req = self.comm_sender.irecv(source=0,tag=0)
            accept = req.wait(status_)

        self.logger.info("TVB_OUTPUT: sending timestep : {}".format(times))
        self.comm_sender.Send([times, MPI.DOUBLE], dest=0, tag=1)
        
        self.logger.info("TVB_OUTPUT: end of simulation" )
    
    def _tvb_mpi_rcv(self):
        #Simulator B
        self.logger.info("TVB_INPUT: start receiving...")
        status_ = MPI.Status() # status of the different message
        while(True):
            self.logger.info("TVB_INPUT: ready to receive next step")
            # send to the translator, I want the next part
            req = self.comm_receiver.isend(True, dest=1, tag=0)
            req.wait()
            
            times=np.empty(2,dtype='d')
            self.comm_receiver.Recv([times, MPI.FLOAT], source=1, tag=0)
            
            size=np.empty(1,dtype='i')
            self.comm_receiver.Recv([size, MPI.INT], source=1, tag=0)
            
            
            rates = np.empty(size, dtype='d')
            self.comm_receiver.Recv([rates,size, MPI.DOUBLE],source=1,tag=MPI.ANY_TAG,status=status_)
            
            # summary of the data
            if status_.Get_tag() == 0:
                self.logger.info("TVB_INPUT:{} received timestep {} and rates {}"
                                   .format(self.comm_receiver.Get_rank(),times,np.sum(rates)))
            else:
                break
            if times[1] >9900:
                break
        # end of tvb in
        req = self.comm_receiver.isend(True, dest=1, tag=1)
        req.wait()
        self.logger.info("TVB_INPUT: received end signal")

    def _end_mpi(self, is_mode_sending):

        # different ending of the transformer
        if is_mode_sending:
            self.logger.info(f"{self.simulator_name} close connection send {self.interscalehub_B_to_A_address}")
            self._close_connection(self.comm_sender, self.interscalehub_B_to_A_address)
        else:
            self.logger.info(f"{self.simulator_name} close connection receive {self.interscalehub_A_to_B_address}")
            self._close_connection(self.comm_receiver, self.interscalehub_A_to_B_address)
        return Response.OK
    
    def _close_connection(self, comm, address):
        # closing the connection at this end
        self.logger.info(f"{self.simulator_name} disconnected communication")
        comm.Disconnect()
        self.logger.info(f"{self.simulator_name} closed {address} ")
        MPI.Close_port(address)
        self.logger.info(f"{self.simulator_name} closed connection {address} ")