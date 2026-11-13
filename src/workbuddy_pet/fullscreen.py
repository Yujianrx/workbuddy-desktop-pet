"""Read only native fullscreen status; never inspect window titles or process arguments."""
import os


def covers_monitor(client,monitor,tolerance=2):
    return (client[2]>client[0] and client[3]>client[1]
            and all(abs(a-b)<=tolerance for a,b in zip(client,monitor)))


def fullscreen_active():
    """True: fullscreen; False: normal foreground; None: unavailable observation."""
    if os.name!='nt':return False
    import ctypes
    from ctypes import wintypes as w
    try:
        user=ctypes.WinDLL('user32',use_last_error=True)
        user.GetForegroundWindow.restype=w.HWND
        user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        user.IsWindowVisible.argtypes=[w.HWND];user.IsIconic.argtypes=[w.HWND]
        user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
        user.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
        user.ClientToScreen.argtypes=[w.HWND,ctypes.POINTER(w.POINT)]
        user.MonitorFromWindow.argtypes=[w.HWND,w.DWORD];user.MonitorFromWindow.restype=w.HMONITOR
        class Monitor(ctypes.Structure):
            _fields_=[('size',w.DWORD),('screen',w.RECT),('work',w.RECT),('flags',w.DWORD)]
        user.GetMonitorInfoW.argtypes=[w.HMONITOR,ctypes.POINTER(Monitor)]
        hwnd=user.GetForegroundWindow()
        if not hwnd:return None
        pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value==os.getpid():return False
        if not user.IsWindowVisible(hwnd) or user.IsIconic(hwnd):return False
        cls=ctypes.create_unicode_buffer(256)
        if not user.GetClassNameW(hwnd,cls,256):return None
        if cls.value in ('Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'):return False
        shell=ctypes.WinDLL('shell32');query=shell.SHQueryUserNotificationState
        query.argtypes=[ctypes.POINTER(ctypes.c_int)];query.restype=ctypes.c_long
        state=ctypes.c_int()
        if query(ctypes.byref(state))==0 and state.value in (3,4):return True
        rect=w.RECT();info=Monitor();info.size=ctypes.sizeof(info)
        monitor=user.MonitorFromWindow(hwnd,2)
        if not monitor or not user.GetMonitorInfoW(monitor,ctypes.byref(info)) or not user.GetClientRect(hwnd,ctypes.byref(rect)):return None
        origin=w.POINT(rect.left,rect.top);end=w.POINT(rect.right,rect.bottom)
        if not user.ClientToScreen(hwnd,ctypes.byref(origin)) or not user.ClientToScreen(hwnd,ctypes.byref(end)):return None
        screen=info.screen
        return covers_monitor((origin.x,origin.y,end.x,end.y),(screen.left,screen.top,screen.right,screen.bottom))
    except (OSError,AttributeError):return None
