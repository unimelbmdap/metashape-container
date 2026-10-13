VERSION ?= 0.1


.PHONY: docker
docker: Dockerfile metashape-pro_2_3_1_amd64.tar.gz metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl pg.py
	docker build . -t djmannion/metashape-pg:${VERSION}
	docker tag djmannion/metashape-pg:${VERSION} djmannion/metashape-pg:latest

.PHONY: push
push:
	docker push djmannion/metashape-pg:${VERSION}
	docker push djmannion/metashape-pg:latest

metashape-pro_2_3_1_amd64.tar.gz:
	wget https://download.agisoft.com/$@

metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl:
	wget https://download.agisoft.com/$@

metashape.sif: Dockerfile metashape-pro_2_3_1_amd64.tar.gz metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl pg.py
	apptainer build $@ dockerfile:.

.PHONY: test
test:

.PHONY: clean
clean:
	rm metashape-pro_2_3_1_amd64.tar.gz metashape-2.3.1-cp39.cp310.cp311.cp312.cp313-abi3-linux_x86_64.whl metashape.sif
