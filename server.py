from sipyco.pc_rpc import simple_server_loop
from queue import Queue
import threading
import usb.core
import usb.util
import time

rw_timeout = 100 # ms
read_interval = 0.02 # s
w_end = 0x2
r_end = 0x82
## transfer
msg_read = b'\x80'
msg_is_of = b'\x81'
msg_clear_of = b'\x82'
msg_clear_buffer = b'\x83'


class Rm3100Server:
    def __init__(self) -> None:
        # this is id code set on stm32
        self._dev = usb.core.find(idVendor=0x16c0, idProduct=0x27dd)
        # avoid busy
        if self._dev.is_kernel_driver_active(1):
            try:
                self._dev.detach_kernel_driver(1)
            except usb.core.USBError as e:
                print("Could not detatch kernel driver from interface({0}): {1}".format(1, str(e)))
                # TODO: raise
        # init usb connect
        self._dev.set_configuration()
        # init data queue
        self._data = Queue()
        # init read thread
        self._watcher_thread = None
        self._watcher_stop: threading.Event = threading.Event()
        self._watcher_stop.set()
        # init device lock
        self._dev_lock: threading.Lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        print("Connecting...")
        self._is_overflow()
        print("Connected!")


    def close(self) -> None:
        self.stop_acquisition()
        usb.util.dispose_resources(self._dev)

    def _transfer(self, msg, ret):
        if not self._dev_lock.acquire(timeout=1): # sec
            assert False, "Failed to acquire lock"
            # TODO: raise lock exception
        try:
            self._dev.write(w_end, msg, rw_timeout)
            res = self._dev.read(r_end, ret, rw_timeout)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            # timeout
            # somehow first few transfer will be omitted, repeat try will fix this. This is supposed only happen during self._connect()
            print(e) 
            self._dev_lock.release()
            res = self._transfer(msg, ret)
            return res
            # TODO: timeout? raise transfer error?
        self._dev_lock.release()
        return res
    
    def _write(self, msg):
        assert False, "_write is not tested!"
        if not self._dev_lock.acquire(timeout=1): # sec
            assert False, "Failed to acquire lock"
            # TODO: raise lock exception
        try:
            self._dev.write(w_end, msg, rw_timeout)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            print(e)
            # TODO: timeout? raise write error?
        self._dev_lock.release()

    def _read_mag(self) -> bool:
        bytes = self._transfer(msg_read, 5)
        if bytes[0]:
            self._data.put_nowait(
                int.from_bytes(bytes[1:5], "big", True)
            )
        return bytes[0]
    
    def _is_overflow(self) -> bool:
        return self._transfer(msg_is_of, 1)
    
    def _clear_buffer(self) -> bool:
        return self._transfer(msg_clear_buffer, 1)

    def _clear_overflow(self) -> bool:
        return self._transfer(msg_clear_of, 1)

    def _watcher(self):
        # clear
        self._data.queue.clear()
        self._clear_buffer()
        self._clear_overflow()
        # loop read
        while not self._watcher_stop.wait(read_interval):
            self._read_mag()
        print("Warning: has overflow!" if self._is_overflow() else "no overflow")

    def start_acquisition(self):
        self._watcher_stop.clear()
        self._watcher_thread = threading.Thread(target=self._watcher, daemon=True)
        self._watcher_thread.start()

    def stop_acquisition(self):
        if not self._watcher_stop.is_set():
            self._watcher_stop.set()
            self._watcher_thread.join()
        else:
            print("already stopped")

    def hasDataN(self, n):
        return self._data.qsize() == n

    def getDataN(self, n):
        assert self.hasDataN(n), f"data size error {self._data.qsize()}"
        temp = [self._data.get_nowait() for i in range(n)]
        return temp

    def hasData(self):
        return not self._data.empty()
    
    def getData(self):
        temp = self._data.get_nowait()
        # print(temp)
        return temp

try:  
    rm3100_server = Rm3100Server()

    simple_server_loop(
        {"rm3100_server": rm3100_server},
        # TODO: "ip", "port"
        "192.168.50.81", 41103
    )
except Exception as e:
    rm3100_server.close()
    print(e)


