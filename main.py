import random
from time import sleep
from machine import Pin, I2C
from presto import Presto
import adafruit_nunchuk

class Paddle(object):
    """Paddle."""

    def __init__(self, display, width, height):
        """Initialize paddle.

        Args:
            display (PRESTO display): presto g.display.
            width (Optional int): Paddle width
            height (Optional int): Paddle height
        """
        self.x = 100
        self.y = 230
        self.x2 = self.x + width - 1
        self.y2 = self.y + height - 1
        self.width = width
        self.height = height
        self.center = width // 2
        self.display = display
        self.paddle_color =  display.create_pen(0, 0, 0)
        self.background_color = display.create_pen(255, 255, 255)
        self.display_width = 240

    def clear(self):
        """Clear paddle."""
        self.display.set_pen(WHITE)
        display.rectangle(self.x, self.y, self.width, self.height)


    def draw(self):
        """Draw paddle."""
        self.display.set_pen(BLACK)
        display.rectangle(self.x, self.y, self.width, self.height)

    def h_position(self, x):
        """Set paddle position.

        Args:
            x (int):  X coordinate.
        """
        new_x = max(3,min (x, self.display_width-self.width))
        if new_x != self.x :  # Check if paddle moved
            prev_x = self.x  # Store previous x position
            self.x = new_x
            self.x2 = self.x + self.width - 1
            self.y2 = self.y + self.height - 1
            self.draw()
            # Clear previous paddle
            self.display.set_pen(WHITE)
            if x > prev_x:
                display.rectangle(prev_x, self.y, x - prev_x, self.height)
            else:
                display.rectangle(prev_x + self.width, self.y, (prev_x + self.width) - (x + self.width), self.height)
        else:
            self.draw()

class Brick(object):
    """Brick."""

    def __init__(self, x, y, color, display, width=20, height=5):
        """Initialize brick.

        Args:
            x, y (int):  X,Y coordinates.
            color (string):  Blue, Green, Pink, Red or Yellow.
            display (SSD1351): OLED g.display.
            width (Optional int): Blick width
            height (Optional int): Blick height
        """
        self.x = x
        self.y = y
        self.x2 = x + width - 1
        self.y2 = y + height - 1
        self.center_x = x + (width // 2)
        self.center_y = y + (height // 2)
        self.color = color
        self.width = width
        self.height = height
        self.display = display
        self.background_color = display.create_pen(255, 255, 255)
        self.draw()

    def bounce(self, ball_x, ball_y, ball_x2, ball_y2,
               x_speed, y_speed,
               ball_center_x, ball_center_y):
        """Determine bounce for ball collision with brick."""
        x = self.x
        y = self.y
        x2 = self.x2
        y2 = self.y2
        center_x = self.center_x
        center_y = self.center_y
        if ((ball_center_x > center_x) and
           (ball_center_y > center_y)):
            if (ball_center_x - x2) < (ball_center_y - y2):
                y_speed = -y_speed
            elif (ball_center_x - x2) > (ball_center_y - y2):
                x_speed = -x_speed
            else:
                x_speed = -x_speed
                y_speed = -y_speed
        elif ((ball_center_x > center_x) and
              (ball_center_y < center_y)):
            if (ball_center_x - x2) < -(ball_center_y - y):
                y_speed = -y_speed
            elif (ball_center_x - x2) > -(ball_center_y - y):
                x_speed = -x_speed
            else:
                x_speed = -x_speed
                y_speed = -y_speed
        elif ((ball_center_x < center_x) and
              (ball_center_y < center_y)):
            if -(ball_center_x - x) < -(ball_center_y - y):
                y_speed = -y_speed
            elif -(ball_center_x - x) > -(ball_center_y - y):
                y_speed = -y_speed
            else:
                x_speed = -x_speed
                y_speed = -y_speed
        elif ((ball_center_x < center_x) and
              (ball_center_y > center_y)):
            if -(ball_center_x - x) < (ball_center_y - y2):
                y_speed = -y_speed
            elif -(ball_center_x - x) > (ball_center_y - y2):
                x_speed = -x_speed
            else:
                x_speed = -x_speed
                y_speed = -y_speed

        return [x_speed, y_speed]

    def clear(self):
        """Clear brick."""
        self.display.set_pen(self.background_color)
        display.rectangle(self.x, self.y, self.width, self.height)
        # self.display.fill_rect(self.x, self.y, self.width, self.height, 0)

    def draw(self):
        """Draw brick."""
        self.display.set_pen(self.color)
        display.rectangle(self.x, self.y, self.width, self.height)
        # self.display.rect(self.x, self.y, self.width, self.height, 1)


def load_level(level, display, level_color) :
    global frameRate
    # if demo :
    #   frameRate = 60 + level * 10
    # else :
    frameRate = 25 + level * 5
    level_bricks = []
    # for row in range(12, 20 + 6 * level , 6):
    for row in range(30, 100 + 10 * level, 10):  # Start at row 30, increment by 10
        # print(row)
        #1st affects how many?
        # Full width?
        # 3rd is spacing?
        # idk = range(4, 222, 22)
        # print(idk)
        for col in range(20, 220, 25):  # Start at column 20, increment by 25
        # for col in range(0, 220, 22 ):
            # display..
            # print(f"Col: {col}")
            level_bricks.append(Brick(col, row, level_color, display))

    return level_bricks


# Setup for the Presto display
presto = Presto()
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

PADDLE = Paddle(display, 40, 10)

count = 0
level = 1
# level_color = display.create_pen(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
level_color = display.create_pen(255, 0, 0)
bricks = load_level(level, display, level_color)
touch = presto.touch
i2c = I2C(0, scl=Pin(41), sda=Pin(40), freq=400_000)
# i2c.scan()
# i2c.write(b"\xF0\x55")
# sleep(20)
# i2c.write(b"\xFB\x00")
# i2c.stop()
nc = adafruit_nunchuk.Nunchuk(i2c)
while True:
    # touch.poll()
    x, y = nc.joystick
    ax, ay, az = nc.acceleration
    print("joystick = {},{}".format(x, y))
    print("accceleration ax={}, ay={}, az={}".format(ax, ay, az))

    count += 1
    display.set_pen(WHITE)
    display.set_layer(0)
    display.clear()
    for brick in bricks:
        brick.draw()

    PADDLE.h_position(count)
    PADDLE.draw()

    # Finally we update the screen with our changes :)
    presto.update()




