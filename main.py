# All the game logic and classes are ported over from the breakout.py found in the cheungbx/gameESP-micropython github repo
# https://github.com/cheungbx/gameESP-micropython/blob/master/breakout.py

from machine import Pin, I2C
from micropython import const
from presto import Presto
import adafruit_nunchuk
from math import sqrt
from utime import ticks_ms, ticks_diff


class Ball(object):
    """Ball."""

    def __init__(self, x, y, x_speed, y_speed, display, width=10, height=10,
                 frozen=False):
        self.x = x
        self.y = y
        self.x2 = x + width - 1
        self.y2 = y + height - 1
        self.prev_x = x
        self.prev_y = y
        self.width = width
        self.height = height
        self.center = width // 2
        self.max_x_speed = 3
        self.max_y_speed = 3
        self.frozen = frozen
        self.display = display
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.x_speed2 = 0.0
        self.y_speed2 = 0.0
        self.created = ticks_ms()
        self.color = display.create_pen(0, 0, 0)
        self.background_color = display.create_pen(255, 255, 255)
    def clear(self):
        """Clear ball."""
        self.display.set_pen(self.background_color)
        display.rectangle(self.x, self.y, self.width, self.height)

    def clear_previous(self):
        """Clear prevous ball position."""
        self.display.set_pen(self.background_color)
        display.rectangle(self.prev_x, self.prev_y, self.width, self.height)

    def draw(self):
        """Draw ball."""
        self.clear_previous()
        self.display.set_pen(self.color)
        display.rectangle(self.x, self.y, self.width, self.height)

    def set_position(self, paddle_x, paddle_y, paddle_x2, paddle_center):
        bounced = False
        """Set ball position."""
        self.prev_x = self.x
        self.prev_y = self.y
        # Check if frozen to paddle
        if self.frozen:
            # Freeze ball to top center of paddle
            self.x = paddle_x + (paddle_center - self.center)
            self.y = paddle_y - self.height
            if ticks_diff(ticks_ms(), self.created) >= 2000:
                # Release frozen ball after 2 seconds
                self.frozen = False
            else:
                return
        self.x += int(self.x_speed) + int(self.x_speed2)
        self.x_speed2 -= int(self.x_speed2)
        self.x_speed2 += self.x_speed - int(self.x_speed)

        self.y += int(self.y_speed) + int(self.y_speed2)
        self.y_speed2 -= int(self.y_speed2)
        self.y_speed2 += self.y_speed - int(self.y_speed)

        far_right_wall = 240
        # Bounces off walls
        #Top bounce?
        if self.y < 30:
            # Bounce on top
            self.y = 32
            self.y_speed = -self.y_speed
            bounced = True
        if self.x + self.width >= far_right_wall:
            self.x = far_right_wall - self.width
            self.x_speed = -self.x_speed
            bounced = True
        elif self.x < 3:
            self.x = 3
            self.x_speed = -self.x_speed
            bounced = True

        # Check for collision with Paddle
        if (self.y2 >= paddle_y and
           self.x <= paddle_x2 and
           self.x2 >= paddle_x):
            # Ball bounces off paddle
            self.y = paddle_y - (self.height + 1)
            ratio = ((self.x + self.center) -
                     (paddle_x + paddle_center)) / paddle_center
            self.x_speed = ratio * self.max_x_speed
            self.y_speed = -sqrt(max(1, self.max_y_speed ** 2 - self.x_speed ** 2))
            bounced = True

        self.x2 = self.x + self.width - 1
        self.y2 = self.y + self.height - 1
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
        self.clear()

    def clear(self):
        """Clear paddle."""
        self.display.set_pen(WHITE)
        # Clears the whole bottom of the screen since the paddle can change in size
        display.rectangle(0, self.y, 240, self.height)

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
            display: presto display.
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

    def __init__(self, index, display, width=4, height=8):
        """Initialize life.

        Args:
            index (int): Life number (1-based).
            display: presto display.
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

    def draw(self):
        """Draw brick."""
        self.display.set_pen(self.color)
        display.rectangle(self.x, self.y, self.width, self.height)

class Score(object):
    """Score."""

    def __init__(self, display):
        """Initialize score.

        Args:
            display: presto display.
        """
        margin = 40
        self.display = display
        display.text("Score:", 160, 8, scale=2)
        self.x = 180 + margin
        self.y = 8
        self.value = 0
        self.background_color = display.create_pen(255, 255, 255)
        self.color = display.create_pen(0, 0, 0)
        self.draw()

    def draw(self):
        """Draw score value."""
        self.display.set_pen(self.background_color)
        display.rectangle(self.x, self.y, 25, 20)
        self.display.set_pen(self.color)
        display.text(str(self.value), self.x, self.y, scale=2)

    def game_over(self):
        """Display game_over."""
        self.display.set_pen(self.color)
        self.display.text("GAME OVER", 20, 170, scale=2)
        self.display.text("Press C to start", 20, 190)

    def increment(self, points):
        """Increase score by specified points."""
        self.value += points
        self.draw()

def load_level(level, display, level_color):
    level_bricks = []
    # Sets the pen to white to clear previous level
    display.set_pen(display.create_pen(255, 255, 255))
    display.rectangle(40, 8, 80, 20)
    # Sets the pen to black to write level
    display.set_pen(display.create_pen(0, 0, 0))
    display.text(f"Level: {level}", 40, 8, scale=2)

    for row in range(30, 50 + 10 * level, 10):  # Start at row 30, increment by 10
        for col in range(20, 220, 25):  # Start at column 20, increment by 25
            level_bricks.append(Brick(col, row, level_color, display))

    return level_bricks


# Setup for the Presto display
presto = Presto()
display = presto.display
display.set_layer(0)
display.set_font("bitmap8")
WIDTH, HEIGHT = display.get_bounds()

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

count = 0
level = 1
# level_color = display.create_pen(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
# level_color = display.create_pen(255, 0, 0)

i2c = I2C(0, scl=Pin(41), sda=Pin(40), freq=400_000)
nc = adafruit_nunchuk.Nunchuk(i2c)
prev_paddle_vect = 0
MAX_LEVEL = const(5)
BACKLIGHT_BRIGHTNESS = .50

exitGame = False
while not exitGame:

    paddle_width = 70
    frameRate = 30
    gameWon = False
    gameOver = False
    usePaddle = False


    while True:
        display.set_pen(WHITE)
        display.clear()
        display.set_pen(BLACK)
        display.text("BREAKOUT", 10, 10, scale=2)
        display.text("Press C to start", 10, 30)
        if nc.buttons.C:
            break
        presto.set_backlight(BACKLIGHT_BRIGHTNESS)
        presto.update()

    if not exitGame:
        display.set_pen(WHITE)
        display.clear()
        level = 1
        bricks = load_level(level, display, display.create_pen(level + 25, level + 25, level + 25))

        # Initialize paddle
        paddle = Paddle(display, paddle_width, 10)
        # Initialize score
        score = Score(display)

        # Initialize balls
        balls = []
        # Add first ball
        balls.append(Ball(120, 120, -2, -1, display, frozen=True))
        # Initialize lives
        lives = []
        for i in range(0, 3):
            lives.append(Life(i, display))
        prev_paddle_vect = 0
        presto.set_backlight(BACKLIGHT_BRIGHTNESS)
        presto.update()

        while not gameOver:
            x, y = nc.joystick

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



            # Handle balls
            score_points = 0
            for ball in balls:
                #True it hits something
                ball.set_position(paddle.x, paddle.y,paddle.x2, paddle.center)
                # move ball and check if bounced off walls and paddle
                # if ball.set_position(paddle.x, paddle.y, paddle.x2, paddle.center):
                    #TODO add a buzzer beep here
                    # g.playSound(900, 10)
                # Check for collision with bricks if not frozen
                if not ball.frozen:
                    prior_collision = False
                    ball_x = ball.x
                    ball_y = ball.y
                    ball_x2 = ball.x2
                    ball_y2 = ball.y2
                    ball_center_x = ball.x + ((ball.x2 + 1 - ball.x) // 2)
                    ball_center_y = ball.y + ((ball.y2 + 1 - ball.y) // 2)

                    # Check for hits
                    for brick in bricks:
                        if (ball_x2 >= brick.x and
                                ball_x <= brick.x2 and
                                ball_y2 >= brick.y and
                                ball_y <= brick.y2):
                            # Hit
                            if not prior_collision:
                                ball.x_speed, ball.y_speed = brick.bounce(
                                    ball.x,
                                    ball.y,
                                    ball.x2,
                                    ball.y2,
                                    ball.x_speed,
                                    ball.y_speed,
                                    ball_center_x,
                                    ball_center_y)
                                # g.playTone('c6', 10)
                                prior_collision = True
                            score_points += 1
                            brick.clear()
                            bricks.remove(brick)

                    # Check for missed
                if ball.y2 > HEIGHT - 2:
                    ball.clear_previous()
                    balls.remove(ball)
                    if not balls:
                        # Lose life if last ball on screen
                        if len(lives) == 0:
                            score.game_over()
                            while True:
                                if nc.buttons.C:
                                    break
                                presto.update()
                            # TODO add a buzzer beep here for lose
                            # g.playTone('g4', 500)
                            # g.playTone('c5', 200)
                            # g.playTone('f4', 500)
                            gameOver = True
                        else:
                            # Subtract Life
                            lives.pop().clear()
                            # Add ball
                            balls.append(Ball(59, 58, 2, -3, display,
                                              frozen=True))
                else:
                    # Draw ball
                    ball.draw()
                    # Update score if changed
                if score_points:
                    #TODO uncomment next line to test going to the next level by scoring once

                    # bricks.clear()
                    score.increment(score_points)
                # Check for level completion
                if not bricks:
                    for ball in balls:
                        ball.clear()
                    balls.clear()
                    level += 1
                    #Make the paddle smaller with each level up
                    paddle = Paddle(display, (paddle_width - (level * 5)), 10)
                    paddle_width -= 2
                    if level > MAX_LEVEL:
                        level = 1
                        score.game_over()
                        display.text("You've won!", 20, 150)
                        presto.update()
                        while True:
                            if nc.buttons.C:
                                break
                        gameOver = True
                    bricks = load_level(level, display, display.create_pen(level + 25, level + 25, level + 25))
                    balls.append(Ball(59, 58, -2, -1, display, frozen=True))
                presto.set_backlight(BACKLIGHT_BRIGHTNESS)
                presto.update()
