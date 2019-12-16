import datetime

def main(opts, args):
    print("{:%Y-%m-%d_%H:%M:%S}".format(datetime.datetime.utcnow()))

if __name__ == "__main__":
    main([], [])
