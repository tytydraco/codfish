import adb
import pm
import itertools


def migrate(receiving, giving):
    print(f'[{giving.name}] -> [{receiving.name}]')

    missing_pkg_ids = pm.get_device_packages_diff(receiving, giving)
    if len(missing_pkg_ids) == 0:
        print('[!] NOTHING TO DO')
    pm.migrate_packages(missing_pkg_ids, receiving, giving)


def migrate_all():
    devices = adb.devices()
    if len(devices) < 2:
        print('[!] TWO OR MORE DEVICES REQUIRED')
        exit(1)

    # Use the first device as a baseline architecture and ensure all others match
    base_device = devices[0]
    base_device_abi = adb.abi(base_device)
    for device in devices[1:]:
        if adb.abi(device) != base_device_abi:
            print('[!] DEVICE ARCHITECTURE MISMATCH')
            exit(1)

    # Sync all devices with each other such that all package lists are identical
    device_combos = list(itertools.combinations(devices, 2))
    for device_pair in device_combos:
        migrate(device_pair[0], device_pair[1])
        migrate(device_pair[1], device_pair[0])


if adb.sanity_check() is False:
    print('[!] ADB BINARY NOT FOUND')
    exit(1)

migrate_all()
