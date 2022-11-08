from pathlib import Path

import glob
import os
import re
import csv
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
        self.arch_vars = list()
    #

# NOTE: 
class ArmParser():
    def __init__(self, path : Path, args):
    #
        self.path = path
        self.arch = args.arch
        self.arch_vars = self.parse_extensions_csv(args.arch_vars)
        #
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
            self.parse_inst(xml)
        #
    #
    def parse_inst(self, xml):
        encs = list()

        for iclass in xml.findall('.//classes/iclass'):
            #
            instr_data = self.parse_instr_section(iclass)
            #
            instr_data.arch_vars = self.parse_arch_variant(iclass)
            if instr_data.arch_vars not in self.arch_vars:
                return

            encoding = iclass.find('regdiagram')
            
            instr_data.ps_name = deslash(encoding.attrib.get('psname'))
            instr_data.mask, instr_data.fields = self.parse_bits_section(encoding)

            if instr_data.mnemonic != str():
                self.insts_list.append(instr_data)
            else:
                print(f"No mnemonic only {instr_data.ps_name}")
            
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
        #
    #
    def parse_arch_variant(self, iclass):
    #
        cur_arch_var = dict()
        arch_vars = iclass.find("arch_variants")
        #
        if arch_vars != None:
            var = arch_vars[0]
            name, feature = var.attrib.get('name'), var.attrib.get('feature')
            cur_arch_var = dict({"name" : name, "feature" : feature})

        return cur_arch_var  
        #   
    #
    def parse_extensions_csv(self, path_to_csv : str):
    #
        features_list = list()
        with open(path_to_csv, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter = ' ')
            for row in spamreader:
                if len(row) == 2:
                    features_list.append(dict({"name" : row[0], "feature" : row[1]}))
                else:
                    features_list.append(dict({"feature" : row[0]}))
                #
            #
        return features_list
        #
    #
#
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