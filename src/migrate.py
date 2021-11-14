import adb
import log
import pm
import os
import shutil
import tempfile


class Migrate:
    def __init__(self, devices, trim=False, demo=False, exclude=None):
        self.devices = devices
        self.trim = trim
        self.demo = demo
        self.exclude = exclude

    # Helper method to sync and trim
    def migrate(self, receiving, giving):
        self.sync_missing(receiving, giving)
        if self.trim:
            self.trim_excess(receiving, giving)

    # Sync missing packages from giver to receiver
    def sync_missing(self, receiving, giving):
        log.dbg(f'Syncing to {receiving.name} from {giving.name}')

        receiving_pkg_ids = pm.parse_package_list(pm.get_packages(receiving))
        giving_pkg_ids = pm.parse_package_list(pm.get_packages(giving, '-3'))

        if self.exclude is not None:
            receiving_pkg_ids = [pkg_id for pkg_id in receiving_pkg_ids if pkg_id not in self.exclude]
            giving_pkg_ids = [pkg_id for pkg_id in giving_pkg_ids if pkg_id not in self.exclude]

        missing_pkg_ids = pm.diff_package_lists(giving_pkg_ids, receiving_pkg_ids)

        if len(missing_pkg_ids) == 0:
            log.warn('No missing packages to sync')
        else:
            for pkg_id in missing_pkg_ids:
                log.dbg(f'[{receiving.name}] Installing: {pkg_id}')
                if not self.demo:
                    self.sync_package(receiving, giving, pkg_id)
                    self.sync_obb(receiving, giving, pkg_id)

    # Syncs a package from the giver to the receiver
    def sync_package(self, receiving, giving, pkg_id):
        tempdir = tempfile.gettempdir()
        default_verify_status = adb.get_verify_adb_installs(receiving)
        adb.set_verify_adb_installs(receiving, False)

        # Find where package APKs live on the giving device
        paths = pm.get_package_path(giving, pkg_id).replace('package:', '').split('\n')

        # Check if we are installing a single APK or a split APK
        if len(paths) == 1:
            # Pull necessary APK
            temp_apk = f'{tempdir}/temp.apk'
            adb.pull(giving, paths[0], temp_apk)

            # Install said APK
            adb.install(receiving, temp_apk)

            # Clean up
            os.remove(temp_apk)
        else:
            # Pull necessary APKs
            apk_parts = []
            for i, path in enumerate(paths):
                temp_apk = f'{tempdir}/temp.{i}.apk'
                adb.pull(giving, path, temp_apk)
                apk_parts.append(temp_apk)

            # Install said APKs
            adb.install(receiving, apk_parts)

            # Clean up
            for apk in apk_parts:
                os.remove(apk)

        adb.set_verify_adb_installs(receiving, default_verify_status)

    # Syncs a single package's OBB from the giver to the receiver
    def sync_obb(self, receiving, giving, pkg_id):
        tempdir = tempfile.gettempdir()

        obb_path = pm.get_package_obb_path(giving, pkg_id)
        if obb_path is not None:
            temp_obb = f'{tempdir}/obb'
            adb.pull(giving, obb_path, temp_obb)
            adb.push(receiving, temp_obb, obb_path)
            shutil.rmtree(temp_obb)

    # Trim excess packages from receiver that giver lacks
    def trim_excess(self, receiving, giving):
        receiving_pkg_ids = pm.parse_package_list(pm.get_packages(receiving, '-3'))
        giving_pkg_ids = pm.parse_package_list(pm.get_packages(giving))

        if self.exclude is not None:
            receiving_pkg_ids = [pkg_id for pkg_id in receiving_pkg_ids if pkg_id not in self.exclude]
            giving_pkg_ids = [pkg_id for pkg_id in giving_pkg_ids if pkg_id not in self.exclude]

        excess_package_ids = pm.diff_package_lists(receiving_pkg_ids, giving_pkg_ids)

        if len(excess_package_ids) == 0:
            log.warn('No excess packages to remove')
        else:
            for pkg_id in excess_package_ids:
                log.dbg(f'[{receiving.name}] Excess: {pkg_id}')
                if not self.demo:
                    adb.uninstall(receiving, pkg_id)
