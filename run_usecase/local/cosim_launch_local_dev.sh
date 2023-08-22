killall -9 python3
killall -9 mpirun

export CO_SIM_ROOT_PATH="/home/vagrant/multiscale-cosim"
export CO_SIM_MODULES_ROOT_PATH="${CO_SIM_ROOT_PATH}/myremotefork/TVB-NEST-usecase1"
export CO_SIM_USE_CASE_ROOT_PATH="${CO_SIM_MODULES_ROOT_PATH}"
export PYTHONPATH=${CO_SIM_USE_CASE_ROOT_PATH}:/home/vagrant/multiscale-cosim/site-packages:/home/vagrant/multiscale-cosim/nest/lib/python3.8/site-packages
#/home/vagrant/multiscale-cosim/site-packages:/home/vagrant/multiscale-cosim/TVB-NEST-usecase1

export PATH=/home/vagrant/multiscale-cosim/nest/bin:${PATH}

python3 ${CO_SIM_MODULES_ROOT_PATH}/main.py --global-settings ${CO_SIM_MODULES_ROOT_PATH}/EBRAINS_WorkflowConfigurations/general/global_settings.xml --action-plan ${CO_SIM_USE_CASE_ROOT_PATH}/userland/configs/local/plans/cosim_alpha_brunel_local.xml
