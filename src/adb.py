import device
import subprocess
import re


def sanity_check():
    try:
        subprocess.run('adb', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False


def __run(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout


def adb(command, device):
    return __run(f'adb -t {device.transport_id} {command}')


def get_devices():
    raw = __run('adb devices -l').strip()
    lines = raw.split('\n')[1:]

    device_list = []
    for line in lines:
        if 'unauthorized' in line:
            print('[!] DEVICE UNAUTHORIZED')
            continue

        _device = device.Device()

        _device.id = re.search('^\\w+', line) \
            .group(0) \
            .strip() \
            .replace('device:', '')

        _device.name = re.search('model:\\w+', line) \
            .group(0) \
            .strip() \
            .replace('model:', '')

        _device.transport_id = int(
            re.search('transport_id:\\w+', line)
            .group(0)
            .strip()
            .replace('transport_id:', '')
        )

        device_list.append(_device)

    return device_list


def find_device_given_transport_id(devices, transport_id):
    for device in devices:
        if device.transport_id == transport_id:
            return device


def install(path, device):
    adb(f'install -t -i com.android.vending {path}', device)


def install_multiple(paths, device):
    adb(f'install-multiple -t -i com.android.vending {" ".join(paths)}', device)


def uninstall(pkg_id, device):
    adb(f'uninstall {pkg_id}', device)


def disable_apk_verification(device):
    shell('settings put global verifier_verify_adb_installs 0', device)


def reset_apk_verification(device):
    shell('settings delete global verifier_verify_adb_installs', device)


def pull(path, name, device):
    output = adb(f'pull "{path}" "{name}"', device)

    # Detect if we failed to pull due to a permission error
    # If so, try copying the file to a permissible location first
    if 'Permission denied' in output:
        shell(f'cp -r "{path}" /data/local/tmp/safe_pull', device)
        adb(f'pull /data/local/tmp/safe_pull "{name}"', device)
        shell(f'rm -rf /data/local/tmp/safe_pull', device)


def push(name, path, device):
    adb(f'push "{name}" "{path}"', device)


def exists(path, device):
    return shell(f'[[ -e "{path}" ]] && echo 1', device).strip() == '1'


def empty(path, device):
    return shell(f'[[ -z "$(ls -A "{path}")" ]] && echo 1', device).strip() == '1'


def abi(device):
    return shell('getprop ro.product.cpu.abi', device)


def shell(command, device):
    return adb(f'shell "{command}"', device)
