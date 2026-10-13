# metashape-container

A container for Agisoft Metashape software, with a simple Python wrapper around its photogrammetry pipeline.

## Getting started

The `AGISOFT_FLS` environment variable needs to be set to your license server.

The container can be run using Docker via:

```bash
docker run --env AGISOFT_FLS=${AGISOFT_FLS} djmannion/metashape-pg:latest --help
```

or using Apptainer via:

```bash
apptainer run docker://djmannion/metashape-pg:latest --help
```

## Building

Use `make` to build the container.

This will download the files `metashape-pro_2_3_1_amd64.tar.gz` and `metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl` from the Agisoft website into the repository directory, if not already present.
