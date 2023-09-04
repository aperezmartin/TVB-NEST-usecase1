#!/usr/bin/env bash

#"$1" is the name of the my local folder where I have my repo cloned
if [ -z "$1" ]
  then
    echo "No argument supplied"
    echo "Please provide your local relative path, e.g 'myremotefork' like /home/vagrant/multiscale-cosim/myremotefork"
    exit 1
fi

killall -9 python3
killall -9 mpirun

export CO_SIM_ROOT_PATH="/home/vagrant/multiscale-cosim"
export CO_SIM_MODULES_ROOT_PATH="${CO_SIM_ROOT_PATH}/"$1"/TVB-NEST-usecase1"
export CO_SIM_USE_CASE_ROOT_PATH="${CO_SIM_MODULES_ROOT_PATH}"
export PYTHONPATH=${CO_SIM_USE_CASE_ROOT_PATH}:/home/vagrant/multiscale-cosim/site-packages:/home/vagrant/multiscale-cosim/nest/lib/python3.8/site-packages
#/home/vagrant/multiscale-cosim/site-packages:/home/vagrant/multiscale-cosim/TVB-NEST-usecase1

export PATH=/home/vagrant/multiscale-cosim/nest/bin:${PATH}

python3 ${CO_SIM_MODULES_ROOT_PATH}/main.py --global-settings ${CO_SIM_MODULES_ROOT_PATH}/$2 --action-plan ${CO_SIM_USE_CASE_ROOT_PATH}/$3
