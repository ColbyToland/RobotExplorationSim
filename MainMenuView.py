"""
This is the initial main menu copied from an arcade demo (original comment below) with tweaked parameters.

---

This example procedurally develops a random cave based on cellular automata.

For more information, see:
https://gamedevelopment.tutsplus.com/tutorials/generate-random-cave-levels-using-cellular-automata--gamedev-9664

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.procedural_caves_cellular
"""

import arcade

from GameView import GameView


class MainMenuView(arcade.View):
    """ View to show instructions """

    def __init__(self):
        super().__init__()
        self.frame_count = 0

    def on_show_view(self):
        """ This is run once when we switch to this view """
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        """ Draw this view """
        self.clear()
        arcade.draw_text("Loading...", self.window.width / 2, self.window.height / 2,
                         arcade.color.BLACK, font_size=50, anchor_x="center")

    def on_update(self, dt):
        if self.frame_count == 0:
            self.frame_count += 1
            return

        """ If the user presses the mouse button, start the game. """
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)