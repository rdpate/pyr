import pyr
def main(opts, args):
    import datetime, sys, re
    now = datetime.datetime.now()
    return pyr.interact(opts, args, locals())
