.PHONY: default clean force_clean
default: all

VERSION = A_profile-2022-09
XMLDIR = xml

A64_TAR=${XMLDIR}/ISA_A64_xml_${VERSION}.tar.gz
A64 = ${XMLDIR}/ISA_A64_xml_${VERSION}

TARFILES = ${A64_TAR}

${XMLDIR}:
	mkdir -p ${XMLDIR}

.PRECIOUS: ${XMLDIR}/%.tar.gz

${XMLDIR}/%.tar.gz: | ${XMLDIR}
	cd ${XMLDIR} && \
	wget https://developer.arm.com/-/media/developer/products/architecture/armv9-a-architecture/2022-09/$(@F)

define TARGET
$($T): $($T_TAR)
	cd ${XMLDIR} && \
	tar zxf $$(<F)
endef

ASLTARGETS=A64
$(foreach T,$(ASLTARGETS), $(eval $(TARGET)))

GET_DATA: ${A64}

parse:
	python3 main.py --directory ${A64} --arch_vars $(abspath extensions.csv) > collisions.out

all: GET_DATA parse

clean:
	rm -rf ${XMLDIR}