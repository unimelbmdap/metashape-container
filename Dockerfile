FROM ubuntu:26.04

ENV PATH=/opt/metashape-pro/venv/bin:${PATH}

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	python3 python3-pip \
	&& apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libdbus-1-3 \
        libgssapi-krb5-2 \
        ca-certificates \
        libgl1 \
        libx11-6 libx11-xcb1 libxext6 libxrender1 libxi6 \
        libxrandr2 libxss1 libxtst6 libxcomposite1 libxcursor1 libxfixes3 \
        libxkbcommon-x11-0 \
        libxcb1 libxcb-cursor0 libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 \
        libxcb-xinerama0 libxcb-xinput0 \
        libxcb-shm0 libxcb-shape0 \
        less \
        libglu1-mesa \
        libcurl4t64 \
        libfontconfig1 \
    	intel-opencl-icd ocl-icd-libopencl1 clinfo \
	pocl-opencl-icd libpocl-dev opencl-headers \
        libsm6 \
    	&& rm -rf /var/lib/apt/lists/*

COPY metashape-pro_2_3_1_amd64.tar.gz /opt
COPY metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl /opt
COPY pg.py /opt

RUN <<EOF
cd /opt
tar xzf metashape-pro_2_3_1_amd64.tar.gz
rm metashape-pro_2_3_1_amd64.tar.gz
EOF

RUN <<EOF
cd /opt/metashape-pro
/opt/metashape-pro/python/bin/python3.12 -m venv venv
/opt/metashape-pro/venv/bin/pip install /opt/metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl
/opt/metashape-pro/venv/bin/pip install ipython
ln -s /opt/metashape-pro/python/lib /opt/metashape-pro/python/bin/lib
rm /opt/metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl
EOF

ENTRYPOINT ["/opt/metashape-pro/venv/bin/python", "/opt/pg.py"]
