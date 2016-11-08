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
#import matplotlib.dates as mdates

RUTA_DATOS_PROCESADOS = "/home/andre/sar_processed_data/Imaging/"
FOLDER_DATOS_PROCESADOS = "datos_procesados_%s"
FECHA_HORA = "10.10.16_12.21.17"

RUTA = RUTA_DATOS_PROCESADOS + FOLDER_DATOS_PROCESADOS %FECHA_HORA + '/'

RUTA_DESPLAZAMIENTOS = "/home/andre/sar_processed_data/Sliding/"
NOMBRE_DESPLAZAMIENTOS = "Desplazamientos_%s/"

folders = []
c0  =  299792458.0
threshold = 0.9
time_format = "%H.%M.%S"
date_format = "%d.%m.%y"

if not os.path.exists(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA):
	os.makedirs(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA)

for file in os.listdir(RUTA):
	if fnmatch.fnmatch(file, '*.hdf5'):
		folders.append(file)

std_values = np.zeros([len(folders)], dtype = float)
mean_values = np.zeros([len(folders)], dtype = float)
date_values = np.zeros([len(folders)], dtype = float)

for x in range(1, len(folders)):
	for file in folders:
		datos = '%d.hdf5' %x
		if fnmatch.fnmatch(file, '*' + 'toma_' + datos):
			datos = file
			break

	f = h5py.File(RUTA + datos, 'r')
	dset = f["Complex_image"]
	Imagen_master = dset[...]
	if x == 1:
		xi = dset.attrs["xi"]
		xf = dset.attrs["xf"]
		yi = dset.attrs["yi"]
		yf = dset.attrs["yf"]
		t1 = dset.attrs["time"]
	f.close()

	for file in folders:
		datos = '%d.hdf5' %(x + 1)
		if fnmatch.fnmatch(file, '*' + 'toma_' + datos):
			datos = file
			break

	file_temp = h5py.File(RUTA + datos, 'r')
	dset = file_temp["Complex_image"]
	t2 = dset.attrs["time"]
	Imagen_slave = dset[...]
	file_temp.close()

	if x == 1:
		complex_correlation_num = (Imagen_master * np.conj(Imagen_slave))
		complex_correlation_den = np.sqrt(np.absolute(Imagen_master)**2 * np.absolute(Imagen_slave)**2)

	complex_correlation_num += (Imagen_master * np.conj(Imagen_slave))
	complex_correlation_den += np.sqrt(np.absolute(Imagen_master)**2 * np.absolute(Imagen_slave)**2)
	#complex_correlation = signal.convolve2d(complex_correlation, kernel)

complex_correlation = complex_correlation_num / complex_correlation_den

fig = plt.figure(1)
fig.suptitle("Complex correlation magnitude", fontsize = 14)
im = plt.imshow(np.absolute(complex_correlation), cmap = 'jet', aspect = 'auto', extent = [xi,xf,yi,yf])
cbar = plt.colorbar(im, orientation = 'vertical')
plt.ylabel('Range (m)', fontsize = 10)
plt.xlabel('Cross-range (m)', fontsize = 10)
plt.savefig(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA + "complex_correlation_magnitude_%s.png" %FECHA_HORA)
fig.clear()

mask = np.absolute(complex_correlation)
mask2 = mask
low_value_indices = mask < threshold
high_value_indices = mask >= threshold
mask[low_value_indices] = 0
mask[high_value_indices] = 1
mask2[low_value_indices] = False
mask2[high_value_indices] = True
mask_complex_correlation = ma.array(complex_correlation, mask = mask2)

fig = plt.figure(1)
fig.suptitle("Mask", fontsize = 14)
im = plt.imshow(mask, cmap = 'Greys', interpolation = 'None', aspect = 'auto', extent = [xi,xf,yi,yf])
plt.ylabel('Range (m)', fontsize = 10)
plt.xlabel('Cross-range (m)', fontsize = 10)
plt.savefig(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA + "/mask_th_%.2f_%s.png" %(threshold, FECHA_HORA))
fig.clear()

for x in range(1, len(folders)):
	for file in folders:
		datos = '%d.hdf5' %x
		if fnmatch.fnmatch(file, '*' + 'toma_' + datos):
			datos = file
			break

	f = h5py.File(RUTA + datos, 'r')
	dset = f["Complex_image"]

	if x == 1:
		xi = dset.attrs["xi"]
		xf = dset.attrs["xf"]
		yi = dset.attrs["yi"]
		yf = dset.attrs["yf"]
	Imagen_master = dset[...]
	f.close()

	for file in folders:
		datos = '%d.hdf5' %(x + 1)
		if fnmatch.fnmatch(file, '*' + 'toma_' + datos):
			datos = file
			break

	file_temp = h5py.File(RUTA + datos, 'r')
	dset = file_temp["Complex_image"]
	t = dset.attrs["time"]
	date = dset.attrs["date"]
	Imagen_slave = dset[...]
	file_temp.close()

	aux = Imagen_master * np.conj(Imagen_slave)
	mean = np.sum(np.angle(aux) * mask) / mask_complex_correlation.count()

	mean_values[x-1] = mean
	std_values[x-1] = np.sqrt(np.sum(((np.angle(aux) - mean) * mask) ** 2) / mask_complex_correlation.count())
	date_values[x-1] = dates.date2num(datetime.strptime('.'.join((date, t)), '.'.join((date_format, time_format))))

'''
new_date = [datetime(date_value) for date_value in date_values]
print(new_date)
print(type(new_date[0]))
'''
fig = plt.figure(1)

plt.subplot(211)
plt.title('Mean over the time', fontsize = 12)
plt.plot(mean_values)
plt.ylabel('Mean', fontsize = 10)
plt.xlabel('time', fontsize = 10)

plt.subplot(212)
plt.title('Std. Deviation over the time', fontsize = 12)
plt.plot(std_values)
plt.ylabel('Std. Deviation', fontsize = 10)
plt.xlabel('time', fontsize = 10)
plt.tight_layout()
#plt.savefig(RUTA_DESPLAZAMIENTOS + NOMBRE_DESPLAZAMIENTOS %FECHA_HORA + "/mean_stddev_%s.png" %(FECHA_HORA))
plt.show()
