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


# Get a new package list of everything that the receiver is missing
def get_device_packages_diff(receiving, giving):
    log.dbg(f'[{receiving.name}] BUILDING PACKAGE LIST')
    receiving_pkg_ids = parse_package_list(get_all_packages(receiving))
    log.dbg(f'[{giving.name}] BUILDING PACKAGE LIST')
    giving_pkg_ids = parse_package_list(get_third_party_packages(giving))

    # Map package IDs to their APK(s) location
    missing_pkg_ids = []
    for pkg_id in giving_pkg_ids:
        if pkg_id not in receiving_pkg_ids:
            log.dbg(f'[{receiving.name}] NEEDS: {pkg_id}')
            missing_pkg_ids.append(pkg_id)

    return missing_pkg_ids


# Return all Android/obb paths found on the system
def get_obb_paths(device):
    return adb.shell('find -L /storage -path \'*/Android/obb\' -type d 2> /dev/null', device) \
        .strip() \
        .split('\n')


# Get the path to the OBB for this package
def get_obb_path(pkg_id, device):
    obb_paths = get_obb_paths(device)
    if obb_paths == "":
        return

    # Search all available OBB locations for the first non-empty directory
    for obb_path in obb_paths:
        obb_pkg_path = f'{obb_path}/{pkg_id}'
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

        # Check if we are installing a single APK or a split APK
        if len(paths) == 1:
            temp_apk = f'{tempdir}/temp.apk'
            log.dbg(f'[{giving.name}] PULLING: {pkg_id}')
            adb.pull(paths[0], temp_apk, giving)
            log.dbg(f'[{receiving.name}] PUSHING: {pkg_id}')
            adb.install(temp_apk, receiving)
            os.remove(temp_apk)
        else:
            apk_part = 0
            apk_parts = []
            for path in paths:
                temp_apk = f'{tempdir}/temp.{apk_part}.apk'
                log.dbg(f'[{giving.name}] PULLING: {pkg_id} [PART: {apk_part}]')
                adb.pull(path, temp_apk, giving)
                apk_parts.append(temp_apk)
                apk_part += 1
            log.dbg(f'[{receiving.name}] PUSHING: {pkg_id} [PARTS: {len(paths)}]')
            adb.install_multiple(apk_parts, receiving)
            for apk in apk_parts:
                os.remove(apk)
        # Push OBB
        # TODO: Handle OBB on external storage
        obb_path = get_obb_path(pkg_id, giving)
        if obb_path is not None:
            temp_obb = f'{tempdir}/obb'
            log.dbg(f'[{giving.name}] PULLING: {pkg_id} [PART: OBB]')
            adb.pull(obb_path, temp_obb, giving)
            log.dbg(f'[{receiving.name}] PUSHING: {pkg_id} [PART: OBB]')
            adb.push(temp_obb, f'/sdcard/Android/obb/{pkg_id}', receiving)
            shutil.rmtree(temp_obb)
    adb.reset_apk_verification(receiving)
