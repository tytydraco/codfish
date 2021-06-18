import adb
import log
import pm


# Helper method to sync and trim
def migrate(receiving, giving, trim=False, demo=False):
    sync(receiving, giving, demo)
    if trim:
        trim(receiving, giving, demo)


# Sync packages from giver to receiver
def sync(receiving, giving, demo=False):
    log.dbg(f'Syncing to {receiving.name} from {giving.name}')

    receiving_pkg_ids = pm.parse_package_list(pm.get_packages(receiving))
    giving_pkg_ids = pm.parse_package_list(pm.get_packages(giving, '-3'))
    missing_pkg_ids = pm.diff_package_lists(giving_pkg_ids, receiving_pkg_ids)

    if len(missing_pkg_ids) == 0:
        log.warn('No missing packages to sync')
    else:
        for pkg_id in missing_pkg_ids:
            log.dbg(f'Receiver missing: {pkg_id}')
        if not demo:
            pm.migrate_packages(receiving, giving, missing_pkg_ids)


# Trim excess packages from receiver that giver lacks
def trim(receiving, giving, demo=False):
    receiving_pkg_ids = pm.parse_package_list(pm.get_packages(receiving, '-3'))
    giving_pkg_ids = pm.parse_package_list(pm.get_packages(giving))
    excess_package_ids = pm.diff_package_lists(receiving_pkg_ids, giving_pkg_ids)

    if len(excess_package_ids) == 0:
        log.warn('No excess packages to remove')
    else:
        for pkg_id in excess_package_ids:
            log.dbg(f'[{receiving.name}] Receiver excess: {pkg_id}')
            if not demo:
                adb.uninstall(receiving, pkg_id)
