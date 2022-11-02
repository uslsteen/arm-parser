from pathlib import Path

import glob
import os
import re
import xml.etree.cElementTree as ET
from collections import defaultdict

ALL_XML, XML_REGULAR = str('*.xml'),\
                       str('.*/(\S+).xml')

# NOTE: 
class Instruction:
    def __init__(self):
        self.mnemonic = str()
        self.ps_name = str()
        #
        self.mask = str()
        self.isa = str()
        #
        self.cond_setting = str()
        self.instr_class = str()
        #
        self.encs = list()
        self.fields = list()
        #
    #

# NOTE: 
class ArmParser():
    def __init__(self, path : Path):
        self.path = path
        self.xml_list = list()
        #
        self.instr_fields = dict()
        self.instructions = dict()
        self.insts_list = list()
        #
        self.not_impl_attr = set()
        #
    #
    def collect(self):
        for inf in glob.glob(os.path.join(self.path, ALL_XML)):
            name = re.search(XML_REGULAR, inf).group(1)
            #
            if name == "onebigfile": continue
            xml = ET.parse(inf)
            #
            self.xml_list.append(xml)
        #
    #
    def parse(self):
        for xml in self.xml_list:
            self.read_data(xml)
        #
    #
    def read_data(self, xml):
        encs = list()

        for iclass in xml.findall('.//classes/iclass'):
            #
            instr_data = self.parse_instr_section(iclass)

            encoding = iclass.find('regdiagram')

            instr_data.ps_name = deslash(encoding.attrib.get('psname'))
            instr_data.mask, instr_data.fields = self.parse_bits_section(encoding)

            if instr_data.mnemonic != str():
                self.insts_list.append(instr_data)
            else:
                print(instr_data.ps_name)
            
            encs.append(instr_data)
            #
    #
    def parse_instr_section(self, iclass) -> Instruction:
    #
        instr_data = Instruction()

        docvars = iclass.find("docvars")
        for doc_var in docvars:
            attr = str(doc_var.get("key"))
            attr = attr.replace("-", "_")
            #
            if hasattr(instr_data, attr):
                setattr(instr_data, attr, doc_var.get("value"))
            else:
                self.not_impl_attr.add(attr)
            #
        return instr_data   
    #
    def parse_bits_section(self, encoding):
    #   
        fields, mask = list(), str()

        for box in encoding.findall('box'):
            field_name = box.attrib.get('name')
            width, msb = int(box.attrib.get('width','1')), int(box.attrib['hibit'])
            lsb = msb - width + 1
            #
            if field_name != None:
                fields.append(field_name)
                if self.instr_fields.get(field_name) == None:
                    self.instr_fields[field_name] = make_fields_data(msb, lsb)
            #
            for b_it in box:
                mask += set_bits(b_it.text, width)
        
        return mask, fields


def set_bits(bit : str, width) -> bool:
    #
    if bit in ['1', '0']:
        return bit
    elif bit == 'x':
        return 'x'
    elif bit == '(1)':
        return '1'
    elif bit == '(0)':
        return '0'
    else:
        return 'x' * width  
    #
#      
def ones(n) -> int:
    return (1 << n) - 1
    #
#
def get_mask(from_, to_) -> int:
    return ones(from_ - to_ + 1) << from_
    #
#
def make_fields_data(msb, lsb) -> dict:
    fld_mask = get_mask(msb, lsb)
    return dict({"bits" : dict({"msb" : msb, "lsb" : lsb}), "mask" : fld_mask, "hex_mask" : hex(fld_mask)})
    #
#
def deslash(name : str) -> str:
    return name.replace("/instrs","").replace("/", "_").replace("-","_")