# DICOM Toolchain: Automated Generation & Transmission

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![DICOM Standard](https://img.shields.io/badge/DICOM-PS3.0-green.svg)](https://www.dicomstandard.org/)

A robust, lightweight Python-based suite designed for the healthcare industry to streamline the generation of synthetic DICOM (Digital Imaging and Communications in Medicine) data and facilitate seamless integration testing with PACS (Picture Archiving and Communication Systems).

---

## 📋 Table of Contents
- [Executive Summary](#-executive-summary)
- [Key Features](#-key-features)
- [Technical Architecture](#-technical-architecture)
- [Getting Started](#-getting-started)
- [Usage Guide](#-usage-guide)
- [Technical Deep Dive](#-technical-deep-dive)
- [Business Value](#-business-value)
- [Future Roadmap](#-future-roadmap)

---

## 🚀 Executive Summary

In the modern medical imaging landscape, the ability to rapidly prototype, test, and validate imaging workflows is critical. This repository provides a dual-component solution:
1.  **Generation**: Programmatically create valid, standards-compliant DICOM files.
2.  **Transmission**: Securely push medical imaging data to remote DICOM servers (like Orthanc or DCM4CHEE) using the C-STORE protocol.

Whether you are a developer building a new AI diagnostic tool or a clinical engineer stress-testing a hospital's PACS infrastructure, this toolchain offers the precision and reliability required.

---

## ✨ Key Features

- **Synthetic Data Generation**: Create MR (Magnetic Resonance) images with unique UIDs and metadata.
- **Protocol Compliance**: Implements the DICOM C-STORE SCU (Service Class User) role.
- **Dynamic Metadata**: Automatic generation of Study, Series, and SOP Instance UIDs.
- **Customizable Endpoints**: Configurable for any DICOM-compliant AE (Application Entity).
- **Lightweight & Portable**: Minimal dependencies, easy to integrate into CI/CD pipelines.

---

## 🏗 Technical Architecture

The workflow follows a classic producer-consumer pattern:

```mermaid
graph LR
    A[generate_dicom.py] -->|Produces| B(test.dcm)
    B -->|Ingested by| C[dicom_server_request.py]
    C -->|C-STORE| D[Remote DICOM Server / PACS]
```

---

## 🛠 Getting Started

### Prerequisites
- Python 3.8 or higher
- Access to a DICOM server (Optional: for testing transmission)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies**:
   ```bash
   pip install pydicom pynetdicom
   ```

---

## 📖 Usage Guide

### 1. Generating a DICOM File
Run the generator script to create a sample MR image dataset.

```bash
python3 generate_dicom.py
```
*   **Output**: Creates a file named `test.dcm` in the local directory.
*   **Action**: Generates a synthetic "Test Patient" with a unique MR modality profile.

### 2. Sending Data to a PACS/Server
Once the file is generated, use the request script to transmit it.

```bash
python3 dicom_server_request.py
```
*   **Process**:
    1.  Initiates a DICOM Association.
    2.  Negotiates Presentation Contexts.
    3.  Performs a C-STORE operation.
*   **Note**: Ensure the `orthanc_server_ip` and `orthanc_server_port` in the script match your target server environment.

---

## 🔍 Technical Deep Dive

### Data Structure (`generate_dicom.py`)
The generator populates the following essential DICOM tags:
- **Patient Attributes**: Name (`PatientName`), ID (`PatientID`).
- **UID Management**: Uses `generate_uid()` for Study, Series, and SOP instances to ensure uniqueness in database systems.
- **Modality**: Defaults to `MR` (Magnetic Resonance).
- **Transfer Syntax**: Utilizes `Explicit VR Little Endian` for maximum compatibility.

### Networking Protocol (`dicom_server_request.py`)
- **Association**: Establishes a TCP/IP connection with the remote Application Entity.
- **Status Codes**: Captures and reports the `0x0000` success status or specific DICOM error codes.

---

## 💼 Business Value

- **Reduced Development Costs**: Avoid the need for expensive clinical imaging hardware during early-stage development.
- **Compliance & QA**: Perfect for validating that your software correctly handles DICOM headers and network handshake protocols.
- **Privacy First**: Use synthetic data for testing to ensure zero exposure of Protected Health Information (PHI/PII), aligning with HIPAA/GDPR standards.

---

## 🗺 Future Roadmap

- [ ] **Support for Multiple Modalities**: CT, X-Ray, and Ultrasound generation profiles.
- [ ] **Batch Processing**: Tooling to send entire directories of DICOM files.
- [ ] **Pixel Data Integration**: Ability to embed real or synthetic image pixel arrays.
- [ ] **Secure DICOM**: Support for TLS-enabled associations.

---

*Developed with ❤️ for the Medical Imaging Community.*
