from device import Device
import subprocess
import re


def __run(command):
    return subprocess.run(command, capture_output=True, text=True).stdout


def adb(command, device):
    return __run(f'adb -t {device.transport_id} {command}')


def devices():
    raw = __run('adb devices -l').strip()
    lines = raw.split('\n')[1:]

    device_list = []
    for line in lines:
        device = Device()

        device.id = re.search('^\\w+', line) \
            .group(0) \
            .strip() \
            .replace('device:', '')

        device.name = re.search('model:\\w+', line) \
            .group(0) \
            .strip() \
            .replace('model:', '')

        device.transport_id = int(
            re.search('transport_id:\\w+', line)
            .group(0)
            .strip()
            .replace('transport_id:', '')
        )

        device_list.append(device)

    return device_list


def install(path, device):
    adb(f'install -t -i com.android.vending {path}', device)


def install_multiple(paths, device):
    adb(f'install-multiple -t -i com.android.vending {" ".join(paths)}', device)


def disable_apk_verification(device):
    shell('settings put global verifier_verify_adb_installs 0', device)


def reset_apk_verification(device):
    shell('settings delete global verifier_verify_adb_installs', device)


def pull(path, name, device):
    adb(f'pull "{path}" "{name}"', device)


def push(name, path, device):
    adb(f'push "{name}" "{path}"', device)


def exists(path, device):
    return shell(f'[[ -e "{path}" ]] && echo 1', device).strip() == '1'


def empty(path, device):
    return shell(f'[[ -z "$(ls -A "{path}")" ]] && echo 1', device).strip() == '1'


def shell(command, device):
    return adb(f'shell "{command}"', device)
