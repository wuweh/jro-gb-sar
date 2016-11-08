from __future__ import division
import fnmatch
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates
from datetime import datetime
from scipy.fftpack import fft, ifft
from scipy import interpolate
from scipy import signal
import time
import h5py
import numpy.ma as ma
from datetime import datetime
import calendar

RUTA_DATOS_PROCESADOS = "/home/andre/sar_processed_data/Imaging/"
FOLDER_DATOS_PROCESADOS = "datos_procesados_%s"
FECHA_HORA = "10.10.16_12.21.17"

RUTA = RUTA_DATOS_PROCESADOS + FOLDER_DATOS_PROCESADOS %FECHA_HORA + '/'

RUTA_DESPLAZAMIENTOS = "/home/andre/sar_processed_data/Sliding/"
NOMBRE_DESPLAZAMIENTOS = "Desplazamientos_%s/"

folders = []
c0  =  299792458.0
time_format = "%H.%M.%S"
date_format = "%d.%m.%y"

if not os.path.exists(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA):
	os.makedirs(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA)

for file in os.listdir(RUTA):
	if fnmatch.fnmatch(file, '*.hdf5'):
		folders.append(file)

std_values = np.zeros([len(folders) - 1], dtype = float)
mean_values = np.zeros([len(folders) - 1], dtype = float)
magnitude_mean_values = np.zeros([len(folders) - 1], dtype = float)
mean_sum_values = np.zeros([len(folders) - 1], dtype = float)
date_values = []
vicinity_length_x = 1.0
vicinity_length_y = 1.0

for x in range(1, len(folders)):
	for file in folders:
		datos = '%d.hdf5' %x
		if fnmatch.fnmatch(file, '*' + 'toma_' + datos):
			datos = file
			break

	f = h5py.File(RUTA + datos, 'r')
	dset = f["Complex_image"]
	dx = dset.attrs["dx"]
	dy = dset.attrs["dy"]
	date = dset.attrs["date"]
	t = dset.attrs["time"]
	Imagen_master = dset[...]
	f.close()

	if x == 1:
		x_max = int(np.where(np.absolute(Imagen_master) == np.amax(np.absolute(Imagen_master)))[0])
		y_max = int(np.where(np.absolute(Imagen_master) == np.amax(np.absolute(Imagen_master)))[1])

	interest_region_master = np.zeros([int((2 * vicinity_length_x) / dx), int((2 * vicinity_length_y) / dy)], dtype = complex)

	interest_region_master = np.copy(Imagen_master[np.absolute(x_max - interest_region_master.shape[0]): x_max + interest_region_master.shape[0] - 1,
												  np.absolute(y_max - interest_region_master.shape[1]): y_max + interest_region_master.shape[1] - 1])
	for file in folders:
		datos = '%d.hdf5' %(x + 1)
		if fnmatch.fnmatch(file, '*' + 'toma_' + datos):
			datos = file
			break

	f = h5py.File(RUTA + datos, 'r')
	dset = f["Complex_image"]
	dx = dset.attrs["dx"]
	dy = dset.attrs["dy"]
	Imagen_slave = dset[...]
	f.close()

	interest_region_slave = np.zeros([int((2 * vicinity_length_x) / dx), int((2 * vicinity_length_y) / dy)], dtype = complex)

	interest_region_slave = np.copy(Imagen_slave[np.absolute(x_max - interest_region_slave.shape[0]): x_max + interest_region_slave.shape[0] - 1,
												 np.absolute(y_max - interest_region_slave.shape[1]): y_max + interest_region_slave.shape[1] - 1])

	#complex_correlation = (interest_region_master * np.conj(interest_region_slave)) / np.sqrt((np.absolute(interest_region_master) ** 2) * np.absolute(interest_region_slave) ** 2)
	complex_correlation = 10 * np.log10(interest_region_master * np.conj(interest_region_slave))
	magnitude_mean_values[x-1] = np.mean(np.absolute(complex_correlation))
	mean_values[x-1] = np.mean((c0/(15.5 * 1E6 * 4 * np.pi)) * np.angle(complex_correlation))
	mean_sum_values[x-1] = np.sum(mean_values[0:x-1])
	std_values[x-1] = np.std((c0/(15.5 * 1E6 * 4 * np.pi)) * np.angle(complex_correlation))
	date_values.append(datetime.strptime('.'.join((date, t)), '.'.join((date_format, time_format))))
	#print (datetime.strptime('.'.join((date, t)), '.'.join((date_format, time_format))))

fig = plt.figure(1)

plt.subplot(221)
plt.title('Sliding mean over the time', fontsize = 12)
plt.plot_date(date_values, mean_values, ls = 'solid')
plt.ylabel('Mean (mm)', fontsize = 10)
plt.xlabel('time', fontsize = 10)

plt.subplot(222)
plt.title('Sliding mean sum over the time', fontsize = 12)
plt.plot_date(date_values, mean_sum_values, ls = 'solid')
plt.ylabel('Mean sum (mm)', fontsize = 10)
plt.xlabel('time', fontsize = 10)

plt.subplot(223)
plt.title('Sliding std. Deviation over the time', fontsize = 12)
plt.plot_date(date_values, std_values, ls = 'solid')
plt.ylabel('Std. Deviation (mm)', fontsize = 10)
plt.xlabel('time', fontsize = 10)

plt.subplot(224)
plt.title('Magnitude mean over the time', fontsize = 12)
plt.plot_date(date_values, magnitude_mean_values, ls = 'solid')
plt.ylabel('Magnitude mean (normalized)', fontsize = 10)
plt.xlabel('time', fontsize = 10)

plt.tight_layout()
plt.show()
