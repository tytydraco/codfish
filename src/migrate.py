import itertools
import sys
import adb
import log
import pm


class Migrate:
    def __init__(
            self,
            devices,
            receiver_transport_id,
            giver_transport_id,
            strict=False,
            demo=False
    ):
        self.devices = devices
        self.receiver_transport_id = receiver_transport_id
        self.giver_transport_id = giver_transport_id
        self.strict = strict
        self.demo = demo

    def __sync(self, receiving, giving):
        log.dbg(f'Syncing to {receiving.name} from {giving.name}')
        missing_pkg_ids = pm.get_device_packages_diff(receiving, giving)
        if len(missing_pkg_ids) == 0:
            log.warn('No missing packages to sync')
        else:
            for pkg_id in missing_pkg_ids:
                log.dbg(f'Receiver missing: {pkg_id}')
            if not self.demo:
                pm.migrate_packages(missing_pkg_ids, receiving, giving)

    def __trim(self, receiving, giving):
        excess_package_ids = pm.get_device_packages_excess(receiving, giving)
        if len(excess_package_ids) == 0:
            log.warn('No excess packages to remove')
        else:
            for pkg_id in excess_package_ids:
                log.dbg(f'[{receiving.name}] Receiver excess: {pkg_id}')
                if not self.demo:
                    adb.uninstall(pkg_id, receiving)

    @staticmethod
    def do_abis_match(devices):
        # Use the first device as a baseline architecture and ensure all others match
        base_device = devices[0]
        base_device_abi = adb.abi(base_device)
        for device in devices[1:]:
            if adb.abi(device) != base_device_abi:
                return False
        return True

    def assert_abis_match(self, devices):
        if not self.do_abis_match(devices):
            log.err('Device architectures do not all match')
            sys.exit(1)

    def migrate_all(self):
        self.assert_abis_match(self.devices)
        # Sync all devices with each other such that all package lists are identical
        device_combos = list(itertools.combinations(self.devices, 2))
        for device_pair in device_combos:
            self.__sync(device_pair[0], device_pair[1])
            self.__sync(device_pair[1], device_pair[0])

    def migrate_with_receiver_and_giver(self):
        receiver = adb.find_device_given_transport_id(self.devices, self.receiver_transport_id)
        giver = adb.find_device_given_transport_id(self.devices, self.giver_transport_id)

        if giver is None or receiver is None:
            log.err(f'The specified transport id does not match any device')
            sys.exit(1)

        self.assert_abis_match([receiver, giver])
        self.__sync(receiver, giver)
        if self.strict:
            self.__trim(receiver, giver)

    def migrate_with_receiver(self):
        receiver = adb.find_device_given_transport_id(self.devices, self.receiver_transport_id)

        if receiver is None:
            log.err(f'The specified transport id does not match any device')
            sys.exit(1)

        self.assert_abis_match(self.devices)
        _devices = self.devices
        _devices.remove(receiver)
        for device in _devices:
            self.__sync(receiver, device)
            if self.strict:
                self.__trim(receiver, device)

    def migrate_with_giver(self):
        giver = adb.find_device_given_transport_id(self.devices, self.giver_transport_id)

        if giver is None:
            log.err(f'The specified transport id does not match any device')
            sys.exit(1)

        self.assert_abis_match(self.devices)
        _devices = self.devices
        _devices.remove(giver)
        for device in _devices:
            self.__sync(device, giver)
            if self.strict:
                self.__trim(device, giver)
