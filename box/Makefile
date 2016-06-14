
BOX_VERSION = 0.2

define BOXYML
name: substance-box
version: $(BOX_VERSION)
description: Substance Box base image
registry: http://bbeausej.developers.turbulent.ca/boxes/substance-box/$(BOX_VERSION)
endef
export BOXYML

all: build/substance-base/substance-base-disk1.vmdk build/substance-box/substance-disk1.vmdk export

build/substance-base/substance-base-disk1.vmdk: substance-base.packer.json
	@echo ""
	@echo "===> Building substance-base image with preseed"
	@echo ""
	packer build -force $< 

build/substance-box/substance-disk1.vmdk: substance-box.packer.json
	@echo ""
	@echo "===> Building substance-box image with salt"
	@echo ""
	packer build -force $<

export:
	@echo ""
	@echo "Producing box artifact substance-box-$(BOX_VERSION).box"
	@echo ""
	@echo "$$BOXYML" > build/box.yml
	@cp build/substance-box/substance.ovf build/box.ovf
	@cp build/substance-box/substance-disk1.vmdk build/box-disk1.vmdk
	@cd build && \
		tar cvzf substance-box-$(BOX_VERSION).box box.yml box.ovf box-disk1.vmdk && \
	  cd -
	@rm -f build/box.yml build/box.ovf build/box-disk1.vmdk

clean:
	rm -rf build/*

.PHONY: all  export clean
