import scipy.io as sp_io
import pandas as pd
import collections

name_trans = collections.OrderedDict((
    ("x-Position", "x"),
    ("y-Position", "y"),
    ("Integrated Intensity", "mass"),
    ("Radius of Gyration", "size"),
    ("Excentricity", "ecc"),
    ("Maximal Pixel Intensity", "signal"),
    ("Background per Pixel", "background"),
    ("Standard Deviation of Background", "bg_deviation"),
    ("Frame Number", "frame"),
    ("Time in Frames", "time")))


def load_particle_tracker_positions(filename, load_protocol=True,
                                    adjust_index=["x", "y", "frame"],
                                    column_names=None):
    pos = sp_io.loadmat(filename)["MT"]

    cols = []
    if load_protocol:
        proto_path = filename[:filename.rfind("positions.mat")] + "protocol.mat"
        name_str = sp_io.loadmat(proto_path)["X"][0][0][9][0]
        names = name_str.split(", ")

        for n in names:
            tn = name_trans.get(n)
            if tn is None:
              tn = n
            cols.append(tn)
    elif column_names is not None:
        cols = column_names
    else:
        for k, v in name_trans.items():
            cols.append(v)

    #append cols with names for unnamed columns
    for i in range(len(cols), pos.shape[1]+3):
        cols.append("column{}".format(i))

    #columns name list cannot have more columns than there are in the file
    cols = cols[:pos.shape[1]]

    df = pd.DataFrame(pos, columns=cols)
    for c in adjust_index:
        if c in df.columns:
            df[c] -= 1

    return df