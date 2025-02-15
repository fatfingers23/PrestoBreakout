import random
from time import sleep
from machine import Pin, I2C
from micropython import const
from presto import Presto
import adafruit_nunchuk
from math import sqrt
from utime import ticks_ms, ticks_diff


class Ball(object):
    """Ball."""

    def __init__(self, x, y, x_speed, y_speed, display, radius=4, frozen=False):
        """Initialize ball.

        Args:
            x, y (int): Initial position of the ball (center of the circle).
            x_speed, y_speed (int): Initial speed of the ball.
            display (PRESTO display): Presto display object.
            radius (int): Radius of the ball.
            frozen (bool): Whether the ball is frozen to the paddle.
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.prev_x = x
        self.prev_y = y
        self.max_x_speed = 3
        self.max_y_speed = 3
        self.frozen = frozen
        self.display = display
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.x_speed2 = 0.0
        self.y_speed2 = 0.0
        self.created = ticks_ms()
        self.ball_color = display.create_pen(255, 0, 0)  # Red color for the ball
        self.background_color = display.create_pen(255, 255, 255)  # White color for the background
        self.display_width = 240
        self.display_height = 240

    def clear(self):
        """Clear ball."""
        self.display.set_pen(self.background_color)
        self.display.circle(self.x, self.y, self.radius)

    def clear_previous(self):
        """Clear previous ball position."""
        self.display.set_pen(self.background_color)
        self.display.circle(self.prev_x, self.prev_y, self.radius)

    def draw(self):
        """Draw ball."""
        self.clear_previous()
        self.display.set_pen(self.ball_color)
        self.display.circle(self.x, self.y, self.radius)

    def set_position(self, paddle_x, paddle_y, paddle_x2, paddle_center):
        """Set ball position and handle collisions.

        Args:
            paddle_x, paddle_y (int): Paddle position.
            paddle_x2 (int): Paddle right edge.
            paddle_center (int): Paddle center.

        Returns:
            bool: True if the ball bounced, False otherwise.
        """
        bounced = False
        self.prev_x = self.x
        self.prev_y = self.y

        # Check if frozen to paddle
        if self.frozen:
            # Freeze ball to top center of paddle
            self.x = paddle_x + (paddle_center - self.radius)
            self.y = paddle_y - self.radius
            if ticks_diff(ticks_ms(), self.created) >= 2000:
                # Release frozen ball after 2 seconds
                self.frozen = False
            else:
                return bounced

        # Update ball position
        self.x += int(self.x_speed) + int(self.x_speed2)
        self.x_speed2 -= int(self.x_speed2)
        self.x_speed2 += self.x_speed - int(self.x_speed)

        self.y += int(self.y_speed) + int(self.y_speed2)
        self.y_speed2 -= int(self.y_speed2)
        self.y_speed2 += self.y_speed - int(self.y_speed)

        # Bounce off walls
        if self.y - self.radius < 10:  # Top wall
            self.y = 10 + self.radius
            self.y_speed = -self.y_speed
            bounced = True
        if self.x + self.radius >= self.display_width - 10:  # Right wall
            self.x = self.display_width - 10 - self.radius
            self.x_speed = -self.x_speed
            bounced = True
        elif self.x - self.radius < 10:  # Left wall
            self.x = 10 + self.radius
            self.x_speed = -self.x_speed
            bounced = True

        # Check for collision with paddle
        if (self.y + self.radius >= paddle_y and
                self.x - self.radius <= paddle_x2 and
                self.x + self.radius >= paddle_x):
            # Ball bounces off paddle
            self.y = paddle_y - (self.radius + 1)
            ratio = ((self.x) - (paddle_x + paddle_center)) / paddle_center
            self.x_speed = ratio * self.max_x_speed
            self.y_speed = -sqrt(max(1, self.max_y_speed ** 2 - self.x_speed ** 2))
            bounced = True

        return bounced


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
        self.paddle_color = display.create_pen(0, 0, 0)
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
        new_x = max(0, min(x, self.display_width - self.width))
        if new_x != self.x:  # Check if paddle moved
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


class Life(object):
    """Life."""

    def __init__(self, index, display, width=4, height=6):
        """Initialize life.

        Args:
            index (int): Life number (1-based).
            display (SSD1351): OLED g.display.
            width (Optional int): Life width
            height (Optional int): Life height
        """
        margin = 5
        self.display = display
        self.x = margin + (index * (width + margin))
        self.y = 10
        self.width = width
        self.height = height
        self.background_color = display.create_pen(255, 255, 255)
        self.color = display.create_pen(0, 0, 0)
        self.draw()

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


def load_level(level, display, level_color):
    global frameRate
    # if demo :
    #   frameRate = 60 + level * 10
    # else :
    frameRate = 25 + level * 5
    level_bricks = []
    # for row in range(12, 20 + 6 * level , 6):
    for row in range(30, 100 + 10 * level, 10):  # Start at row 30, increment by 10
        # print(row)
        # 1st affects how many?
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

# PADDLE = Paddle(display, 40, 10)

count = 0
level = 1
# level_color = display.create_pen(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
# level_color = display.create_pen(255, 0, 0)
# bricks = load_level(level, display, level_color)
touch = presto.touch
i2c = I2C(0, scl=Pin(41), sda=Pin(40), freq=400_000)
# x 127 is middle, y 128
nc = adafruit_nunchuk.Nunchuk(i2c)
prev_paddle_vect = 0
MAX_LEVEL = const(5)

demoOn = False
exitGame = False
while not exitGame:
    paddle_width = 40
    frameRate = 30
    # gc.collect()
    # print (gc.mem_free())

    gameOver = False
    usePaddle = False
    if demoOn:
        demo = True
    else:
        demo = False

    while True:
        display.set_pen(WHITE)
        display.set_layer(0)
        display.clear()
        display.set_pen(BLACK)
        display.text("BREAKOUT", 0, 0, scale=2)
        display.text("Press C to start", 100, 0)
        if nc.buttons.C:
            break
        presto.update()

    if not exitGame:
        display.set_pen(WHITE)
        display.set_layer(0)
        display.clear()
        level = 1
        bricks = load_level(level, display, display.create_pen(level + 25, level + 25, level + 25))

        # Initialize paddle
        paddle = Paddle(display, paddle_width, 10)
        # Initialize balls
        balls = []
        # Add first ball
        balls.append(Ball(59, 58, -2, -1, display, frozen=True))
        # Initialize lives
        lives = []
        for i in range(0, 3):
            print(i)
            lives.append(Life(i, display))
        prev_paddle_vect = 0

        presto.update()
        # try:
        while not gameOver:
            x, y = nc.joystick
            move_amount = 0
            # if x > 127:
            #     prev_paddle_vect = 1
            # elif x < 127:
            #     prev_paddle_vect = -1

            paddle_vect = 0
            if x < 127:
                paddle_vect = -1
            elif x > 127:
                paddle_vect = 1
            if paddle_vect != prev_paddle_vect:
                paddle_vect *= 3
            else:
                paddle_vect *= 5
            paddle.h_position(paddle.x + paddle_vect)
            prev_paddle_vect = paddle_vect
            presto.update()

        # if usePaddle :
# while True:
#     # touch.poll()
#     x, y = nc.joystick
#     move_amount = 0
#     # if x > 127:
#     #     prev_paddle_vect = 1
#     # elif x < 127:
#     #     prev_paddle_vect = -1
#
#     paddle_vect = 0
#     if x < 127:
#         paddle_vect = -1
#     elif x > 127:
#         paddle_vect = 1
#     if paddle_vect != prev_paddle_vect:
#         paddle_vect *= 3
#     else:
#         paddle_vect *= 5
#     PADDLE.h_position(PADDLE.x + paddle_vect)
#     prev_paddle_vect = paddle_vect
#
#
#     # ax, ay, az = nc.acceleration
#     # print("joystick = {},{}".format(x, y))
#     # print("accceleration ax={}, ay={}, az={}".format(ax, ay, az))
#
#     count += 1
#     display.set_pen(WHITE)
#     display.set_layer(0)
#     display.clear()
#     for brick in bricks:
#         brick.draw()
#
#     PADDLE.draw()
#
#     # Finally we update the screen with our changes :)
#     presto.update()
#
#




