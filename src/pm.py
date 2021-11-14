import adb
import miniprogress


# Backend method to run pm list packages with a few arguments
def get_packages(device, additional_args=''):
    return adb.shell(device, f'pm list packages {additional_args}')


# Get the paths to the APKs
def get_package_path(device, pkg_id):
    return adb.shell(device, f'pm path {pkg_id}')


# Turn a raw package list string into a list of package IDs
def parse_package_list(package_list):
    lines = package_list.split('\n')
    progress = miniprogress.MiniProgress(len(lines), 'Parsing a package list')
    pkg_ids = []
    for line in lines:
        progress.inc()
        progress.visual()

        pkg_id = line.replace('package:', '')
        pkg_ids.append(pkg_id)

    return pkg_ids


# Return packages from first that are missing from second
def diff_package_lists(first, second):
    progress = miniprogress.MiniProgress(len(first), 'Comparing two package lists')

    missing_pkg_ids = []
    for pkg_id in first:
        progress.inc()
        progress.visual()

        if pkg_id not in second:
            missing_pkg_ids.append(pkg_id)

    return missing_pkg_ids


# Get the path to the OBB for this package
def get_package_obb_path(device, pkg_id):
    obb_pkg_path = f'/storage/self/primary/Android/obb/{pkg_id}'
    if adb.exists(device, obb_pkg_path):
        if not adb.empty(device, obb_pkg_path):
            return obb_pkg_path
