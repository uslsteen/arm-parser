from pathlib import Path
from parser.parser import ArmParser
import argparse

def main():
    #
    parser = argparse.ArgumentParser(description="ARM parser - tool to get instruction data from xml sources")
    
    parser.add_argument('-dir', "--directory", type=str, help="Path to xml sources directory")
    parser.add_argument('--arch', type=str, default = ['A64'], help="Optional list of architecture")
    parser.add_argument('-v', "--version", type=str, default=[], help="Minor version of ISA set")
    #
    args = parser.parse_args()

    exec_path = Path.resolve(Path(__file__)).parent
    src_path = exec_path.joinpath(args.directory)
    #
    parser = ArmParser(Path(src_path), args.arch, args.arch, args.version)
    parser.collect()
    parser.parse()
    #

if __name__ == "__main__":
    main()