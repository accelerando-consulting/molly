print("Jello World!")

import time

import board
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

print("scanning i2c")
i2c = board.I2C()

while not i2c.try_lock():
    pass
i2c_addrs = i2c.scan()
i2c.unlock()

i2c_sensors = []
for addr in i2c_addrs:
    if addr < 32: continue
    print("I2C device found at:",hex(addr))
    i2c_sensors.append({
        'addr': addr,
        #'device': adafruit_pcf8574.PCF8574(i2c_bus=i2c, addrress=addr),
        'state': 0,
    })
print("Sensor table is ", i2c_sensors)

print("creating keyboard")
kbd = Keyboard(usb_hid.devices)

def read_sensor(addr, bus=i2c):
    regs = bytearray(1)
    bus.readfrom_into(address=addr, buffer=regs)
    return regs[0]

def write_sensor(addr, value, bus=i2c):
    print("write_sensor({}, {})".format(hex(addr), hex(value)))
    regs = bytearray(1)
    regs[0] = value
    while not bus.try_lock():
        pass
    bus.writeto(addr, regs)
    bus.unlock()
    

def poll_sensors(bus=i2c, sensors=i2c_sensors):

    #print("lock bus", bus)
    while not bus.try_lock():
        pass
    
    for s in sensors:
        #print("poll sensor", s)
        b = read_sensor(s['addr'])
        if (b != s['state']):
            s['state']=b
            print("Device at {} has new state {}".format(s['addr'], hex(s['state'])))
                
    #print("release bus", bus)
    bus.unlock()

key_table = [
    [56, 0, False, Keycode.UP_ARROW],
]

def get_sensor(addr, sensors=i2c_sensors):
    for s in sensors:
        if s["addr"]==addr:
            return s
    return None

def is_pressed(bits, pos):
    return ((bits & (1<<(pos*2)))==0)

def scan_keys(bus=i2c, sensors=i2c_sensors, keys=key_table):
    for k in keys:
        (addr, pos ,pressed, code) = k
        #print("Examine key addr={} pos={} pressed={} code={}".format(addr,pos,pressed,code))
        s = get_sensor(addr)
        if s==None: continue
        state = s['state']
        
        if not pressed and is_pressed(state, pos):
            # press detected, light up the led and send a keystroke
            print("Keypress detected state=",hex(state))
            s['state'] &= ~(1<<(1+pos*2)) # led low (sinking current)
            s['state'] |= (1<<(0+pos*2)) # key high (input pullup)
            write_sensor(addr, s['state'])
            kbd.send(code)
            k[2]=True # pressed
        elif pressed and not is_pressed(state, pos):
            # release detected, turn off the LED
            print("Release detected state=",hex(state))
            s['state'] |= (1<<(1+pos*2)) # led high (not sinking current)
            s['state'] |= (1<<(0+pos*2)) # key high (input pullup)
            write_sensor(addr, s['state'])
            k[2]=False # released


print("scan loop")
while True:
    poll_sensors()
    scan_keys()
    time.sleep(0.1)
    




