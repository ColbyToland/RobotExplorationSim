"""
This robot randomly selects a destination, navigates to it with A*, then selects another random destination.
"""

import arcade

import Robot


TYPE_NAME = "pc"


class PlayerCharacterRobot(Robot.Robot):
    """ User controlled robot """
    def __init__(self, robot_group_id: int, wall_list: arcade.SpriteList, speed: float=5):
        super().__init__(robot_group_id, wall_list, speed)

        self.name = "Player"
        self.nametext.text = self.name
        self.replan_on_collision = False

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def _check_and_fix_jammed_robot(self):
        """ Disable jam checking """
        pass

    def update_speed(self):
        """ Update the player speed """

        # Calculate speed based on the keys pressed
        self.change_x = 0
        self.change_y = 0

        if self.up_pressed and not self.down_pressed:
            self.change_y = self.speed
        elif self.down_pressed and not self.up_pressed:
            self.change_y = -self.speed
        if self.left_pressed and not self.right_pressed:
            self.change_x = -self.speed
        elif self.right_pressed and not self.left_pressed:
            self.change_x = self.speed