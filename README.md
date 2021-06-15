# codfish
A python tool to sync packages between two Android devices

# Details
APKs and OBBs are transferred to both devices to ensure each client has a copy of the same applications. Installed apps are installed via the Google Play Store, so they are able to be updated.

- Several devices supported (2, 3, 4, etc...)
- OBB transfer supported
- Architecture sanity checks
- Split APKs support
- Zero external dependencies
- Custom in-house progress bar library

# How-to
1. Connect two Android devices to your computer
2. Ensure ADB is properly configured both both the clients and the host
3. `python main.py`
