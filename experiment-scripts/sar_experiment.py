from __future__ import division
import os
import numpy as np
import h5py
import anritsu_vna
import rail_ethernet_api
import time
from constants import *
from parameters import *

if __name__ == "__main__":
    '''
    connect to the vna and configure it
    '''
    vector_network_analyzer = anritsu_vna.VnaClient()
    vector_network_analyzer.connect()
    vector_network_analyzer.send_ifbw(ifbw)
    vector_network_analyzer.send_number_points(nfre)
    vector_network_analyzer.send_freq_start(freq_start = fi)
    vector_network_analyzer.send_freq_stop(freq_stop = ff)
    vector_network_analyzer.send_power(ptx)
    vector_network_analyzer.send_select_instrument()
    vector_network_analyzer.send_cfg()
    time.sleep(10) #wait for some time til it complets to configure

    '''
    connect to the rail, send to the start, configure it, close connection
    '''

    rail = rail_ethernet_api.railClient()
    rail.connect()
    rail.send_to_start()
    rail.close()

    time_begin = time.time() #store starting time of the experiment

    DATE   = (time.strftime("%d.%m.%y", time.localtime(time_begin)))
    TIME   = (time.strftime("%H.%M.%S", time.localtime(time_begin)))

    '''
    create storing folder, with the date and time
    '''
    if not os.path.exists(RAW_DATA_SAVING_ROUTE + FOLDER_NAME %(DATE, TIME)):
        os.makedirs(RAW_DATA_SAVING_ROUTE + FOLDER_NAME %(DATE, TIME))

    data_take = 1 #this variable will store number of takes

    while True:
        time_take = time.time()

        if (time_take - time_begin) >= timespan:
            break

        f = h5py.File(RAW_DATA_SAVING_ROUTE + FOLDER_NAME %(DATE, TIME) + FILE_NAME %(data_take), 'w')
        dset = f.create_dataset("sar_dataset", (npos, nfre), dtype = np.complex64)
        dset.attrs['xi'] = xi / METERS_TO_STEPS_FACTOR
        dset.attrs['xf'] = xf / METERS_TO_STEPS_FACTOR
        dset.attrs['dx'] = dx / METERS_TO_STEPS_FACTOR
        dset.attrs['npos'] = npos
        dset.attrs['fi'] = fi * 1E9
        dset.attrs['ff'] = ff * 1E9
        dset.attrs['nfre'] = nfre
        dset.attrs['ptx'] = ptx
        dset.attrs['ifbw'] = ifbw
        dset.attrs['date'] = time.strftime(("%d.%m.%y"), time.localtime(time_take))
        dset.attrs['time'] = time.strftime(("%H.%M.%S"), time.localtime(time_take))

        if xi != 0:
            rail.connect()
            rail.send_move(xi, 'L')
            rail.close()

        for j in range(0, npos):
            if j == 0:
                dset[j,:] = vector_network_analyzer.send_sweep()
                continue
            rail.connect()
            rail.send_move(dx, 'L')
            rail.close()
            time.sleep(0.5)
            dset[j,:] = vector_network_analyzer.send_sweep()

        rail.connect()
        rail.send_to_start()
        rail.close()
        f.close()
        time.sleep(2)
        data_take += 1

    vector_network_analyzer.close()
