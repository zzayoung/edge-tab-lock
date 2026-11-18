import ctypes as c
from ctypes import wintypes as w
import json
import os
import queue
import struct
import sys
import threading
from uuid import UUID

user = c.WinDLL('user32', use_last_error=True)
kernel = c.WinDLL('kernel32', use_last_error=True)
user.GetForegroundWindow.restype = w.HWND
user.SetThreadDpiAwarenessContext.argtypes = [c.c_void_p]
user.SetThreadDpiAwarenessContext.restype = c.c_void_p
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
kernel.OpenProcess.restype = w.HANDLE
kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
kernel.CloseHandle.argtypes = [w.HANDLE]
kernel.GetModuleHandleW.argtypes = [w.LPCWSTR]
kernel.GetModuleHandleW.restype = w.HMODULE
user.GetAsyncKeyState.argtypes = [c.c_int]
user.GetAsyncKeyState.restype = c.c_short
user.CallNextHookEx.argtypes = [w.HHOOK, c.c_int, w.WPARAM, w.LPARAM]
user.CallNextHookEx.restype = c.c_ssize_t
HOOK = c.WINFUNCTYPE(c.c_ssize_t, c.c_int, w.WPARAM, w.LPARAM)
user.SetWindowsHookExW.argtypes = [c.c_int, HOOK, w.HINSTANCE, w.DWORD]
user.SetWindowsHookExW.restype = w.HHOOK
user.UnhookWindowsHookEx.argtypes = [w.HHOOK]
user.PostThreadMessageW.argtypes = [w.DWORD, w.UINT, w.WPARAM, w.LPARAM]
kernel.GetCurrentThreadId.restype = w.DWORD
ole = c.OleDLL('ole32')
ole.CoCreateInstance.argtypes = [c.c_void_p, c.c_void_p, w.DWORD, c.c_void_p, c.c_void_p]
automation = c.WinDLL('oleaut32')
automation.SysFreeString.argtypes = [c.c_void_p]

protected = False
tabs = []
middle_press_blocked = False
thread_id = kernel.GetCurrentThreadId()
mouse_checks = queue.Queue(maxsize=1)


def com_call(obj, slot, result, args, *values):
    table = c.cast(obj, c.POINTER(c.POINTER(c.c_void_p))).contents
    return c.WINFUNCTYPE(result, c.c_void_p, *args)(table[slot])(obj, *values)


def com_get(obj, slot, output, *arguments):
    value = output()
    types, values = zip(*arguments) if arguments else ((), ())
    status = com_call(obj, slot, c.c_long, (*types, c.POINTER(output)), *values, c.byref(value))
    if status < 0:
        raise OSError(status)
    return value.value if hasattr(value, 'value') else value


def element_text(element, slot):
    value = com_get(element, slot, c.c_void_p)
    try:
        return c.wstring_at(value) if value else ''
    finally:
        automation.SysFreeString(value)


def release(obj):
    com_call(obj, 2, w.ULONG, ())


def title_matches(title, label):
    # Edge can append memory usage and other status text to accessible names.
    return bool(title) and (label == title or label.startswith(title + ' - '))


