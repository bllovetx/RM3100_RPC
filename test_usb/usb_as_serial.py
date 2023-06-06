import serial
ser = serial.Serial('/dev/ttyACM1', 38400, timeout=1)
ser.write(b'test')
print(ser.read(4))
ser.close()