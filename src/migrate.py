import log
import pm
import adb
import sys
import itertools


def __migrate(receiving, giving, strict=False):
    log.dbg(f'[{giving.name}] -> [{receiving.name}] [STRICT: {strict}]')
    missing_pkg_ids = pm.get_device_packages_diff(receiving, giving)
    if len(missing_pkg_ids) == 0:
        log.warn('NO MISSING PACKAGES')
    else:
        for pkg_id in missing_pkg_ids:
            log.dbg(f'[{receiving.name}] NEEDS: {pkg_id}')
        pm.migrate_packages(missing_pkg_ids, receiving, giving)

    if strict:
        excess_package_ids = pm.get_device_packages_excess(receiving, giving)
        if len(excess_package_ids) == 0:
            log.warn('NO EXCESS PACKAGES')
        else:
            for pkg_id in excess_package_ids:
                log.dbg(f'[{receiving.name}] EXCESS: {pkg_id}')
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
        log.err('DEVICE ARCHITECTURE MISMATCH')
        sys.exit(1)


def migrate_all(devices):
    assert_abis_match(devices)
    # Sync all devices with each other such that all package lists are identical
    device_combos = list(itertools.combinations(devices, 2))
    for device_pair in device_combos:
        __migrate(device_pair[0], device_pair[1])
        __migrate(device_pair[1], device_pair[0])


def migrate_with_giver_and_receiver(devices, receiver, giver, strict):
    receiver_device = find_device_given_transport_id(devices, receiver)
    giver_device = find_device_given_transport_id(devices, giver)
    if giver_device is None or receiver_device is None:
        log.err(f'SPECIFIED TRANSPORT_ID DOES MATCH ANY DEVICE')
        sys.exit(1)
    assert_abis_match([receiver_device, giver_device])
    __migrate(receiver_device, giver_device, strict)


def migrate_with_giver(devices, giver, strict):
    assert_abis_match(devices)
    giver_device = find_device_given_transport_id(devices, giver)
    if giver_device is None:
        log.err(f'SPECIFIED TRANSPORT_ID DOES MATCH ANY DEVICE')
        sys.exit(1)

    # Sync all receivers with this giver
    devices.remove(giver_device)
    for device in devices:
        __migrate(device, giver_device, strict)


def migrate_with_receiver(devices, receiver, strict):
    assert_abis_match(devices)
    receiver_device = find_device_given_transport_id(devices, receiver)
    if receiver_device is None:
        log.err(f'SPECIFIED TRANSPORT_ID DOES MATCH ANY DEVICE')
        sys.exit(1)

    # Sync all receivers with this giver
    devices.remove(receiver_device)
    for device in devices:
        __migrate(receiver_device, device, strict)


def migrate(receiver=None, giver=None, strict=False):
    try:
        devices = adb.devices()
    except AttributeError:
        log.err('FAILED TO ENUMERATE DEVICES')
        sys.exit(1)

    if len(devices) < 2:
        log.err('TWO OR MORE DEVICES REQUIRED')
        sys.exit(1)

    if giver is not None and receiver == giver:
        log.err('GIVER CANNOT ALSO BE RECEIVER')
        sys.exit(1)

    if giver is None and receiver is None:
        if strict:
            log.err('GIVER OR RECEIVER MUST BE EXPLICIT FOR STRICT MODE')
            sys.exit(1)
        migrate_all(devices)
    elif giver is not None and receiver is not None:
        migrate_with_giver_and_receiver(devices, receiver, giver, strict)
    elif giver is not None:
        migrate_with_giver(devices, giver, strict)
    elif receiver is not None:
        migrate_with_receiver(devices, receiver, strict)
