from pathlib import Path

import glob
import os
import re
import csv
import xml.etree.cElementTree as ET
from collections import defaultdict
from typing import Any

from ruamel.yaml import YAML

ALL_XML, XML_REGULAR = str('*.xml'),\
                       str('.*/(\S+).xml')

# NOTE: 
class Instruction():
    def __init__(self):
        self.mnemonic = str()
        self.ps_name = str()
        #
        self.mask = str()
        self.isa = str()
        #
        self.cond_setting = str()
        self.upd_nzcv = False
        self.instr_class = str()
        #
        self.illegal_vals = list()
        self.fields = list()
        #
        self.arch_vars = list()
        self.encs = list()
        #
    # def __setattr__(self, __name: str, __value : Any) -> None:
    #     # setattr(instr_data, attr, instr_attr.get("value"))
    #     if __name == "cond_setting":
    #         if __value not in ['s', 'S']:
    #             return
    #         else:
    #             __value = True
    #     #
    #     setattr(self, __name, __value)
    #
    def __to_dict__(self):
    #
        fixed_mask = self.mask.replace('0', '1')
        fixed_mask = fixed_mask.replace('x', '0')
        fixed_mask = int(fixed_mask, 2)
        #
        fixed_value = self.mask.replace('x', '0')
        fixed_value = int(fixed_value, 2)
        #
        if self.upd_nzcv == False:
            return dict({                                \
                "mn" : self.mnemonic,                    \
                "ps_name" : self.ps_name,                \
            # NOTE: instr_class <=> ps_name
            #    "instr_class" : self.instr_class,        \
                "mask" : self.mask,                      \
                "fixed_mask" : fixed_mask,               \
                "fixed_value" : fixed_value,             \
                "illegal_vals" : self.illegal_vals,      \
                "fields" : self.fields,                  \
                "encodings" : self.encs                  \
            })
        else:
            return dict({                                \
                "mn" : self.mnemonic,                    \
                "ps_name" : self.ps_name,                \
            # NOTE: instr_class <=> ps_name
            #    "instr_class" : self.instr_class,        \
                "upd_NZCVflags" : self.upd_nzcv,         \
                "mask" : self.mask,                      \
                "fixed_mask" : fixed_mask,               \
                "fixed_value" : fixed_value,             \
                "illegal_vals" : self.illegal_vals,      \
                "fields" : self.fields,                  \
                "encodings" : self.encs                  \
            })
            

    #
#
class Operand():
    def __init__(self, name : str, descr : str):
        self.name = name
        self.descr = descr
    #
#
class Encoding():
    def __init__(self, conds : list, asm_str, operands : list):
        self.conds = conds
        self.asm_str = asm_str
        self.ops = list()
        #
        for op in operands:
            self.ops.append(op.__dict__)
    #
