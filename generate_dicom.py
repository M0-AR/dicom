"""Generate a valid, synthetic MR DICOM image with no patient data.

The output is safe to commit, share, and send to a test PACS. It is built from
public DICOM data elements only and contains a deterministic synthetic phantom.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import (
    PYDICOM_IMPLEMENTATION_UID,
    ExplicitVRLittleEndian,
    MRImageStorage,
    generate_uid,
)


def build_phantom(rows: int = 256, columns: int = 256) -> np.ndarray:
    """Return a deterministic 16-bit CT-like phantom."""
    y, x = np.mgrid[0:rows, 0:columns]
    cy, cx = (rows - 1) / 2.0, (columns - 1) / 2.0
    yy = (y - cy) / (rows * 0.36)
    xx = (x - cx) / (columns * 0.30)

    image = np.zeros((rows, columns), dtype=np.float32)
    body = (xx**2 + yy**2) <= 1.0
    image[body] = 1040.0

    for dx, dy, radius, value in [(-0.38, -0.18, 0.16, 1820.0), (0.34, 0.22, 0.12, 1560.0)]:
        lesion = ((xx - dx) ** 2 + (yy - dy) ** 2) <= radius**2
        image[lesion] = value

    gradient = np.broadcast_to(
        np.linspace(0.0, 180.0, columns, dtype=np.float32), (rows, columns)
    )
    image[body] += gradient[body]
    image += np.random.default_rng(7).normal(0.0, 18.0, (rows, columns)).astype(np.float32)
    return np.clip(image, 0, 4095).astype(np.uint16)


def build_dataset(
    patient_name: str = "SYNTHETIC^PATIENT",
    patient_id: str = "SYN-0001",
    rows: int = 256,
    columns: int = 256,
) -> Dataset:
    """Build an MR Image Storage dataset populated with required attributes."""
    now = datetime.now()
    date = now.strftime("%Y%m%d")
    time = now.strftime("%H%M%S")

    sop_instance_uid = generate_uid()
    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_uid = generate_uid()

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID

    ds = Dataset()
    ds.file_meta = file_meta

    ds.SpecificCharacterSet = "ISO_IR 100"
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.PatientBirthDate = ""
    ds.PatientSex = "O"
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.SOPInstanceUID = sop_instance_uid
    ds.FrameOfReferenceUID = frame_uid
    ds.SOPClassUID = MRImageStorage

    ds.StudyDate = date
    ds.SeriesDate = date
    ds.ContentDate = date
    ds.AcquisitionDate = date
    ds.StudyTime = time
    ds.SeriesTime = time
    ds.ContentTime = time
    ds.AcquisitionTime = time

    ds.Modality = "MR"
    ds.StudyID = "STUDY-001"
    ds.AccessionNumber = "ACC-0001"
    ds.StudyDescription = "Synthetic DICOM Toolchain Study"
    ds.SeriesDescription = "Synthetic Phantom"
    ds.InstitutionName = "Synthetic Imaging Lab"
    ds.ReferringPhysicianName = ""
    ds.Manufacturer = "DICOM Toolchain"
    ds.ManufacturerModelName = "Phantom Generator"
    ds.SoftwareVersions = "1.0"
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1
    ds.ImageType = ["ORIGINAL", "PRIMARY", "M", "ND"]

    ds.ImagePositionPatient = [0.0, 0.0, 0.0]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.PixelSpacing = [0.7, 0.7]
    ds.SliceThickness = 5.0
    ds.SpacingBetweenSlices = 5.0
    ds.SliceLocation = 0.0

    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = columns
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.PixelData = build_phantom(rows, columns).tobytes()

    return ds


def generate_file(
    output: str | Path = "test.dcm",
    patient_name: str = "SYNTHETIC^PATIENT",
    patient_id: str = "SYN-0001",
) -> Path:
    """Write a synthetic DICOM Part 10 file and return its path."""
    path = Path(output)
    ds = build_dataset(patient_name=patient_name, patient_id=patient_id)
    ds.save_as(path, enforce_file_format=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic MR DICOM image (zero PHI)."
    )
    parser.add_argument("-o", "--output", default="test.dcm", help="Output file path.")
    parser.add_argument("--patient-name", default="SYNTHETIC^PATIENT", help="Synthetic patient name.")
    parser.add_argument("--patient-id", default="SYN-0001", help="Synthetic patient ID.")
    args = parser.parse_args()

    path = generate_file(args.output, args.patient_name, args.patient_id)
    print(f"Created {path} ({path.stat().st_size:,} bytes) with zero patient data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
