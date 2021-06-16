import itertools
import sys
import adb
import log
import pm


def __sync(receiving, giving):
    log.dbg(f'Syncing to {receiving.name} from {giving.name}')
    missing_pkg_ids = pm.get_device_packages_diff(receiving, giving)
    if len(missing_pkg_ids) == 0:
        log.warn('No missing packages to sync')
    else:
        for pkg_id in missing_pkg_ids:
            log.dbg(f'Receiver missing: {pkg_id}')
        pm.migrate_packages(missing_pkg_ids, receiving, giving)


def __trim(receiving, giving):
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
        __sync(device_pair[0], device_pair[1])
        __sync(device_pair[1], device_pair[0])


def migrate_with_receiver_and_giver(
        devices,
        receiver_transport_id,
        giver_transport_id,
        strict=False
):
    receiver = find_device_given_transport_id(devices, receiver_transport_id)
    giver = find_device_given_transport_id(devices, giver_transport_id)
    if giver is None or receiver is None:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)
    assert_abis_match([receiver, giver])
    __sync(receiver, giver)
    if strict:
        __trim(receiver, giver)


def migrate_with_giver(
        devices,
        giver_transport_id,
        strict=False
):
    assert_abis_match(devices)
    giver = find_device_given_transport_id(devices, giver_transport_id)
    if giver is None:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)

    devices.remove(giver)
    for device in devices:
        __sync(device, giver)
        if strict:
            __trim(device, giver)


def migrate_with_receiver(
        devices,
        receiver_transport_id,
        strict=False
):
    assert_abis_match(devices)
    receiver = find_device_given_transport_id(devices, receiver_transport_id)
    if receiver is None:
        log.err(f'The specified transport id does not match any device')
        sys.exit(1)

    devices.remove(receiver)
    for device in devices:
        __sync(receiver, device)
        if strict:
            __trim(receiver, device)
