import os
import shutil
import tempfile
import adb
import log
import miniprogress

tempdir = tempfile.gettempdir()


# Get all packages installed by the user
def get_third_party_packages(device):
    return adb.shell('pm list packages -3', device)


# Get all packages, including system packages
def get_all_packages(device):
    return adb.shell('pm list packages', device)


# Get the paths to the APKs
def get_package_path(pkg_id, device):
    return adb.shell(f'pm path {pkg_id}', device)


# Turn a raw package list string into a list of package IDs
def parse_package_list(package_list):
    lines = package_list \
        .strip() \
        .split('\n')

    progress = miniprogress.MiniProgress(len(lines))

    pkg_ids = []
    for line in lines:
        progress.inc()
        progress.visual()

        pkg_id = line.replace('package:', '')
        pkg_ids.append(pkg_id)

    return pkg_ids


# Return packages from first that are missing from second
def diff_package_lists(first, second):
    progress = miniprogress.MiniProgress(len(second))

    missing_pkg_ids = []
    for pkg_id in first:
        progress.inc()
        progress.visual()
        if pkg_id not in second:
            missing_pkg_ids.append(pkg_id)

    return missing_pkg_ids


def get_device_packages_excess(receiving, giving):
    receiving_pkg_ids = parse_package_list(get_third_party_packages(receiving))
    giving_pkg_ids = parse_package_list(get_all_packages(giving))

    return diff_package_lists(receiving_pkg_ids, giving_pkg_ids)


# Get a new package list of everything that the receiver is missing
def get_device_packages_diff(receiving, giving):
    receiving_pkg_ids = parse_package_list(get_all_packages(receiving))
    giving_pkg_ids = parse_package_list(get_third_party_packages(giving))

    return diff_package_lists(giving_pkg_ids, receiving_pkg_ids)


# Get the path to the OBB for this package
def get_package_obb_path(pkg_id, device):
    obb_pkg_path = f'/storage/self/primary/Android/obb/{pkg_id}'
    if adb.exists(obb_pkg_path, device):
        if not adb.empty(obb_pkg_path, device):
            return obb_pkg_path


# Install packages from the giver to the receiver
def migrate_packages(missing_pkg_ids, receiving, giving):
    # Allow unverified APKs to be installed temporarily
    adb.disable_apk_verification(receiving)
    for pkg_id in missing_pkg_ids:
        # Find where package APKs live on the giving device
        paths = get_package_path(pkg_id, giving).replace('package:', '').strip().split('\n')

        log.dbg(f'Receiver installing: {pkg_id}')

        # Check if we are installing a single APK or a split APK
        if len(paths) == 1:
            temp_apk = f'{tempdir}/temp.apk'
            adb.pull(paths[0], temp_apk, giving)
            adb.install(temp_apk, receiving)
            os.remove(temp_apk)
        else:
            apk_part = 0
            apk_parts = []
            for path in paths:
                temp_apk = f'{tempdir}/temp.{apk_part}.apk'
                adb.pull(path, temp_apk, giving)
                apk_parts.append(temp_apk)
                apk_part += 1
            adb.install_multiple(apk_parts, receiving)
            for apk in apk_parts:
                os.remove(apk)
        # Push OBB if it exists
        obb_path = get_package_obb_path(pkg_id, giving)
        if obb_path is not None:
            log.dbg(f'Receiver getting OBB: {pkg_id}')
            temp_obb = f'{tempdir}/obb'
            adb.pull(obb_path, temp_obb, giving)
            adb.push(temp_obb, obb_path, receiving)
            shutil.rmtree(temp_obb)
    adb.reset_apk_verification(receiving)
