import argparse

args = None


# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--giver', type=int, metavar='TRANSPORT_ID', help='''
        Choose a device to be a dedicated "giving" device.
        Instead of syncing devices with each other,
        receivers will only sync with the giver.
        The giver will not receive anything.
        TRANSPORT_ID can be found using "adb devices -l".
    ''')
    parser.add_argument('-r', '--receiver', type=int, metavar='TRANSPORT_ID', help='''
        Choose a device to be a dedicated "receiver" device.
        Instead of syncing devices with each other,
        givers will only sync with the receiver.
        The receiver will not give anything.
        TRANSPORT_ID can be found using "adb devices -l".
    ''')
    parser.add_argument('-s', '--strict', action='store_true', help='''
        Uninstall packages that the receiver lacks from the giver.
        Requires --giver or --receiver to be specified.
    ''')
    parser.add_argument('-d', '--demo', action='store_true', help='''
        Simulate the program; do not make any changes
    ''')

    global args
    args = parser.parse_args()
