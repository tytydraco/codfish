import adb
import pm
import log
import itertools
import sys


def migrate(receiving, giving):
    log.dbg(f'MIGRATING: [{giving.name}] -> [{receiving.name}]')

    missing_pkg_ids = pm.get_device_packages_diff(receiving, giving)
    if len(missing_pkg_ids) == 0:
        log.warn('NOTHING TO DO')
    pm.migrate_packages(missing_pkg_ids, receiving, giving)


def migrate_all():
    devices = []
    try:
        devices = adb.devices()
    except AttributeError:
        log.err('FAILED TO ENUMERATE DEVICES')
        sys.exit(1)

    if len(devices) < 2:
        log.err('TWO OR MORE DEVICES REQUIRED')
        sys.exit(1)

    # Use the first device as a baseline architecture and ensure all others match
    base_device = devices[0]
    base_device_abi = adb.abi(base_device)
    for device in devices[1:]:
        if adb.abi(device) != base_device_abi:
            log.err('DEVICE ARCHITECTURE MISMATCH')
            sys.exit(1)

    # Sync all devices with each other such that all package lists are identical
    device_combos = list(itertools.combinations(devices, 2))
    for device_pair in device_combos:
        migrate(device_pair[0], device_pair[1])
        migrate(device_pair[1], device_pair[0])


if __name__ == '__main__':
    if adb.sanity_check() is False:
        log.err('ADB BINARY NOT FOUND')
        sys.exit(1)
    migrate_all()
