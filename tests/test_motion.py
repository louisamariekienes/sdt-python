import unittest
import os

import pandas as pd
import numpy as np

from sdt.motion import calculate_sd, emsd
import sdt.data


path, f = os.path.split(os.path.abspath(__file__))
data_path = os.path.join(path, "data_motion")


class TestMotion(unittest.TestCase):
    def setUp(self):
        pass

    def _compare_matlab(self, py, mat):
        for i in py:
            pyi = py[i]
            try:
                mati = (mat[i-1] if not np.isscalar(mat[i-1])
                        else np.array([mat[i-1]]))
            except:
                raise AssertionError
            np.testing.assert_allclose(np.sort(pyi), np.sort(mati),
                                       rtol=1e-5, atol=1e-5)

    def test_calculate_sd(self):
        # Original file: 2015-06-12 - PMPC single molecule/AF-647 POPC/
        #   B-1_000_.SPE
        orig = np.load(os.path.join(data_path, "test_calculate_sd.npy"))
        traj = sdt.data.load(os.path.join(data_path, "B-1_000__tracks.mat"))
        sd = calculate_sd(traj, 1, 1)
        assert(len(sd) == len(orig))
        self._compare_matlab(sd, orig)

    def test_emsd(self):
        orig = np.load(os.path.join(data_path, "test_calculate_sd.npy"))
        traj = sdt.data.load(os.path.join(data_path, "B-1_000__tracks.mat"))
        e = emsd(traj, 1, 1)
        e_mat = e[["msd", "stderr"]].as_matrix()
        for i, (msd, stderr) in enumerate(e_mat):
            if np.isscalar(orig[i]):
                o = np.array([orig[i]])
            else:
                o = orig[i]
            np.testing.assert_allclose(msd, np.mean(o), rtol=1e-6)
            stderr_orig = np.std(o, ddof=1)/np.sqrt(len(o))
            np.testing.assert_allclose(stderr, stderr_orig, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
