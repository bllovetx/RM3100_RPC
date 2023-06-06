import usb.core
import usb.util
import time
dev = usb.core.find(idVendor=0x16c0, idProduct=0x27dd)
if dev.is_kernel_driver_active(1):
    dev.detach_kernel_driver(1)
    # try:
    #     dev.detach_kernel_driver(1)
    # except usb.core.USBError as e:
    #     sys.exit("Could not detatch kernel driver from interface({0}): {1}".format(1, str(e)))

dev.set_configuration()
try:
    msg = b'\x80'
    while True:
        temp = dev.write(2, msg, 100)
        res = 0
        try: 
            res = dev.read(0x82, 5, 100)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            print("Great! Let's findout what cause", e)
        print(res)
        time.sleep(0.02)
except Exception as e:
    usb.util.dispose_resources(dev)
    print(e)
