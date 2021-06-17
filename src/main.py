import adb
import log
import args
import migrate
import sys


if __name__ == '__main__':
    args.parse_args()
    if adb.sanity_check() is False:
        log.err('ADB binary cannot be located')
        sys.exit(1)

    try:
        devices = adb.get_devices()
    except AttributeError:
        log.err('Failed to enumerate devices')
        sys.exit(1)

    if len(devices) < 2:
        log.err('Not enough devices connected; requires two or more')
        sys.exit(1)

    receiver_transport_id = args.args.receiver
    giver_transport_id = args.args.giver
    strict = args.args.strict
    demo = args.args.demo

    _migrate = migrate.Migrate(
        devices,
        receiver_transport_id,
        giver_transport_id,
        strict,
        demo
    )

    if receiver_transport_id is not None and receiver_transport_id == giver_transport_id:
        log.err('The receiver cannot also be the giver')
        sys.exit(1)

    if receiver_transport_id is None and giver_transport_id is None:
        if strict:
            log.err('Receiver or giver must be explicitly set to use strict mode')
            sys.exit(1)
        _migrate.migrate_all()
    elif receiver_transport_id is not None and giver_transport_id is not None:
        _migrate.migrate_with_receiver_and_giver()
    elif receiver_transport_id is not None:
        _migrate.migrate_with_receiver()
    elif giver_transport_id is not None:
        _migrate.migrate_with_giver()

    log.dbg('Done')
