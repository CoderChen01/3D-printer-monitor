import os
import subprocess

import configs


def check_network():
    fnull = open(os.devnull, 'w')
    retval = subprocess.call('ping ' + configs.PING_NETWORK + ' -n 2',
                             shell=True,
                             stdout=fnull,
                             stderr=fnull)
    fnull.close()
    return False if retval else True