def check_mouse():
    # Match the physical screen coordinates reported by the low-level mouse hook.
    user.SetThreadDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    ole.CoInitializeEx(None, 0)
    clsid = c.create_string_buffer(UUID('ff48dba4-60ef-4201-aa87-54103eef594e').bytes_le)
    iid = c.create_string_buffer(UUID('30cbe57d-d9d0-452a-ab13-7ac5ac4825ee').bytes_le)
    uia = c.c_void_p()
    ole.CoCreateInstance(clsid, None, 1, iid, c.byref(uia))
    walker = com_get(uia, 16, c.c_void_p)  # RawViewWalker

    # VARIANT(VT_I4, UIA_TabItemControlTypeId) for the UIA_ControlTypePropertyId filter.
    class Variant(c.Structure):
        _fields_ = [('type', c.c_uint64), ('value', c.c_int64), ('padding', c.c_void_p)]

    condition = com_get(uia, 23, c.c_void_p, (c.c_int, 30003), (Variant, Variant(3, 50019)))
    while True:
        point, snapshot, response = mouse_checks.get()
        blocked = False
        elements = []
        try:
            element = com_get(uia, 7, c.c_void_p, (w.POINT, point))
            hit = None
            while element:
                elements.append(element)
                name = element_text(element, 30)  # CurrentClassName
                if name == 'EdgeTab':
                    hit = element
                if name == 'EdgeTabStrip' and hit:
                    label = element_text(hit, 23)  # CurrentName
                    candidates = [locked for title, locked in snapshot if title_matches(title, label)]
                    if len(candidates) == 1 and all(title for title, _ in snapshot):
                        blocked = candidates[0]
                        break

                    # Tabs with the same title need position and element identity.
                    items = com_get(element, 6, c.c_void_p, (c.c_int, 4), (c.c_void_p, condition))
                    elements.append(items)
                    if com_get(items, 3, c.c_int) != len(snapshot):
                        break
                    for index, (title, locked) in enumerate(snapshot):
                        item = com_get(items, 4, c.c_void_p, (c.c_int, index))
                        elements.append(item)
                        if title and not title_matches(title, element_text(item, 23)):
                            blocked = False
                            break
                        if locked and com_get(uia, 3, w.BOOL, (c.c_void_p, item), (c.c_void_p, hit)):
                            blocked = True
                    break
                if name in ('Chrome_RenderWidgetHostHWND', 'RootView'):
                    break
                element = com_get(walker, 3, c.c_void_p, (c.c_void_p, element))
        except OSError:
            blocked = False
        finally:
            for element in reversed(elements):
                release(element)
            response.put(blocked)


def foreground_edge():
    pid = w.DWORD()
    user.GetWindowThreadProcessId(user.GetForegroundWindow(), c.byref(pid))
    process = kernel.OpenProcess(0x1000, False, pid.value)
    if not process:
        return False
    path = c.create_unicode_buffer(32768)
    size = w.DWORD(len(path))
    ok = kernel.QueryFullProcessImageNameW(process, 0, path, c.byref(size))
    kernel.CloseHandle(process)
    return ok and os.path.basename(path.value).lower() == 'msedge.exe'

def receive():
    global protected, tabs
    stream = sys.stdin.buffer
    while True:
        header = stream.read(4)
        if len(header) != 4:
            break
        length = struct.unpack('<I', header)[0]
        message = json.loads(stream.read(length))
        if 'protect' in message:
            protected = message['protect'] is True
        if 'tabs' in message:
            tabs = message['tabs']
    protected = False
    tabs = []
    user.PostThreadMessageW(thread_id, 0x0012, 0, 0)

@HOOK
def hook(code, message, ptr):
    if code == 0 and message in (0x0100, 0x0104) and protected:
        key = c.cast(ptr, c.POINTER(w.DWORD))[0]
        if key == 0x57 and user.GetAsyncKeyState(0x11) < 0 and foreground_edge():
            return 1
    return user.CallNextHookEx(None, code, message, ptr)


@HOOK
def mouse_hook(code, message, ptr):
    global middle_press_blocked
    if code == 0 and message == 0x0208:
        if middle_press_blocked:
            middle_press_blocked = False
            return 1
    snapshot = tabs
    if code == 0 and message == 0x0207 and any(locked for _, locked in snapshot) and foreground_edge():
        point = w.POINT.from_buffer_copy(c.string_at(ptr, c.sizeof(w.POINT)))
        response = queue.Queue(maxsize=1)
        try:
            mouse_checks.put_nowait((point, snapshot, response))
            if response.get(timeout=0.15):
                middle_press_blocked = True
                return 1
        except (queue.Full, queue.Empty):
            pass
    return user.CallNextHookEx(None, code, message, ptr)


handle = user.SetWindowsHookExW(13, hook, kernel.GetModuleHandleW(None), 0)
if not handle:
    raise c.WinError(c.get_last_error())
mouse_handle = user.SetWindowsHookExW(14, mouse_hook, kernel.GetModuleHandleW(None), 0)
if not mouse_handle:
    raise c.WinError(c.get_last_error())
threading.Thread(target=check_mouse, daemon=True).start()
message = json.dumps({'ready': True}).encode()
sys.stdout.buffer.write(struct.pack('<I', len(message)) + message)
sys.stdout.buffer.flush()
threading.Thread(target=receive, daemon=True).start()
msg = w.MSG()
while user.GetMessageW(c.byref(msg), None, 0, 0) > 0:
    user.TranslateMessage(c.byref(msg))
    user.DispatchMessageW(c.byref(msg))
user.UnhookWindowsHookEx(handle)
user.UnhookWindowsHookEx(mouse_handle)
