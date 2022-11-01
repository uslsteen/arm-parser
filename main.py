from pathlib import Path
from parser.parser import ArmParser

def main():
    #
    parser = ArmParser(Path("/home/anton/code/arm-asl-parser/xml/ISA_v85A_A64_xml_00bet9"))
    parser.collect()
    parser.parse()
    #

if __name__ == "__main__":
    main()