# codfish
A python tool to sync packages between Android devices

# Details
APKs and OBBs are transferred to both devices to ensure each client has a copy of the same applications. Installed apps are installed via the Google Play Store, so they are able to be updated.

- Several devices supported (2, 3, 4, etc...)
- OBB transfer supported
- Architecture sanity checks
- Split APKs support
- Zero external dependencies
- Custom in-house progress bar library

# Usage
- Running without specifying a giver or a receiver will sync all devices with each other, such that all devices contain the same third-party packages.
- Specify a receiver device using `-r` or `--receiver`. The argument takes a transport id, which can be found using `adb devices -l`. In this case, the specified receiver will receive from all givers, such that the receiver contains the same third-party packages as all of the givers.
- Specify a giver device using `-g` or `--giver`. The argument takes a transport id, which can be found using `adb devices -l`. In this case, all receivers will only receive from the giver, such that all receivers contain the same third-party packages as the giver.
- Specify both a receiver and a giver for a one-way, two-device sync.
- Specify `-s` or `--strict` to remove packages that the receiver contains that the giver lacks. This option can only be used if a receiver or giver is specified.
- Specify `-d` or `--demo` to do a safe run of the program where no changes will be made. It is *highly* recommended to run this program with demo mode first to make sure the final result is desirable.

# How-to
1. Connect two or more Android devices to your computer
2. Ensure ADB is properly configured
3. Navigate to `src`
4. `python main.py`
