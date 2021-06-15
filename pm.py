import os
import shutil
import tempfile
import adb
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


# Turn a package list into a map of package IDs and APK paths
def package_map(package_list, device):
    lines = package_list \
        .strip() \
        .split('\n')

    progress = miniprogress.MiniProgress(len(lines))

    paths = []
    pkg_ids = []
    for line in lines:
        progress.inc()
        progress.visual()

        pkg_id = line.replace('package:', '')
        pkg_ids.append(pkg_id)

        path = get_package_path(pkg_id, device).replace('package:', '').strip()
        paths.append(path.split('\n'))

    return dict(zip(pkg_ids, paths))


# Get a new package map of everything that the receiver is missing
def get_device_packages_diff(receiving, giving):
    print(f'[{receiving.name}] BUILDING PACKAGE LIST')
    receiving_packages = package_map(get_all_packages(receiving), receiving)
    print(f'[{giving.name}] BUILDING PACKAGE LIST')
    giving_packages = package_map(get_third_party_packages(giving), giving)

    map_missing = {}
    for pkg_id in giving_packages:
        if pkg_id not in receiving_packages.keys():
            map_missing[pkg_id] = giving_packages[pkg_id]
            print(f'[{receiving.name}] NEEDS: {pkg_id} [PARTS: {len(map_missing[pkg_id])}]')

    return map_missing


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
def migrate_packages(map_missing, receiving, giving):
    # Allow unverified APKs to be installed temporarily
    adb.disable_apk_verification(receiving)
    for key in map_missing:
        # Check if we are installing a single APK or a split APK
        if len(map_missing[key]) == 1:
            temp_apk = f'{tempdir}/temp.apk'
            print(f'[{giving.name}] PULLING: {key}')
            adb.pull(map_missing[key][0], temp_apk, giving)
            print(f'[{receiving.name}] PUSHING: {key}')
            adb.install(temp_apk, receiving)
            os.remove(temp_apk)
        else:
            apk_part = 0
            apk_parts = []
            for package_path in map_missing[key]:
                temp_apk = f'{tempdir}/temp.{apk_part}.apk'
                print(f'[{giving.name}] PULLING: {key} [PART: {apk_part}]')
                adb.pull(package_path, temp_apk, giving)
                apk_parts.append(temp_apk)
                apk_part += 1
            print(f'[{receiving.name}] PUSHING: {key} [PARTS: {len(map_missing[key])}]')
            adb.install_multiple(apk_parts, receiving)
            for apk in apk_parts:
                os.remove(apk)
        # Push OBB
        # TODO: Handle OBB on external storage
        obb_path = get_obb_path(key, giving)
        if obb_path is not None:
            temp_obb = f'{tempdir}/obb'
            print(f'[{giving.name}] PULLING: {key} [PART: OBB]')
            adb.pull(obb_path, temp_obb, giving)
            print(f'[{receiving.name}] PUSHING: {key} [PART: OBB]')
            adb.push(temp_obb, f'/sdcard/Android/obb/{key}', receiving)
            shutil.rmtree(temp_obb)
    adb.reset_apk_verification(receiving)
