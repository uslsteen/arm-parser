from pathlib import Path

import glob
import json
import os
import re
import string
import sys
import xml.etree.cElementTree as ET
from collections import defaultdict
from itertools import takewhile

from matplotlib import widgets

ALL_XML, XML_REGULAR = str('*.xml'),\
                       str('.*/(\S+).xml')

class Instruction:
    def __init__(self, name, encs, post, conditional, exec):
        self.name = name
        self.encs = encs
        self.post = post
        self.conditional = conditional
        self.exec = exec


class ArmParser():
    def __init__(self, path):
        self.path = path
        self.xml_list = list()
        #
        self.instr_fields = dict()
        self.instructions = dict()
        self.insts_list = list()
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
            instr_data = dict()
            enc_mask = str()
            #
            docvars = iclass.find("docvars")
            for doc_var in docvars:
                instr_data[doc_var.get("key")] = doc_var.get("value")

            encoding = iclass.find('regdiagram')
            ps_name = encoding.attrib.get('psname')
            fields = list()
            #
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
                    enc_mask += str(b_it.text) if b_it.text != None else "x" * width
            
            instr_data["mask"] = enc_mask
            instr_data["fields"] = fields
            instr_data["ps_name"] = ps_name

            self.insts_list.append(instr_data)
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