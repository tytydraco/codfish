import adb
import log
import args
import migrate
import itertools
import sys


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
def assert_transport_ids(receiver_transport_id, giver_transport_id):
    if receiver_transport_id is not None and receiver_transport_id == giver_transport_id:
        log.err('The receiver cannot also be the giver')
        sys.exit(1)


# Sync all devices with each other (implicit givers and receivers)
def migrate_all(devices, demo):
    assert_all_abis_match(devices)
    # Sync all devices with each other such that all package lists are identical
    device_combos = list(itertools.combinations(devices, 2))
    for device_pair in device_combos:
        migrate.migrate(device_pair[0], device_pair[1], demo=demo)
        migrate.migrate(device_pair[1], device_pair[0], demo=demo)


# Sync two devices with each other (explicit giver and receiver)
def migrate_with_receiver_and_giver(receiver, giver, strict, demo):
    assert_devices_exist(receiver, giver)
    assert_all_abis_match([receiver, giver])
    migrate.migrate(receiver, giver, strict, demo)


# Sync given one device as a receiver (others are implicitly givers)
def migrate_with_receiver(devices, receiver, strict, demo):
    assert_devices_exist(receiver)
    assert_all_abis_match(devices)
    _devices = devices
    _devices.remove(receiver)
    for device in _devices:
        migrate.migrate(receiver, device, strict, demo)


# Sync given one device as a giver (others are implicitly receivers)
def migrate_with_giver(devices, giver, strict, demo):
    assert_devices_exist(giver)
    assert_all_abis_match(devices)
    _devices = devices
    _devices.remove(giver)
    for device in _devices:
        migrate.migrate(device, giver, strict, demo)


def main():
    # Parse command line arguments to determine mode of operations
    _args = args.parse_args()
    receiver_transport_id = _args.receiver
    giver_transport_id = _args.giver
    strict = _args.strict
    demo = _args.demo

    # Do sanity checks
    assert_adb_exists()
    assert_transport_ids(receiver_transport_id, giver_transport_id)

    # Enumerate devices
    devices = assert_devices()

    # Assign receiver and giver if provided
    receiver = adb.find_device_given_transport_id(devices, receiver_transport_id)
    giver = adb.find_device_given_transport_id(devices, giver_transport_id)

    # User did not specify a receiver or giver
    if receiver_transport_id is None and giver_transport_id is None:
        if strict:
            log.err('Receiver or giver must be explicitly set to use strict mode')
            sys.exit(1)
        migrate_all(devices, demo)

    # User specified both a receiver and a giver
    elif receiver_transport_id is not None and giver_transport_id is not None:
        migrate_with_receiver_and_giver(receiver, giver, strict, demo)

    # User specified a receiver but not a giver
    elif receiver_transport_id is not None:
        migrate_with_receiver(devices, receiver, strict, demo)

    # User specified a giver but not a receiver
    elif giver_transport_id is not None:
        migrate_with_giver(devices, giver, strict, demo)

    log.dbg('Done')


if __name__ == '__main__':
    main()
