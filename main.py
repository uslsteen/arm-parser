from pathlib import Path
from parser.parser import Parser
import argparse

def main():
    #
    parser = argparse.ArgumentParser(description="ARM parser - tool to get instruction data from xml sources")
    
    parser.add_argument('-dir', "--directory", type=str, help="Path to xml sources directory")
    parser.add_argument('--arch', type=str, default = ['A64'], help="Optional list of architecture")
    parser.add_argument('--arch_vars', type=str, help="Path to file w/ legal ARM extensions")
    #
    args = parser.parse_args()
    #
    exec_path = Path.resolve(Path(__file__)).parent
    src_path = exec_path.joinpath(args.directory)
    #
    parser = Parser(Path(src_path), args)
    parser.collect()
    parser.parse()

    parser.to_yaml(Path("aarch64.yaml"))
    #

if __name__ == "__main__":
    main()