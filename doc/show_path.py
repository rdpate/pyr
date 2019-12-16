import sys

def main(opts, args):
    for n, x in enumerate(sys.path):
        print("{:3d} {}".format(n, x))

if __name__ == "__main__":
    main([], [])
