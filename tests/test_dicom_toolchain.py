"""End-to-end checks for generation, file validity, and C-STORE delivery."""

from __future__ import annotations

import socket

import pytest
from pydicom import dcmread
from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage
from pynetdicom import AE, AllStoragePresentationContexts, evt

from dicom_server_request import send_file
from generate_dicom import generate_file


@pytest.fixture()
def dicom_file(tmp_path):
    path = generate_file(tmp_path / "test.dcm")
    yield path
    path.unlink(missing_ok=True)


def test_generated_file_is_valid_part10(dicom_file):
    ds = dcmread(dicom_file)
    assert ds.preamble == b"\x00" * 128
    assert ds.file_meta.TransferSyntaxUID == ExplicitVRLittleEndian
    assert ds.SOPClassUID == MRImageStorage
    assert ds.SOPInstanceUID == ds.file_meta.MediaStorageSOPInstanceUID
    assert ds.PatientName == "SYNTHETIC^PATIENT"
    assert ds.PatientID == "SYN-0001"
    assert ds.Modality == "MR"
    assert ds.Rows == 256 and ds.Columns == 256
    assert len(ds.PixelData) == ds.Rows * ds.Columns * 2


def test_generated_file_contains_a_renderable_phantom(dicom_file):
    ds = dcmread(dicom_file)
    pixels = ds.pixel_array
    assert pixels.shape == (256, 256)
    assert pixels.dtype.name == "uint16"
    assert pixels.max() > pixels.min()
    assert pixels.mean() > 0


def test_uids_are_unique_between_runs(tmp_path):
    first = dcmread(generate_file(tmp_path / "a.dcm"))
    second = dcmread(generate_file(tmp_path / "b.dcm"))
    assert first.StudyInstanceUID != second.StudyInstanceUID
    assert first.SOPInstanceUID != second.SOPInstanceUID


def test_send_file_to_live_scp(dicom_file):
    received = []

    def handle_store(event):
        received.append(event.dataset)
        return 0x0000

    scp = AE(ae_title="TEST_SCP")
    scp.supported_contexts = AllStoragePresentationContexts
    handlers = [(evt.EVT_C_STORE, handle_store)]

    server = scp.start_server(("127.0.0.1", 0), evt_handlers=handlers, block=False)
    port = server.server_address[1]
    try:
        result = send_file(
            file_path=dicom_file,
            host="127.0.0.1",
            port=port,
            calling_ae="TEST_SCU",
            called_ae="TEST_SCP",
            timeout=5,
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result == 0
    assert len(received) == 1
    assert received[0].SOPInstanceUID == dcmread(dicom_file).SOPInstanceUID


def test_send_rejects_missing_file(tmp_path):
    assert send_file(tmp_path / "missing.dcm", host="127.0.0.1", port=1) == 2


def test_send_handles_unreachable_server(dicom_file):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        free_port = sock.getsockname()[1]
    assert send_file(dicom_file, host="127.0.0.1", port=free_port, timeout=0.5) == 1
