# metashape-container

Apptainer definition for Agisoft Metashape software.

This requires the files `metashape-pro_2_3_1_amd64.tar.gz` and `metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl` to be downloaded from the Agisoft website and placed in the repository directory.

The `AGISOFT_FLS` environment variable can be used to set the license server.

Executing the container will run a simple Python wrapper around the Metashape photogrammetry pipeline; see `pg.py` for the details.
