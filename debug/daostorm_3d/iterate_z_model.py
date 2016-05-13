"""Create files for sdt.loc.daostorm_3d.fit single iteration tests (z model)"""
import os

import numpy as np

from sa_library import multi_fit_c
from sa_library.multi_fit_c import multi

import sim_astigmatism


fit_path = os.path.join("tests", "daostorm_3d", "data_fit")
imgfile = os.path.join(fit_path, "z_sim_img.npz")
finderfile = os.path.join(fit_path, "z_sim_finder.npz")

frame = np.load(imgfile)["img"].astype(np.float)
peaks = np.load(finderfile)["peaks"]  # generated by `find.py`

model = "Z"
tol = 1e-6
scmos_cal = False

wx_params = np.hstack(sim_astigmatism.params_um.x)
wy_params = np.hstack(sim_astigmatism.params_um.y)
wx_params[0] *= 2  # double since the C implementation wants it so
wy_params[0] *= 2

fitfunc = getattr(multi, "iterate"+model)

if model == "Z":
    multi_fit_c.initZParams(wx_params, wy_params,
                            *sim_astigmatism.params_um.z_range)

multi.initialize(frame, np.zeros(frame.shape), peaks, tol,
                 frame.shape[1], frame.shape[0], len(peaks), model == "Z")
fitfunc()
result = multi_fit_c.getResults(len(peaks))
residual = multi_fit_c.getResidual(frame.shape[0], frame.shape[1])
multi.cleanup()

outfile = os.path.join(fit_path, "z_sim_iter_"+model.lower()+".npz")
# np.savez_compressed(outfile, peaks=result, residual=residual)