import os
import shlex
import struct
import platform
import subprocess

hasTermios = False
oldtty = None

try:
    import termios
    import tty
    hasTermios = True
except ImportError:
    hasTermios = False


def hasTermios():
    return hasTermios


def isTerminal(stream):
    return stream.isatty()


def saveTerminalAttrs(stream):
    global oldtty
    if stream.isatty():
        oldtty = termios.tcgetattr(stream)


def getSavedTerminalAttrs():
    return oldtty


def restoreTerminalAttrs(stream):
    global oldtty
    restoreAttrs = getSavedTerminalAttrs()
    if isTerminal(stream) and restoreAttrs:
        termios.tcsetattr(stream, termios.TCSADRAIN, restoreAttrs)


def setTerminalInteractive(stream):
    if stream.isatty():
        tty.setraw(stream.fileno())
        tty.setcbreak(stream.fileno())


# from jtriley/terminalsize.py
def getTerminalSize():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _getTerminalSizeWindows()
        if tuple_xy is None:
            tuple_xy = _getTerminalSizeTPUT()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _getTerminalSizeLinux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy


def _getTerminalSizeWindows():
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass


def _getTerminalSizeTPUT():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass


def _getTerminalSizeLinux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])


def decodeTerminalBytes(bytes):
    return bytes.decode(errors='ignore')


if __name__ == "__main__":
    sizex, sizey = getTerminalSize()
    print('width =', sizex, 'height =', sizey)
