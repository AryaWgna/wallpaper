import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32
user32.GetClassNameW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_uint]
user32.GetWindow.restype = ctypes.wintypes.HWND

def get_class(h):
    if not h: return ""
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, b, 256)
    return b.value

@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
def cb(hwnd, lp):
    c = get_class(hwnd)
    if c in ('WorkerW', 'Progman'):
        print(f'{c}: {hwnd} (Visible: {user32.IsWindowVisible(hwnd)})')
        
        # Enumerate direct children properly
        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def child_cb(child_hwnd, lp):
            cc = get_class(child_hwnd)
            print(f'  Child: {cc} ({child_hwnd}) (Visible: {user32.IsWindowVisible(child_hwnd)})')
            return True
        user32.EnumChildWindows(hwnd, child_cb, 0)
    return True

user32.EnumWindows(cb, 0)
