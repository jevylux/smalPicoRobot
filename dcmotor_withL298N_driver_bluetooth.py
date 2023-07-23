#
# dcmotor driver example with L298N driver
# example with 1 motor using pwm to set speed
# remove the jumpers for ENA and ENB to use pwm for speed control
# use a jystick to move around
# diagramm : dc_motor_l298n_joystick.png

# In order to use the bluetooth connection a uf2
# of micropython-firmware-pico-w-130623.uf2  or greated must be used !!
from machine import Pin, ADC, PWM  #importing PIN,ADC and PWM
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import time #importing time   
import utime 

# Create a Bluetooth Low Energy (BLE) object
ble = bluetooth.BLE()

# Create an instance of the BLESimplePeripheral class with the BLE object
sp = BLESimplePeripheral(ble)

ble_f = 0
ble_b = 0
ble_r = 0
ble_l = 0
# Define a callback function to handle received data
def on_rx(data):
    print("Data received: ", data)  # Print the received data
    strData = str((data), 16)
    
    print("String received: ", strData)
    global ble_f, ble_b, ble_r, ble_l
    ble_f = 0
    ble_b = 0
    ble_r = 0
    ble_l = 0
    # data convention :
    # speed from 0 to 9  ( 0x30-0x39)
    # forward : f (0x66) - backwards : b (0x62) - left : l (0x6c) - right: r (0x72) -stop : s (0x73)
    # example : slow forward : 0x66310d0a (b'f1\r\n') - fast forward 0x66390d0a ((b'f9\r\n')
    #           fast right : 0x72390d0a (b'r9\r\n')  - medium left 0x6c35 ((b'l5\r\n')
    command = strData[0]
    speed = strData[1]
    print("Function : ",command," Speed : ",speed) 
    if command == 'f':  # forward
        ble_f = int(speed)
    if command == 'b':  # backwards
        ble_b = int(speed)
    if command == 'l':  # left
        ble_l = int(speed)
    if command == 'r':  # right
        ble_r = int(speed)
    if command == 's': #stop
        ble_f = 0
        ble_b = 0
        ble_r = 0
        ble_l = 0
    # end of data handling

xAxis = ADC(Pin(27))
yAxis = ADC(Pin(26))
# Defining motor pins

#OUT1  and OUT2
In1=Pin(6,Pin.OUT)  #IN1`
In2=Pin(7,Pin.OUT)  #IN2
EN_A=PWM(Pin(8))




#OUT3  and OUT4
In3=Pin(4,Pin.OUT)  #IN3
In4=Pin(3,Pin.OUT)  #IN4
EN_B=PWM(Pin(2))

  
# Defining frequency for enable pins
EN_A.freq(1500)
EN_B.freq(1500)

bleMsg = ""

# Forward
def move_forward():
    In1.high()
    In2.low()
    In3.low()
    In4.high()
    
# Backward
def move_backward():
    In1.low()
    In2.high()
    In3.high()
    In4.low()
    
   
#Stop
def stop():
    In1.low()
    In2.low()
    In3.low()
    In4.low()

while True:
    time.sleep(0.1)
    # Joystick handler
    
    yValue = yAxis.read_u16()
    xValue = xAxis.read_u16()
    print("y value : ",yValue,"x Value : ", xValue)
    
    
    # if joystick idewl
    if yValue >= 32000 and yValue <= 34000 or xValue >= 32000 and xValue <= 34000:
    # bluetooth handler
    # get data  
        if sp.is_connected():  # Check if a BLE connection is established
            sp.on_write(on_rx)  # Set the callback function for data reception
        else :
            ble_f = 0
            ble_b = 0
            ble_r = 0
            ble_l = 0 
        # data has to be normalized to joystick moide :
        # yvalue >= 34000 =>> forward - yvalue <= 32000 ==>> backward
        # xvalue < 3100 == >> left - xvalue >=34000 == >> right       
        # simulate joystick value from bluetooth values
        if ble_f != 0:
            yValue = 20000 - (ble_f*1970)
        if ble_b != 0:
            yValue = 35000 + (ble_b*3000)
        if ble_r != 0:
            xValue = 40000 + (ble_r*2500)
        if ble_l != 0:
            xValue = 30000 - (ble_l*2970)
    else :
        ble_f = 0
        ble_b = 0
        ble_r = 0
        ble_l = 0 

    print("y value : ",yValue,"x Value : ", xValue)
    
    if yValue >= 32000 and yValue <= 34000 or xValue >= 32000 and xValue <= 34000:

        stop()
        ble_msg = "stop"
        

    
    
    if yValue >= 34000:
        duty_cycle = (((yValue-65535/2)/65535)*100)*2
        print("Move backward: Speed " + str(abs(duty_cycle)) + " %")
        duty_cycle = ((yValue/65535)*100)*650.2
        
        EN_A.duty_u16(int(duty_cycle))
        EN_B.duty_u16(int(duty_cycle))
        
        move_backward()
        bleMsg = "move_backward "+ str(duty_cycle)

        

    
    elif yValue <= 32000:
        duty_cycle = ((yValue-65535/2)/65535*100)*2
        print("Move Forward: Speed " + str(abs(duty_cycle)) + " %")
        duty_cycle = abs(duty_cycle)*650.2

        EN_A.duty_u16(int(duty_cycle))
        EN_B.duty_u16(int(duty_cycle))
        
        move_forward()
        bleMsg = "move_forward "str(duty_cycle)
       
    elif xValue < 31000:
        duty_cycle = (((xValue-65535)/65535)*100)
        print("Move Left: Speed " + str(abs(duty_cycle)) + " %")
        duty_cycle = abs((duty_cycle)*650.25)

        EN_B.duty_u16(0)
        EN_A.duty_u16(int(duty_cycle))
        
        move_forward()
        bleMsg = "move left "str(duty_cycle) 


    elif xValue > 34000:
        duty_cycle = ((xValue-65535/2)/65535*100)*2
        print("Move Right: Speed " + str(abs(duty_cycle)) + " %")
        duty_cycle = abs(duty_cycle)*650.2

        EN_B.duty_u16(int(duty_cycle))
        EN_A.duty_u16(0)
        
        move_forward()
        bleMsg = "move right "str(duty_cycle)
    
    if bleMsg != "":
        sp.send(msg)




    
    
    
    