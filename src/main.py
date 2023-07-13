import sys
from kernel import Kernel

if __name__ == "__main__":
    kernel = Kernel(sys.argv[1])
    kernel.load()
    kernel.run()
    