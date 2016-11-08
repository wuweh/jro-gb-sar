from __future__ import division
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft, ifft
from scipy import interpolate
import fnmatch
import time
import h5py
from tempfile import TemporaryFile, mkdtemp
import os.path as path

DATE_TIME = '10.10.16_12.21.17'

FOLDER_DATA = '/home/andre/sar_raw_data/experimentos_%s/'
NAME_DATA = 'datos_toma_%d.hdf5'

PATH_RESULTS = '/home/andre/sar_processed_data/Imaging'
FOLDER_RESULTS = '/datos_procesados_%s'
NAME_RESULTS = '/res_%s_toma_%d.hdf5'
FOLDER_IMAGES = '/imagenes_%s'
NAME_IMAGES = '/Imagen_%d_[%2f_%2f_%2f_%2f].png'

folders = []

for file in os.listdir(FOLDER_DATA %DATE_TIME):
	if fnmatch.fnmatch(file, '*.hdf5'):
		folders.append(file)

file = None

less_freq = False

if less_freq:
	FOLDER_RESULTS = '/datos_procesados2_%s'
	FOLDER_IMAGES = '/imagenes2_%s'

if not os.path.exists(PATH_RESULTS + FOLDER_RESULTS %(DATE_TIME)):
	os.makedirs(PATH_RESULTS + FOLDER_RESULTS %(DATE_TIME))

if not os.path.exists(PATH_RESULTS + FOLDER_IMAGES %(DATE_TIME)):
	os.makedirs(PATH_RESULTS + FOLDER_IMAGES %(DATE_TIME))

LONG_VUELTA = 66
PASOS_VUELTA = 20000
FACTOR_LONG_PASOS = 1000 * PASOS_VUELTA / LONG_VUELTA
win = False

for n_toma in range(1,len(folders)):
#for n_toma in range(1,2):
	tic = time.time()
	print "Procesando datos %s toma %d" %(DATE_TIME, n_toma)
	f = h5py.File(FOLDER_DATA %DATE_TIME + NAME_DATA %(n_toma), 'r')
	dset = f['sar_dataset']

	xai = dset.attrs['xi']
	xaf = dset.attrs['xf']
	dax = dset.attrs['dx']
	nx = dset.attrs['npos']
	fre_min = dset.attrs['fi']
	fre_max = dset.attrs['ff']
	t = dset.attrs['time']
	date = dset.attrs['date']
	nfre = dset.attrs['nfre']
	s21 = np.empty([nx, nfre], dtype = np.complex64)
	s21 = dset[...]
	f.close()

	if less_freq:
		nfre = (int(nfre / 2)) + 1
		s21_new = np.zeros([nx, nfre], dtype = np.complex64)
		for i in range(nx):
			if i%2 != 0:
				s21_new[:,i] = s21[:,i]

	fre_c = (fre_min+fre_max)/2
	df = (fre_max - fre_min) / (nfre - 1)

	xi =  -2.0
	xf =  2.0
	yi =  0.0
	yf =  10.0

	c0  =  299792458.0
	R0 	=  0.0
	dx    =  0.01
	dy    =  0.01
	nposx =  int(np.ceil((xf - xi) / dx) + 1)
	nposy =  int(np.ceil((yf - yi) / dy) + 1)
	xf    =  xi + dx * (nposx - 1)
	yf    =  yi + dy * (nposy - 1)

	fact  =  8
	nr = 2 ** int(np.ceil(np.log2(nfre*fact)))

	n  = np.arange(nr)
	B  = df*nr
	dr = c0 / (2*B)

	rn   = dr * n
	R    = dr * nr
	npos = nposx * nposy

	xa = xai + dax*np.arange(nx)
	xn = xi + dx*np.arange(nposx)
	yn = yi + dy*np.arange(nposy)
	Imagen = np.zeros([npos], dtype = complex)
	s21_arr = np.zeros([nr], dtype = complex)
	Rnk = np.zeros([npos], dtype = float)
	freq = np.arange(nfre)

	if win:
		#Window Range
		Wr = 1.0 - np.cos(2*np.pi*np.arange(1,nfre+1)/(nfre+1))
		for k in range(0,nx):
			s21[k,:] = Wr * s21[k,:]
		#Window Cross-range
		Wx = 1.0 - np.cos(2*np.pi*np.arange(1,nx+1)/(nx+1))
		for f in range(0,nfre):
			s21[:,f] = Wx * s21[:,f]

	nc0 = int(nfre/2.0)
	nc1 = int((nfre+1)/2.0)

	for k in range(0,nx):
		for y in range(0, nposy):
			Rnk[y * nposx: (y+1) * nposx] = np.sqrt((xn - xa[k])**2 + yn[y]**2)

		s21_arr[0:nc1] = s21[k,nc0:nfre]
		s21_arr[nr-nc0:nr] = s21[k,0:nc0]

		Fn0 = nr*ifft(s21_arr[:], n = nr)

		Fn = np.interp(Rnk - R0, rn, np.real(Fn0), period = R) + 1j * np.interp(Rnk - R0, rn, np.imag(Fn0), period = R)
		Fn *= np.exp(4j * np.pi * (fre_min/c0) * (Rnk - R0))
		Imagen +=  Fn

	Imagen /= (nfre * (nx))
	Imagen = np.reshape(Imagen, (nposy, nposx))
	Imagen = np.flipud(Imagen)

	f = h5py.File(PATH_RESULTS + FOLDER_RESULTS %(DATE_TIME) + NAME_RESULTS %(DATE_TIME, n_toma), 'w')
	dset = f.create_dataset("Complex_image", (nposy, nposx), dtype = np.complex64)
	dset.attrs['dx'] = dx
	dset.attrs['dy'] = dy
	dset.attrs['date'] = date
	dset.attrs['time'] = t
	dset.attrs['ntoma'] = n_toma
	dset.attrs['xi'] = xi
	dset.attrs['xf'] = xf
	dset.attrs['yi'] = yi
	dset.attrs['yf'] = yf
	dset.attrs['fi'] = fre_min
	dset.attrs['ff'] = fre_max
	dset[...] = Imagen
	f.close()

	Imagen = np.absolute(Imagen)

	fig = plt.figure(1)
	im = plt.imshow(Imagen, cmap = 'jet', aspect = 'auto', extent = [xi,xf,yi,yf])
	cbar = plt.colorbar(im, orientation = 'vertical')
	plt.ylabel('Range (m)', fontsize = 14)
	plt.xlabel('Cross-range (m)', fontsize = 14)
	plt.savefig(PATH_RESULTS + FOLDER_IMAGES %(DATE_TIME) + NAME_IMAGES %(n_toma,xi,xf,yi,yf))
	fig.clear()
	print 'Se demoro %f' %(time.time() - tic)
