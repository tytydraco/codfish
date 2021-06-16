import itertools
import sys
import adb
import log
import pm


def __migrate(receiving, giving, strict=False):
    log.dbg(f'Syncing to {receiving.name} from {giving.name}')
    missing_pkg_ids = pm.get_device_packages_diff(receiving, giving)
    if len(missing_pkg_ids) == 0:
        log.warn('No missing packages to sync')
    else:
        for pkg_id in missing_pkg_ids:
            log.dbg(f'Receiver missing: {pkg_id}')
        pm.migrate_packages(missing_pkg_ids, receiving, giving)

    if strict:
        excess_package_ids = pm.get_device_packages_excess(receiving, giving)
        if len(excess_package_ids) == 0:
            log.warn('No excess packages to remove')
        else:
            for pkg_id in excess_package_ids:
                log.dbg(f'[{receiving.name}] Receiver excess: {pkg_id}')
                adb.uninstall(pkg_id, receiving)


def find_device_given_transport_id(devices, transport_id):
    for device in devices:
        if device.transport_id == transport_id:
            return device


def do_abis_match(devices):
    # Use the first device as a baseline architecture and ensure all others match
    base_device = devices[0]
    base_device_abi = adb.abi(base_device)
    for device in devices[1:]:
        if adb.abi(device) != base_device_abi:
            return False
    return True


def assert_abis_match(devices):
    if not do_abis_match(devices):
        log.err('Device architectures do not all match')
        sys.exit(1)


def migrate_all(devices):
    assert_abis_match(devices)
    # Sync all devices with each other such that all package lists are identical
    device_combos = list(itertools.combinations(devices, 2))
    for device_pair in device_combos:
        __migrate(device_pair[0], device_pair[1])
        __migrate(device_pair[1], device_pair[0])


def migrate_with_receiver_and_giver(devices, receiver, giver, strict):
    receiver_device = find_device_given_transport_id(devices, receiver)
    giver_device = find_device_given_transport_id(devices, giver)
    if giver_device is None or receiver_device is None:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)
    assert_abis_match([receiver_device, giver_device])
    __migrate(receiver_device, giver_device, strict)


def migrate_with_giver(devices, giver, strict):
    assert_abis_match(devices)
    giver_device = find_device_given_transport_id(devices, giver)
    if giver_device is None:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)

    devices.remove(giver_device)
    for device in devices:
        __migrate(device, giver_device, strict)


def migrate_with_receiver(devices, receiver, strict):
    assert_abis_match(devices)
    receiver_device = find_device_given_transport_id(devices, receiver)
    if receiver_device is None:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)

    devices.remove(receiver_device)
    for device in devices:
        __migrate(receiver_device, device, strict)


def migrate(receiver=None, giver=None, strict=False):
    try:
        devices = adb.devices()
    except AttributeError:
        log.err('Failed to enumerate devices')
        sys.exit(1)

    if len(devices) < 2:
        log.err('Not enough devices connected; requires two or more')
        sys.exit(1)

    if receiver is not None and receiver == giver:
        log.err('The receiver cannot also be the giver')
        sys.exit(1)

    if receiver is None and giver is None:
        if strict:
            log.err('Receiver or giver must be explicitly set to use strict mode')
            sys.exit(1)
        migrate_all(devices)
    elif receiver is not None and giver is not None:
        migrate_with_receiver_and_giver(devices, receiver, giver, strict)
    elif receiver is not None:
        migrate_with_receiver(devices, receiver, strict)
    elif giver is not None:
        migrate_with_giver(devices, giver, strict)