#
class Field():
    def __init__(self, name : str, msb : int, lsb : int) -> None:
        self.name = name
        self.msb = msb
        self.lsb = lsb
    #
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
        self.instructions = list()
        #
        self.not_impl_attr = set()
        #
        self.OR, self.AND = " || ", " && "
        self.EQ, self.NOT_EQ = " == ", " != " 
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
    #
        root = xml.getroot()
        instr_section = self.parse_instr_section(root.attrib)
        #
        if instr_section["is_instr"] == False:
            return

        for iclass in xml.findall('.//classes/iclass'):
            instr_data =  self.parse_instr_class(iclass)
            #   
            if instr_data != None:
                if instr_data.mnemonic == str():
                    # print(f"No mnemonic, only {instr_data.ps_name}")
                    instr_data.mnemonic = instr_section['id']
                #
                self.instructions.append(instr_data.__to_dict__()) 
            #
    #
    def parse_instr_section(self, instr_section):
        id, title = instr_section.get("id"), instr_section.get("title")
        is_instr = True if instr_section.get("type") == "instruction" \
                        else False

        return dict({"id" : id, "title" : title, "is_instr" : is_instr})
        #
    #
    def parse_instr_class(self, iclass) -> Instruction:
    #
        instr_data = Instruction()
        self.parse_class_attrs(iclass.find("docvars"), instr_data)
        #
        arch_vars = self.parse_arch_variant(iclass)

        if (arch_vars != None) and (arch_vars not in self.arch_vars):
            print() # return
        #
        self.parse_regdiagram(iclass.find('regdiagram'), instr_data)
        #
        for enc in iclass.findall('encoding'):
            self.parse_encoding(enc, instr_data)
        #
        return instr_data   
        #
    #
    def parse_class_attrs(self, attrs, instr_data : Instruction):
    #
        for instr_attr in attrs:
            attr = str(instr_attr.get("key"))
            attr = attr.replace("-", "_")
            #
            if hasattr(instr_data, attr):
                value = instr_attr.get("value")
                if attr == "cond_setting":
                    if value not in ['s', 'S']:
                        continue
                    else:
                        attr = "upd_nzcv"
                        value = True
                #
                setattr(instr_data, attr, value)
            else:
                self.not_impl_attr.add(attr)
            #
        #
    #
    def parse_regdiagram(self, regdiagram, instr_data : Instruction):
    #
        instr_data.ps_name = deslash(regdiagram.attrib.get('psname'))
        self.parse_bits_box(regdiagram, instr_data)
        #
    #
    def parse_encoding(self, encoding, instr_data : Instruction):
        bitdiffs = encoding.attrib.get("bitdiffs")
        conds = list()
        #
        if bitdiffs != None:
            conds = self.parse_cond(bitdiffs) 
        #
        asm_str, operands = self.parse_asm_template(encoding.find("asmtemplate"))
        instr_data.encs.append(Encoding(conds , asm_str, operands).__dict__)
        #
    #
    def parse_asm_template(self, asm_template):
    #
        asm_str, operands = str(), list()
        #
        for it in asm_template:
            asm_str += it.text
            hover = it.attrib.get("hover")

            if hover != str() and hover != None:
                operands.append(Operand(it.text, hover))
        #
        return asm_str, operands
        #
    #
    def parse_cond(self, cond : str):
        enc_cond = dict()
        #
        for it in cond.split(self.AND):
            cur_op = str()
            for op in list([self.EQ, self.NOT_EQ]):
                if it.find(op) != -1:
                    cur_op = op
            #
            (name, val) = it.split(cur_op)
            vals = list()
            #
            if 'x' not in val:
                if cur_op == self.NOT_EQ:
                    vals = not_equal(val)
                else:
                    vals = equal(val)
            else:
                vals = get_legal_vals(val)
            #
            enc_cond[name] = dict({"vals" : vals})
        #
        return enc_cond
        #
    #
    def parse_conds(self, conds : str):
        enc_conds = list()
        #
        for cond in conds.split(self.OR):
            enc_conds.append(self.parse_cond(cond))
        #
        return enc_conds
        #
    #
    def parse_bits_box(self, regdiagram, instr_data : Instruction):
    #   
        for box in regdiagram.findall('box'):
        #
            field_name, is_usename = box.attrib.get('name'), box.attrib.get('usename')
            is_usename = True if is_usename == '1' else False
            
            width, msb = int(box.attrib.get('width','1')), int(box.attrib['hibit'])
            lsb = msb - width + 1
            #
            for b_it in box:
            #
                cur_bits, cond = get_bits(b_it.text, width)
                #
                if cond == False:
                    instr_data.illegal_vals.append(dict({"msb" : msb, "lsb" : lsb, "value" : cur_bits}))
                    instr_data.mask += 'x' * width
                else:
                    instr_data.mask += cur_bits
            #
            if field_name != None and is_usename:
                field = Field(field_name, msb, lsb)
                instr_data.fields.append(field.__dict__)
        #
    #
    def parse_arch_variant(self, iclass):
    #
        cur_arch_var = None
        arch_vars = iclass.find("arch_variants")
        #
        if arch_vars != None:
            var = arch_vars[0]
            name, feature = var.attrib.get('name'), var.attrib.get('feature')
            cur_arch_var = dict({"name" : name, "feature" : feature})
            #
        #
        return cur_arch_var  
        #   
    #
    def parse_extensions_csv(self, path_to_csv : str):
    #
        features_list = list()
        with open(path_to_csv, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter = ',')
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
        aarch_data["instructions"] = self.instructions

        with open(path, 'w+') as file:
            yaml.dump(aarch_data, file)
        #
    #
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
        field_val, vals = bit_data[3:], list()
        #
        if 'x' in field_val:
            vals = get_legal_vals(field_val)
        else:
            vals = list([field_val])
        #
        return vals, False
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
def deslash(name : str) -> str:
    return name.replace("/instrs","").replace("/", "__").replace("-","_")
    #
#
def is_comma(text : str) -> bool:
    return ',' in text
    #
#
def not_equal(val : str) -> list:
    not_eq = list()
    width = len(val)
    val = int(val, 2)
    #
    for cur_val in range(ones(width)):
        not_eq.append(cur_val)
    return not_eq
    #
#
def equal(val : str) -> list:
    vals = list()
    #
    if '(' and ')' in val:
        vals.append(val[1:-1])
    else:
        vals.append(val)
    return vals
    #
#
def replace_bit(val : str, bit_num : int, bit_value : int) -> str:
    return val[:bit_num] + str(bit_value) + val[bit_num + 1:]
    #
#
def get_legal_vals(val : str) -> list:
    legal_vals = list()
    x_pos = val.find('x')
    #
    if x_pos != -1:
        val0, val1 =  replace_bit(val, x_pos, 0),\
                      replace_bit(val, x_pos, 1)
        
        legal_vals += get_legal_vals(val0)
        legal_vals += get_legal_vals(val1)
    #
    else:
        legal_vals.append(val)
    #
    return legal_vals
    