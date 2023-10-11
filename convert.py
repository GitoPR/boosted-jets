import argparse
import awkward as ak
import h5py
import numpy as np
import uproot
import os
import vector

from pathlib import Path
from typing import List, Optional
from utils import IsReadableDir, IsValidFile


def parse_source(source: Path, target: Path) -> None:
    _file = uproot.open(source)
    _tree = _file["l1NtupleProducer/efficiencyTree"]

    # Process inputs
    deposits = _tree["jetRegionEt"].array()
    deposits = ak.flatten(deposits)

    # Process labels
    labels = _tree["allL1Signals"].array()
    labels = ak.flatten(labels, axis=None)

    # Read the reconstruction data
    reco_pt = _tree["recoPt_1"].array()
    reco_eta = _tree["recoEta_1"].array()
    reco_phi = _tree["recoPhi_1"].array()

    # Read the L1 jets data
    l1_pt = _tree["l1Pt_1"].array()
    l1_jets = _tree["allL1Jets"].array()
    jets_per_event = [len(_) for _ in l1_jets]

    lv_eta = ak.broadcast_arrays(reco_eta, l1_jets)[0]
    lv_phi = ak.broadcast_arrays(reco_phi, l1_jets)[0]
    l1_jets = ak.flatten(l1_jets)
    lorenz_vectors = vector.arr(
        {
            "px": l1_jets[:]["fP"]["fX"],
            "py": l1_jets[:]["fP"]["fY"],
            "pz": l1_jets[:]["fP"]["fZ"],
            "pt": l1_jets[:]["fE"],
        }
    )

    l1_jets_deltas = (
        (lorenz_vectors.eta - ak.flatten(lv_eta)) ** 2
        + (lorenz_vectors.phi - ak.flatten(lv_phi)) ** 2
    ) ** 0.5
    l1_jets_pts = lorenz_vectors.pt

    # Write all the arrays into the H5 file.
    with h5py.File(f"{target}/dataset.h5", "w") as f:
        f.create_dataset("deposits", data=deposits.to_numpy())
        f.create_dataset("labels", data=labels.to_numpy())
        f.create_dataset("reco_eta", data=reco_eta.to_numpy())
        f.create_dataset("reco_phi", data=reco_phi.to_numpy())
        f.create_dataset("reco_pt", data=reco_pt.to_numpy())
        f.create_dataset("l1_pt", data=l1_pt.to_numpy())
        f.create_dataset("l1_jets", data=l1_jets.to_numpy())
        f.create_dataset("l1_jets_deltas", data=l1_jets_deltas.to_numpy())
        f.create_dataset("l1_jets_pts", data=l1_jets_pts)
        f.create_dataset("jets_per_event", data=jets_per_event)


def main(args_in: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        """Convert CMS Calorimeter Layer-1 Trigger region energy deposits from ROOT to HDF5 format"""
    )
    parser.add_argument(
        "filepath", action=IsValidFile, help="Input ROOT file", type=Path
    )
    parser.add_argument(
        "savepath", action=IsReadableDir, help="Output HDF5 file", type=Path
    )
    args = parser.parse_args(args_in)
    parse_source(args.filepath, args.savepath)


if __name__ == "__main__":
    main()
