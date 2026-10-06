# metashape-container

Apptainer definition for Agisoft Metashape software.

## Getting started

The `AGISOFT_FLS` environment variable needs to be used to set the license server.

Executing the container will run a simple Python wrapper around the Metashape photogrammetry pipeline; see `pg.py` for the details.

## Building

Use `make` to build the container.

This will download the files `metashape-pro_2_3_1_amd64.tar.gz` and `metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl` from the Agisoft website into the repository directory, if not already present.
