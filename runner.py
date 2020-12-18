import os 
import sys

# this file just alias for running tests

if __name__ == "__main__":
    input_filename = sys.argv[1]
    os.system("python3 main.py " + input_filename + " | python3 evaluate.py " + input_filename)
