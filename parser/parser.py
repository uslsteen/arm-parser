from pathlib import Path

import glob
import os
import re
import csv
import xml.etree.cElementTree as ET
from collections import defaultdict

from ruamel.yaml import YAML

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
        self.fields = list()
        #
        self.arch_vars = list()
    #
    def __to_dict__(self):
        fixed_mask = self.mask.replace('0', '1')
        fixed_mask = fixed_mask.replace('x', '0')
        fixed_mask = int(fixed_mask, 2)

        fixed_value = self.mask.replace('x', '0')
        fixed_value = int(fixed_value, 2)

        return dict({                       \
            "mn" : self.mnemonic,           \
            "ps_name" : self.ps_name,       \
            "mask" : self.mask,             \
            "fixed_mask" : fixed_mask,     \
            "fixed_value" : fixed_value,    \
            "fields" : self.fields,         \
            "attr" : 0                      \
        })

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
            instr_data.arch_vars = self.parse_arch_variant(iclass)
            
            if instr_data.arch_vars not in self.arch_vars:
                print() # return

            encoding = iclass.find('regdiagram')
            
            instr_data.ps_name = deslash(encoding.attrib.get('psname'))
            #
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
        #
        for box in encoding.findall('box'):
            illegal_vals = list()
            field_name = box.attrib.get('name')
            width, msb = int(box.attrib.get('width','1')), int(box.attrib['hibit'])
            lsb = msb - width + 1
            #
            for b_it in box:
                cur_bits, cond = get_bits(b_it.text, width)
                
                if cond == False:
                    illegal_vals.append(cur_bits)
                    mask += 'x' * width
                else:
                    mask += cur_bits
            #
            if field_name != None:
                if illegal_vals != list():
                    fields.append(dict({"name" : field_name, "illegal_vals" : illegal_vals}))
                else:
                    fields.append(dict({"name" : field_name}))

                if self.instr_fields.get(field_name) == None:
                    self.instr_fields[field_name] = make_fields_data(msb, lsb)

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
    def to_yaml(self, path : Path):
        yaml = YAML()
        yaml.indent = 4

        aarch_data = dict()
        aarch_data["fields"] = self.instr_fields
        aarch_data["instructions"] = list_to_dict(self.insts_list)

        with open(path, 'w+') as file:
            yaml.dump(aarch_data, file)
        #
    #
#
def list_to_dict(list) -> dict:
    cur_dict = dict()
    #
    for ind, it in enumerate(list):
        cur_dict[ind] = it.__to_dict__()
    #
    return cur_dict

#
def get_bits(bit_data : str, width):
    #
    if bit_data in ['1', '0', 'x']:
        return bit_data, True
    elif bit_data == '(1)':
        return '1', True
    elif bit_data == '(0)':
        return '0', True
    elif bit_data != None and bit_data[0:2] == "!=":
        return bit_data[3:], False
    else:
        return 'x' * width, True  
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
    #
#
        