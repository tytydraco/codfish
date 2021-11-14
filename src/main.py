import adb
import log
import args
import migrate
import itertools
import sys

_args = args.parse_args()
_migrate: migrate.Migrate

# Bail if ADB is missing
def assert_adb_exists():
    if adb.sanity_check() is False:
        log.err('ADB binary cannot be located')
        sys.exit(1)


# Bail if ABIs do not match
def assert_all_abis_match(devices):
    # Use the first device as a baseline architecture and ensure all others match
    base_device = devices[0]
    base_device_abi = adb.abi(base_device)
    for device in devices[1:]:
        if adb.abi(device) != base_device_abi:
            log.err('Device architectures do not all match')
            sys.exit(1)


# Bail if a device does not exist
def assert_devices_exist(*device):
    if None in device:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)


# Bail if devices cannot be enumerated, return them if they can be
def assert_devices():
    devices = adb.get_devices()

    if len(devices) < 2:
        log.err('Not enough devices connected; requires two or more')
        sys.exit(1)

    return devices


# Bail if user tried to use the receiver as the giver
def assert_transport_ids():
    if _args.receiver is not None and _args.receiver == _args.giver:
        log.err('The receiver cannot also be the giver')
        sys.exit(1)


# Sync all devices with each other (implicit givers and receivers)
def migrate_all(devices):
    assert_all_abis_match(devices)
    # Sync all devices with each other such that all package lists are identical
    device_combos = list(itertools.combinations(devices, 2))
    for device_pair in device_combos:
        _migrate.migrate(device_pair[0], device_pair[1])
        _migrate.migrate(device_pair[1], device_pair[0])


# Sync two devices with each other (explicit giver and receiver)
def migrate_with_receiver_and_giver(receiver, giver):
    assert_devices_exist(receiver, giver)
    assert_all_abis_match([receiver, giver])
    _migrate.migrate(receiver, giver)


# Sync given one device as a receiver (others are implicitly givers)
def migrate_with_receiver(devices, receiver):
    assert_devices_exist(receiver)
    assert_all_abis_match(devices)
    _devices = devices.copy()
    _devices.remove(receiver)
    for device in _devices:
        _migrate.migrate(receiver, device)


# Sync given one device as a giver (others are implicitly receivers)
def migrate_with_giver(devices, giver):
    assert_devices_exist(giver)
    assert_all_abis_match(devices)
    _devices = devices
    _devices.remove(giver)
    for device in _devices:
        _migrate.migrate(device, giver)


def main():
    global _migrate

    # Do sanity checks
    assert_adb_exists()
    assert_transport_ids()

    # Enumerate devices
    devices = assert_devices()

    _migrate = migrate.Migrate(devices, _args.strict, _args.demo, _args.exclude)

    # Assign receiver and giver if provided
    receiver = adb.find_device_given_transport_id(devices, _args.receiver)
    giver = adb.find_device_given_transport_id(devices, _args.giver)

    # User did not specify a receiver or giver
    if _args.receiver is None and _args.giver is None:
        if _args.strict:
            log.err('Receiver or giver must be explicitly set to use strict mode')
            sys.exit(1)
        migrate_all(devices)

    # User specified both a receiver and a giver
    elif _args.receiver is not None and _args.giver is not None:
        migrate_with_receiver_and_giver(receiver, giver)

    # User specified a receiver but not a giver
    elif _args.receiver is not None:
        migrate_with_receiver(devices, receiver)

    # User specified a giver but not a receiver
    elif _args.giver is not None:
        migrate_with_giver(devices, giver)

    log.dbg('Done')


if __name__ == '__main__':
    main()
