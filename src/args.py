import argparse

args = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--giver', type=int, metavar='TRANSPORT_ID', help='''
        Choose a device to be a dedicated "giving" device.
        Instead of syncing devices with each other,
        receivers will only sync with the giver.
        The giver will not receive anything.
        TRANSPORT_ID can be found using "adb devices -l".
    ''')

    global args
    args = parser.parse_args()
