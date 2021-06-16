def dbg(text):
    print(f'\033[1;32;48m » {text}\033[1;37;0m')


def progress(text):
    print(f' \033[1;37;48m{text}\033[1;37;0m', end='\r')


def warn(text):
    print(f'\033[1;33;48m ¤ {text}\033[1;37;0m')


def err(text):
    print(f'\033[1;31;48m ■ {text}\033[1;37;0m')
