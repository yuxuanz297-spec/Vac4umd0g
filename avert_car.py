from pyb import Pin,Timer,micros
from math import pi,exp


py1=Pin('Y1',Pin.OUT_PP)
py2=Pin('Y2',Pin.OUT_PP)
py3=Pin('Y3',Pin.OUT_PP)
py4=Pin('Y4',Pin.OUT_PP)
py5=Pin('Y5',Pin.OUT_PP)
py6=Pin('Y6',Pin.OUT_PP)
py7=Pin('Y7',Pin.OUT_PP)
py8=Pin('Y8',Pin.OUT_PP)
px1=Pin('X1')
px2=Pin('X2')
px3=Pin('X3')
px4=Pin('X4')
# px19=Pin('X19',Pin.IN)
# px20=Pin('X20',Pin.IN)
# px21=Pin('X21',Pin.IN)
# px22=Pin('X22',Pin.IN)
tim=Timer(2,freq=13213)
tim1=Timer(3,freq=1000)


ir_pin=pyb.Pin('X5',pyb.Pin.IN)
# def measure_speed(a):
#     time=0
#     for i in range(20):
#         while a.value()!=1:
#             pass
#         while a.value()==1:
#             pass
#         start=pyb.micros()
#         while a.value()==1:
#             pass
#         while a.value()!=1:
#             pass
#         while a.value()==1:
#             pass
#         time1=pyb.elapsed_micros(start)
#         time=time+time1  
#     frequency=2*pi*10**6/time
#     return frequency*3.2
def measure_pulse(level,timeout=20000):
    start=pyb.micros()
    while ir_pin.value()!=level:
        if pyb.elapsed_micros(start)>timeout:return None
    pulse_start=pyb.micros()
    while ir_pin.value()==level:
        if pyb.elapsed_micros(pulse_start)>timeout:return None
    return pyb.elapsed_micros(pulse_start)
def decode_ir():
    pulse_len=measure_pulse(0)
    if pulse_len is None or not(8000<pulse_len<10000):return None
    pulse_len=measure_pulse(1)
    if pulse_len is None or not(4000<pulse_len<5000):return None
    data=0
    for i in range(32):
        pulse_len=measure_pulse(0)
        if pulse_len is None or not(500<pulse_len<600):return None
        pulse_len=measure_pulse(1)
        if pulse_len is None or (pulse_len>1000):
            data |=(1<<i)
        else:
            data |=(0<<i)
    return data


pwp1x=81.081
pwp2x=79.293
pwp3x=79.694
pwp4x=79.599
pwp1=0
pwp2=0
pwp3=0
pwp4=0

ch1=tim.channel(1,Timer.PWM,pin=px1)
ch2=tim.channel(2,Timer.PWM,pin=px2)
ch3=tim.channel(3,Timer.PWM,pin=px3)
ch4=tim.channel(4,Timer.PWM,pin=px4)

trig_left = Pin('X6', Pin.OUT_PP)   # 原来的，继续用
trig_middle  = Pin('X7', Pin.OUT_PP)   # 新增，X7 空闲（你原来 px7 是 PWM 输出，但可以另找）
trig_right   = Pin('X8', Pin.OUT_PP)
echo_right = Pin('Y9', Pin.IN)
echo_left = Pin('Y10', Pin.IN)
echo_middle = Pin('Y12', Pin.IN)
trig_middle.low()
trig_left.low()
trig_right.low()
pyb.delay(100)
last_ultrasonic_time = 0
# py1.high()
# py2.low()
# py3.low()
# py4.high()
# py5.high()
# py6.low()
# py7.low()
# py8.high()
last_ir_state = 1
while True:
    ch1.pulse_width_percent(pwp1)
    ch2.pulse_width_percent(pwp2)
    ch3.pulse_width_percent(pwp3)
    ch4.pulse_width_percent(pwp4)
    current_ir_state = ir_pin.value()
    if last_ir_state == 1 and current_ir_state == 0:
        code=decode_ir()
        if code is not None:
            print("IR Code:",hex(code))
            s=hex(code)
            if s[2:10]=='e916ff00':
                py1.high()
                py2.low()
                py3.low()
                py4.high()
                py5.high()
                py6.low()
                py7.low()
                py8.high()
            elif s[2:10]=='e619ff00':
                py1.low()
                py2.low()
                py3.low()
                py4.low()
                py5.low()
                py6.low()
                py7.low()
                py8.low()
    if micros() - last_ultrasonic_time > 200000:  # 每200ms测一次（而不是每循环都测）
        last_ultrasonic_time = micros()
        last_ir_state=current_ir_state
        trig_middle.high()
        pyb.udelay(10)
        trig_middle.low()
        while echo_middle.value() == 0: pass
        t_middle = micros()
        while echo_middle.value() == 1: pass
        duration_middle = micros() - t_middle
        distance_middle = duration_middle * 0.034 / 2
        trig_right.high()
        pyb.udelay(10)
        trig_right.low()
        while echo_right.value() == 0: pass
        t_right = micros()
        while echo_right.value() == 1: pass
        duration_right = micros() - t_right
        distance_right = duration_right * 0.034 / 2
        trig_left.high()
        pyb.udelay(10)
        trig_left.low()
        while echo_left.value() == 0: pass
        t_left = micros()
        while echo_left.value() == 1: pass
        duration_left = micros() - t_left
        distance_left = duration_left * 0.034 / 2
        
        #duration单位是us，所以340要*10^-4
        if distance_middle<=20:
            a=py1.value()
            b=py2.value()
            c=py3.value()
            d=py4.value()
            e=py5.value()
            f=py6.value()
            g=py7.value()
            h=py8.value()
            py1.low()
            py2.high()
            py3.high()
            py4.low()
            py5.low()
            py6.high()
            py7.high()
            py8.low()
            pwp1=81.081
            pwp2=79.293
            pwp3=79.694
            pwp4=79.599
            ch1.pulse_width_percent(pwp1)
            ch2.pulse_width_percent(pwp2)
            ch3.pulse_width_percent(pwp3)
            ch4.pulse_width_percent(pwp4)
            pyb.delay(1000)
            py1.value(a)
            py2.value(b)
            py3.value(c)
            py4.value(d)
            py5.value(e)
            py6.value(f)
            py7.value(g)
            py8.value(h)
        else:
            pwp1=pwp1x*(1/2*exp(-20*distance_left**2)-1/2*exp(-20*distance_right**2)-exp(-20*distance_middle**2)+1)
            pwp2=pwp2x*(1/3*exp(-20*distance_left**2)-1/2*exp(-20*distance_right**2)-exp(-20*distance_middle**2)+1)
            pwp3=pwp4x*(1/2*exp(-20*distance_right**2)-1/2*exp(-20*distance_left**2)-exp(-20*distance_middle**2)+1)
            pwp4=pwp4x*(1/2*exp(-20*distance_right**2)-1/2*exp(-20*distance_left**2)-exp(-20*distance_middle**2)+1)
        print(pwp1)
        print(pwp2)
        print(pwp3)
        print(pwp4)
        print(distance_middle)
        print(distance_left)
        print(distance_right)
        last_ultrasonic_time=micros()
    else:
        pyb.delay(10)
#     percentage = distance / 100
