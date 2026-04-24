import ctypes
import sys

if sys.platform == 'win32':
	ctypes.windll.kernel32.FreeConsole()