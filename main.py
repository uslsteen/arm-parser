from pathlib import Path
from parser.parser import ArmParser
import argparse

def main():
    #
    parser = argparse.ArgumentParser(description="ARM parser - tool to get instruction data from xml sources")

    parser.add_argument('-dir', "--directory", type=str, help="Path to xml sources directory")
    # args = parser.parse_args()

    exec_path = Path.resolve(Path(__file__)).parent
    # xml_path = Path(args.dir)
    #
    parser = ArmParser(exec_path.joinpath("xml", "ISA_v85A_A64_xml_00bet9"))
    parser.collect()
    parser.parse()
    #

if __name__ == "__main__":
    main()