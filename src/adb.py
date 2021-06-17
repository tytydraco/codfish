from device import Device
import subprocess
import re


def sanity_check():
    try:
        subprocess.run('adb', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False


def __run(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout.strip()


def adb(device, command):
    return __run(f'adb -t {device.transport_id} {command}')


def get_devices():
    raw = __run('adb devices -l')
    lines = raw.split('\n')[1:]

    device_list = []
    for line in lines:
        if 'unauthorized' in line:
            print('[!] DEVICE UNAUTHORIZED')
            continue

        _device = Device()

        _device.id = re.search('^\\w+', line) \
            .group(0) \
            .replace('device:', '')

        _device.name = re.search('model:\\w+', line) \
            .group(0) \
            .replace('model:', '')

        _device.transport_id = int(
            re.search('transport_id:\\w+', line)
            .group(0)
            .replace('transport_id:', '')
        )

        device_list.append(_device)

    return device_list


def find_device_given_transport_id(devices, transport_id):
    for device in devices:
        if device.transport_id == transport_id:
            return device


def install(device, path):
    adb(device, f'install -t -i com.android.vending {path}')


def install_multiple(device, paths):
    adb(device, f'install-multiple -t -i com.android.vending {" ".join(paths)}')


def uninstall(device, pkg_id):
    adb(device, f'uninstall {pkg_id}')


def disable_apk_verification(device):
    shell(device, 'settings put global verifier_verify_adb_installs 0')


def reset_apk_verification(device):
    shell(device, 'settings delete global verifier_verify_adb_installs')


def pull(device, path, name):
    output = adb(device, f'pull "{path}" "{name}"')

    # Detect if we failed to pull due to a permission error
    # If so, try copying the file to a permissible location first
    if 'Permission denied' in output:
        shell(device, f'cp -r "{path}" /data/local/tmp/safe_pull')
        adb(device, f'pull /data/local/tmp/safe_pull "{name}"')
        shell(device, f'rm -rf /data/local/tmp/safe_pull')


def push(device, name, path):
    adb(device, f'push "{name}" "{path}"')


def exists(device, path):
    return shell(device, f'[[ -e "{path}" ]] && echo 1') == '1'


def empty(device, path):
    return shell(device, f'[[ -z "$(ls -A "{path}")" ]] && echo 1') == '1'


def abi(device):
    return shell(device, 'getprop ro.product.cpu.abi')


def shell(device, command):
    return adb(device, f'shell "{command}"')
