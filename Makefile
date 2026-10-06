
.PHONY: all
all: metashape.sif

metashape-pro_2_3_1_amd64.tar.gz:
	wget https://download.agisoft.com/$@

metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl:
	wget https://download.agisoft.com/$@

metashape.sif: metashape-pro_2_3_1_amd64.tar.gz metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl pg.py metashape.def
	apptainer build $@ metashape.def

.PHONY: test
test:

.PHONY: clean
clean:
	rm metashape-pro_2_3_1_amd64.tar.gz metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl metashape.sif
