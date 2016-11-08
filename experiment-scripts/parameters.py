c0 = 299792458.0
xi = 0.01
xf = 1.4
fi = 15.5
ff = 16.5
nfre = 1001
ptx = 'HIGH'
ifbw = 1000
timespan = 3 * (24 * 60 * 60)

xi = int(xi * METERS_TO_STEPS_FACTOR)
xf = int(xf * METERS_TO_STEPS_FACTOR)
dx = int((c0  / (4.0 * ff * 1E9)) * METERS_TO_STEPS_FACTOR)
npos = int(((xf - xi) / dx) + 1.0)
xf = xi + dx * (npos - 1)
