#  Copyright 2020 Forschungszentrum Jülich GmbH and Aix-Marseille Université
# "Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements; and to You under the Apache License, Version 2.0. "

import numpy as np
import pathlib
import re
import os
import time


def wait_transformation_modules(nest, path, spike_generator, spike_detector, logger):
    """
    To create the files for transfer information to the transformation modules
    and to wait the file which contains the port description
    :param nest:
    :param path:
    :param spike_generator:
    :param spike_detector:
    :param logger:
    :return:
    """
    if nest.Rank() == 0:
        path_spike_generator = path + '/nest/spike_generator.txt'
        list_spike_generator = []
        for node in spike_generator:
            list_spike_generator.append(node.tolist())
        np.savetxt(path_spike_generator, np.array(list_spike_generator, dtype=int), fmt='%i')
        pathlib.Path(path_spike_generator + '.unlock').touch()
        path_spike_detector = path + '/nest/spike_detector.txt'
        list_spike_detector = []
        for node in spike_detector:
            list_spike_detector.append(node.tolist())
        np.savetxt(path_spike_detector, np.array(list_spike_detector, dtype=int), fmt='%i')
        pathlib.Path(path_spike_detector + '.unlock').touch()

        logger.info('check if the port are file for the port are ready to use')
        for ids_spike_generator in list_spike_generator:
            for id_spike_generator in ids_spike_generator:
                while not os.path.exists(
                        path + '/transformation/spike_generator/' + str(id_spike_generator) + '.txt.unlock'):
                    time.sleep(1)
                os.remove(path + '/transformation/spike_generator/' + str(id_spike_generator) + '.txt.unlock')
        for id_spike_detector in list_spike_detector:
            while not os.path.exists(
                    path + '/transformation/spike_detector/' + str(id_spike_detector[0]) + '.txt.unlock'):
                time.sleep(1)
            os.remove(path + '/transformation/spike_detector/' + str(id_spike_detector[0]) + '.txt.unlock')


def get_data(logger, path, pattern="brunel-py-ex-*"):
    """
    read dat file with spikes inside
    :param path: path of files
    :param pattern: pattern to identify the files (one generated by MPI process)
    :return: spikes time
    """

    def _blockread(fname, skiprows=0, skiphead=3):
        a = []
        with open(fname, 'r') as f:
            while True:
                line = None
                for i in range(skiprows + skiphead):
                    line = f.readline()
                    if not line:
                        break
                if not line:
                    break
                for i in range(int(1e6)):
                    line = f.readline()
                    if not line:
                        break
                    a.append(line.split())
                yield a
        if a == []:
            try:
                raise Exception('stop file')
            except Exception:
                logger.exception('data is empty')

    re_pattern = re.compile(pattern)
    data = []
    for file in os.listdir(path):
        if re.match(re_pattern, file) is not None:
            for i in _blockread(path + file):
                for id, time in i:
                    data.append([int(id), float(time)])
    return np.array(data)
