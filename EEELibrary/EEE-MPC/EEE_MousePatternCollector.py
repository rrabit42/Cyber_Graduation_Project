# collect pattern only if cursor position has changed
# action interval, button state, x, y

# action interval - interval time with above value
# button state - Move, Drag, Scroll, Left-Pressed, Left-Released, Right-Pressed, Right-Released

import time
from pynput.mouse import Listener
import csv

before_time = time.time()
is_pressed = False

def MPC(filename):
    
    f = open(filename,'w',newline='')
    wr = csv.writer(f)
    wr.writerow(['action interval', 'button state', 'x', 'y'])

    def on_move(x, y):
        global before_time
        global is_pressed

        now_time = time.time()
        interval_time = int(50*(now_time-before_time))

        if is_pressed is True:
            print(interval_time, "Drag", x, y)
            wr.writerow([interval_time, "Drag", x, y])
        
        if is_pressed is False:
            print(interval_time, "Move", x, y)
            wr.writerow([interval_time, "Move", x, y])
        before_time = now_time


    def on_click(x, y, button, pressed):
        global before_time
        global is_pressed

        now_time = time.time()
        interval_time = int(50*(now_time-before_time))

        if pressed is True:
            is_pressed = True
            if button.name == 'left':
                print(interval_time, "Left-Pressed", x, y)
                wr.writerow([interval_time, "Left-Pressed", x, y])
            if button.name == 'right':
                print(interval_time, "Right-Pressed", x, y)
                wr.writerow([interval_time, "Right-Pressed", x, y])
            before_time = now_time

        else:
            is_pressed = False
            if button.name == 'left':
                print(interval_time, "Left-Released", x, y)
                wr.writerow([interval_time, "Left-Released", x, y])
            if button.name == 'right':
                print(interval_time, "Right-Released", x, y)
                wr.writerow([interval_time, "Right-Released", x, y])
            before_time = now_time 


    def on_scroll(x, y, dx, dy):
        global before_time 
        now_time = time.time()
        interval_time = int(50*(now_time-before_time))

        print(interval_time, "Scroll", x, y)
        wr.writerow([interval_time, "Scroll", x, y])
        before_time = now_time


    with Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()