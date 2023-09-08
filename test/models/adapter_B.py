import os, sys, pickle, base64, ast, numpy as np, traceback
from dataclasses import dataclass
from mpi4py import MPI

from action_adapters_alphabrunel.resource_usage_monitor_adapter import ResourceMonitorAdapter

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

from mock_app_B import Simulator_B

class Adapter_B():
    def __init__(self, p_configurations_manager, p_log_settings,
                 p_interscalehub_addresses,
                 is_monitoring_enabled,
                 sci_params_xml_path_filename=None):
        self.log_settings = p_log_settings
        self.configurations_manager = p_configurations_manager
        self.logger = self.configurations_manager.load_log_configurations(
            name="Adapter_B",
            log_configurations=self.log_settings,
            target_directory=DefaultDirectories.SIMULATION_RESULTS)
        self.path_to_parameters_file = self.configurations_manager.get_directory(
            directory=DefaultDirectories.SIMULATION_RESULTS)
        
        self.my_pid = os.getpid()
        
        # Loading scientific parameters into an object
        self.sci_params = Xml2ClassParser(sci_params_xml_path_filename, self.logger)
        self.parameters = Parameters(self.path_to_parameters_file)
        #self.is_monitoring_enabled = is_monitoring_enabled
        #if self.is_monitoring_enabled:
        #    self.resource_usage_monitor = ResourceMonitorAdapter(self.configurations_manager,
        #                                                       self.log_settings,
        #                                                       self.my_pid,
        #                                                       "B")
        
        self.simulator = Simulator_B(self.configurations_manager, self.log_settings, p_interscalehub_addresses)

    @property
    def pid(self):
        return self.my_pid 
    
    def execute_init_command(self):        
        self.simulator.configure()
        self.logger.info("APM B INIT command is executed")
        return 10, [123, 789]

    def execute_start_command(self, global_minimum_step_size):
        #if self.is_monitoring_enabled:
        #    self.resource_usage_monitor.start_monitoring()
            
        self.logger.info('APM B START command')
        self.simulator.simulate()
        self.logger.info('APM B START command is executed')
         
    def execute_end_command(self):
        #if self.is_monitoring_enabled:
        #    self.resource_usage_monitor.stop_monitoring()
            
        self.logger.info('APM B END command is executed')
        

if __name__ == "__main__":
    try:
        # TODO better handling of arguments parsing
        if len(sys.argv) == 6:        
            # 1. parse arguments
            # unpickle configurations_manager object
            configurations_manager = pickle.loads(base64.b64decode(sys.argv[1]))
            # unpickle log_settings
            log_settings = pickle.loads(base64.b64decode(sys.argv[2]))
            # get science parameters XML file path
            p_sci_params_xml_path_filename = sys.argv[3]
            # flag indicating whether resource usage monitoring is enabled
            is_monitoring_enabled = pickle.loads(base64.b64decode(sys.argv[4]))
            # get interscalehub connection details
            p_interscalehub_address = pickle.loads(base64.b64decode(sys.argv[5]))
            #print("APM B ",p_interscalehub_address)

            # 2. security check of pickled objects
            # it raises an exception, if the integrity is compromised
            check_integrity(configurations_manager, ConfigurationsManager)
            check_integrity(log_settings, dict)
            check_integrity(p_interscalehub_address, list)
            check_integrity(is_monitoring_enabled, bool)

            # 3. everything is fine, configure simulator
            nest_adapter = Adapter_B(
                configurations_manager,
                log_settings,
                p_interscalehub_address,
                is_monitoring_enabled,
                sci_params_xml_path_filename=p_sci_params_xml_path_filename)

            # 4. execute 'INIT' command which is implicit with when laucnhed
            local_minimum_step_size, list_spike_detector = nest_adapter.execute_init_command()

            # 5. send the pid and the local minimum step size to Application Manager
            # as a response to 'INIT' as per protocol
            
            # NOTE Application Manager expects a string in the following format:
            # {'PID': <pid>, 'LOCAL_MINIMUM_STEP_SIZE': <step size>}

            pid_and_local_minimum_step_size = \
                {SIMULATOR.PID.name: nest_adapter.pid,
                SIMULATOR.LOCAL_MINIMUM_STEP_SIZE.name: local_minimum_step_size,
                SIMULATOR.SPIKE_DETECTORS.name: list_spike_detector,
                }
        
            # send the response
            # NOTE Application Manager will read the stdout stream via PIPE
            print(f'{pid_and_local_minimum_step_size}')            
            
            #TODO
            #- check MPI if connections are not stablized

            # 6. fetch next command from Application Manager
            user_action_command = input()

            # NOTE Application Manager sends the control commands with parameters in
            # the following specific format as a string via stdio:
            # {'STEERING_COMMAND': {'<Enum SteeringCommands>': <Enum value>}, 'PARAMETERS': <value>}
            
            # For example:
            # {'STEERING_COMMAND': {'SteeringCommands.START': 2}, 'PARAMETERS': 1.2}        

            # convert the received string to dictionary
            control_command = ast.literal_eval(user_action_command.strip())
            # get steering command
            steering_command_dictionary = control_command.get(COMMANDS.STEERING_COMMAND.name)
            current_steering_command = next(iter(steering_command_dictionary.values()))
            
            #print("APM B PARAMETERS", control_command)
            # 7. execute if steering command is 'START'
            if current_steering_command == SteeringCommands.START:
                # fetch global minimum step size
                #print("APM B PARAMETERS", control_command)
                global_minimum_step_size = [10]#control_command.get(COMMANDS.PARAMETERS.name)
                # execute the command
                nest_adapter.execute_start_command(global_minimum_step_size[0])
                nest_adapter.execute_end_command()
                # exit with success code
                sys.exit(0)
            else:
                print(f'unknown command: {current_steering_command}', file=sys.stderr)
                sys.exit(1)
        else:
            print(f'missing argument[s]; required: 6, received: {len(sys.argv)}')
            print(f'Argument list received: {str(sys.argv)}')
            sys.exit(1)
    except Exception as err:
        ex_type, ex_value, ex_traceback = sys.exc_info()

        # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)

        # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

        print("Exception type : %s " % ex_type.__name__)
        print("Exception message : %s" %ex_value)
        print("Stack trace : %s" %stack_trace)
        
        print("General Error " + str(err))
        sys.exit(1)