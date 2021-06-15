import adb
import pm


def migrate(receiving, giving):
    print(f'[{giving.name}] -> [{receiving.name}]')

    map_missing = pm.get_device_packages_diff(receiving, giving)
    if len(map_missing) == 0:
        print('[!] NOTHING TO DO')
    pm.migrate_packages(map_missing, receiving, giving)


def migrate_both():
    devices = adb.devices()
    if len(devices) != 2:
        print('[!] TWO DEVICES REQUIRED')
        exit(1)
    if adb.abi(devices[0]) != adb.abi(devices[1]):
        print('[!] DEVICE ARCHITECTURE MISMATCH')
        exit(1)
    migrate(devices[0], devices[1])
    migrate(devices[1], devices[0])


if adb.sanity_check() is False:
    print('[!] ADB BINARY NOT FOUND')
    exit(1)

migrate_both()
