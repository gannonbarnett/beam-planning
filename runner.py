import os 
import sys
import glob
import timeit

# runs tests, stores output w/ commit hash in results.csv
def run_test(filename):
    os.system("python3 main.py " + filename + " | python3 evaluate.py " + filename)

def run_all_tests():
    input_filenames = glob.glob("./test_cases/*.txt").sorted()
    for filename in input_filenames: 
        print("testing " + str(filename))
        elapsed = timeit.timeit('run_test(\"' + filename + '\")', 'from __main__ import run_test', number=1)
        print(" Time :" + str(elapsed))

if __name__ == "__main__":
    # run_all_tests()
    run_test(sys.argv[1])

