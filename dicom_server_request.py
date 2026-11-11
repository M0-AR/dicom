"""Send a DICOM file to a PACS or DICOM server using the C-STORE service."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from pydicom import dcmread
from pynetdicom import AE
from pynetdicom.sop_class import Verification


def send_file(
    file_path: str | Path = "test.dcm",
    host: str = "127.0.0.1",
    port: int = 4242,
    calling_ae: str = "DICOM_TOOLKIT",
    called_ae: str = "ORTHANC",
    timeout: float = 10.0,
    echo: bool = False,
) -> int:
    """Perform an association and C-STORE; return a process exit code."""
    path = Path(file_path)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    ds = dcmread(path)
    if "SOPClassUID" not in ds or "SOPInstanceUID" not in ds:
        print("Refusing to send: the file has no SOP Class or SOP Instance UID.", file=sys.stderr)
        return 2

    ae = AE(ae_title=calling_ae)
    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout
    ae.network_timeout = timeout
    ae.add_requested_context(ds.SOPClassUID)
    if echo:
        ae.add_requested_context(Verification)

    print(f"Connecting to {host}:{port} as {calling_ae} -> {called_ae} ...")
    assoc = ae.associate(host, port, ae_title=called_ae)

    if not assoc.is_established:
        print("Association rejected, aborted, or the server is unreachable.", file=sys.stderr)
        return 1

    try:
        if echo:
            echo_status = assoc.send_c_echo()
            if not echo_status or echo_status.Status != 0x0000:
                print("C-ECHO failed; the server did not confirm DICOM connectivity.", file=sys.stderr)
                return 1
            print("C-ECHO status: 0x0000 (DICOM connectivity confirmed)")

        status = assoc.send_c_store(ds)
        if not status:
            print("C-STORE timed out, was aborted, or returned an invalid response.", file=sys.stderr)
            return 1

        code = status.Status
        print(f"C-STORE status: 0x{code:04X}")
        if code == 0x0000:
            print(f"Stored {ds.SOPInstanceUID} successfully.")
            return 0
        if 0xB000 <= code <= 0xBFFF:
            print("Stored with warnings. Check the PACS logs for coercion details.")
            return 0
        print("The server rejected the instance. See the status code in the DICOM standard.", file=sys.stderr)
        return 1
    finally:
        assoc.release()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send a DICOM file to a PACS using C-STORE."
    )
    parser.add_argument("-f", "--file", default="test.dcm", help="DICOM file to send.")
    parser.add_argument("--host", default=os.getenv("DICOM_HOST", "127.0.0.1"), help="PACS hostname or IP.")
    parser.add_argument("--port", type=int, default=int(os.getenv("DICOM_PORT", "4242")), help="PACS DICOM port.")
    parser.add_argument("--calling-ae", default=os.getenv("DICOM_CALLING_AE", "DICOM_TOOLKIT"), help="Local AE title.")
    parser.add_argument("--called-ae", default=os.getenv("DICOM_CALLED_AE", "ORTHANC"), help="Remote AE title.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Network timeout in seconds.")
    parser.add_argument("--echo", action="store_true", help="Run C-ECHO before C-STORE.")
    args = parser.parse_args()

    return send_file(
        file_path=args.file,
        host=args.host,
        port=args.port,
        calling_ae=args.calling_ae,
        called_ae=args.called_ae,
        timeout=args.timeout,
        echo=args.echo,
    )


if __name__ == "__main__":
    raise SystemExit(main())
