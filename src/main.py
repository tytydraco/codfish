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

    migrate.migrate(
        args.args.receiver,
        args.args.giver,
        args.args.strict
    )
