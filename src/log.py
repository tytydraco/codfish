# Logs a non-error message
def dbg(text):
    print(f'\033[1;32;48m » {text}\033[1;37;0m')


# Logs a progress bar status (does not add newline)
def progress(text):
    print(f' \033[1;37;48m{text}\033[1;37;0m', end='\r')


# Logs a non-fatal error message
def warn(text):
    print(f'\033[1;33;48m ¤ {text}\033[1;37;0m')


# Logs a fatal error message
def err(text):
    print(f'\033[1;31;48m ■ {text}\033[1;37;0m')
