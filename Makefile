.PHONY: default clean force_clean
default: all

VERSION = 00bet9
XMLDIR = xml

A64_TAR=${XMLDIR}/A64_v85A_ISA_xml_${VERSION}.tar.gz
A64 = ${XMLDIR}/ISA_v85A_A64_xml_${VERSION}

TARFILES = ${A64_TAR}


${XMLDIR}:
	mkdir -p ${XMLDIR}

.PRECIOUS: ${XMLDIR}/%.tar.gz

${XMLDIR}/%.tar.gz: | ${XMLDIR}
	cd ${XMLDIR} && \
	wget https://developer.arm.com/-/media/developer/products/architecture/armv8-a-architecture/$(@F)

define TARGET
$($T): $($T_TAR)
	cd ${XMLDIR} && \
	tar zxf $$(<F) && tar zxf $$(@F).tar.gz
endef

ASLTARGETS=A64
$(foreach T,$(ASLTARGETS), $(eval $(TARGET)))

GET_DATA: ${A64}

parse:
	python3 main.py

all: GET_DATA parse

clean:
	rm -rf ${ASLDIR} ${PARSEDIR}

force_clean: clean
	rm -rf ${XMLDIR}
