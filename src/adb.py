from device import Device
import subprocess
import re


# Check if the ADB binary exists on the system
def sanity_check():
    try:
        subprocess.run('adb', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False


# Run a subprocess command and return the string output
def run(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout.strip()


# Run an ADB command on a device
def adb(device, command):
    return run(f'adb -t {device.transport_id} {command}')


# Run an ADB shell command on the device
def shell(device, command):
    return adb(device, f'shell "{command}"')


# Return all connected devices
def get_devices():
    raw = run('adb devices -l')
    lines = raw.split('\n')[1:]

    device_list = []
    for line in lines:
        try:
            device = Device()
            device.id = re.search('^\\w+', line) \
                .group(0) \
                .replace('device:', '')

            device.name = re.search('model:\\w+', line) \
                .group(0) \
                .replace('model:', '')

            device.transport_id = int(
                re.search('transport_id:\\w+', line)
                .group(0)
                .replace('transport_id:', '')
            )
        except AttributeError:
            continue

        device_list.append(device)

    return device_list


# Search a list of devices for a specific transport id
def find_device_given_transport_id(devices, transport_id):
    for device in devices:
        if device.transport_id == transport_id:
            return device


# Install a package as if it was installed from the Play Store
def install(device, paths):
    if type(paths) == list:
        paths_string = ' '.join(paths)
        adb(device, f'install-multiple -t -i com.android.vending {paths_string}')
    else:
        adb(device, f'install -t -i com.android.vending {paths[0]}')


# Uninstall a specific device package
def uninstall(device, pkg_id):
    adb(device, f'uninstall {pkg_id}')


# Allow devices to install unsigned APKs
def bypass_apk_verification(device, mode):
    if mode:
        shell(device, 'settings put global verifier_verify_adb_installs 0')
    else:
        shell(device, 'settings delete global verifier_verify_adb_installs')


# Pull a package from the device
def pull(device, path, name):
    output = adb(device, f'pull "{path}" "{name}"')

    # Detect if we failed to pull due to a permission error
    # If so, try copying the file to a permissible location first
    if 'Permission denied' in output:
        shell(device, f'cp -r "{path}" /data/local/tmp/safe_pull')
        adb(device, f'pull /data/local/tmp/safe_pull "{name}"')
        shell(device, f'rm -rf /data/local/tmp/safe_pull')


# Push a file to the device
def push(device, name, path):
    adb(device, f'push "{name}" "{path}"')


# Check if a file or folder exists on the device
def exists(device, path):
    return shell(device, f'[[ -e "{path}" ]] && echo 1') == '1'


# Check if a directory is empty on the device
def empty(device, path):
    return shell(device, f'[[ -z "$(ls -A "{path}")" ]] && echo 1') == '1'


# Return the ABI used by the device
def abi(device):
    return shell(device, 'getprop ro.product.cpu.abi')
