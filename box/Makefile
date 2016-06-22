
BOX_NS = turbulent
BOX_NAME = substance-box
BOX_VERSION = 0.2

define BOXYML
name: $(BOX_NAME)
version: $(BOX_VERSION)
description: Substance Box base image
registry: http://bbeausej.developers.turbulent.ca/$(BOX_NS)/$(BOX_NAME)-$(BOX_VERSION).json
endef
export BOXYML

all: build/substance-base/substance-base-disk1.vmdk build/$(BOX_NAME)/substance-disk1.vmdk build/$(BOX_NAME)-$(BOX_VERSION).json export

build/substance-base/substance-base-disk1.vmdk: substance-base.packer.json
	@echo ""
	@echo "===> Building substance-base image with preseed"
	@echo ""
	packer build -force $< 

build/$(BOX_NAME)/substance-disk1.vmdk: $(BOX_NAME).packer.json
	@echo ""
	@echo "===> Building $(BOX_NAME) image with salt"
	@echo ""
	packer build -force $<

build/$(BOX_NAME)-$(BOX_VERSION).box: build/$(BOX_NAME)/substance-disk1.vmdk
	@echo ""
	@echo "Producing box artifact $(BOX_NAME)-$(BOX_VERSION).box"
	@echo ""
	@echo "$$BOXYML" > build/box.yml
	@cp build/$(BOX_NAME)/substance.ovf build/box.ovf
	@cp build/$(BOX_NAME)/substance-disk1.vmdk build/box-disk1.vmdk
	@sed -i '.bak' 's/substance-disk1.vmdk/box-disk1.vmdk/g' build/box.ovf
	@cd build && \
		tar cvzf $(BOX_NAME)-$(BOX_VERSION).box box.yml box.ovf box-disk1.vmdk && \
	  cd -
	@rm -f build/box.yml build/box.ovf build/box-disk1.vmdk build/box.ovf.bak


build/$(BOX_NAME)-$(BOX_VERSION).json: support/boxjson.m4 build/$(BOX_NAME)-$(BOX_VERSION).box
	$(eval BOX_SHA = $(shell shasum 'build/$(BOX_NAME)-$(BOX_VERSION).box' | awk '{print $$1}'))
	@echo "Archive SHA: $(BOX_SHA)"
	@m4 \
		-DBOX_NS="$(BOX_NS)" \
		-DBOX_NAME="$(BOX_NAME)" \
		-DBOX_VERSION="$(BOX_VERSION)" \
		-DBOX_SHA="$(BOX_SHA)" \
		support/boxjson.m4 > build/substance-box-$(BOX_VERSION).json
  
upload:
	scp build/$(BOX_NAME)-$(BOX_VERSION).box developers:substance-registry/box/$(BOX_NS)/$(BOX_NAME)-$(BOX_VERSION).box
	scp build/$(BOX_NAME)-$(BOX_VERSION).json developers:substance-registry/box/$(BOX_NS)/$(BOX_NAME)-$(BOX_VERSION).json

clean:
	rm -rf build/*

.PHONY: all  export clean
