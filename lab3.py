

__author__ = 'mandriy'

import sfml.sf as sf
import time
from functools import partial
import multiprocessing
import multiprocessing.queues as mqueues
import Tkinter


def recursive_filling(img, start_pixel, new_color):
    start_x, start_y = start_pixel
    if not 0 <= start_x < img.size.x or not 0 <= start_y < img.size.y:
        raise ValueError('Invalid pixel coordinates.')
    old_color = img[(start_x, start_y)]

    def fill_inner(pixel):
        x, y = pixel
        if 0 <= x < img.size.x and 0 <= y < img.size.y and img[tuple(pixel)] == old_color:
            img[tuple(pixel)] = new_color
            fill_inner((x - 1, y))
            fill_inner((x + 1, y))
            fill_inner((x, y - 1))
            fill_inner((x, y + 1))

    if old_color != new_color:
        fill_inner(start_pixel)

    return img


def stack_filling(img, start_pixel, new_color):
    start_x, start_y = start_pixel
    if not 0 <= start_x < img.size.x or not 0 <= start_y < img.size.y:
        raise ValueError('Invalid pixel coordinates.')
    old_color = img[(start_x, start_y)]

    if old_color != new_color:
        pixels_stack = [(start_x, start_y)]

        while pixels_stack:
            x, y = pixels_stack.pop()
            if 0 <= x < img.size.x and 0 <= y < img.size.y:
                if img[(x, y)] == old_color:
                    img[(x, y)] = new_color
                    pixels_stack.extend([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)])

    return img


class Pixel(sf.Drawable):

    def __init__(self, pos, color):
        super(Pixel, self).__init__()
        self._pos = pos
        self._color = color

    def draw(self, target, states):
        pixel = sf.VertexArray(sf.PrimitiveType.POINTS)
        pixel.append(sf.Vertex(self._pos, self._color))
        target.draw(pixel)


def line_filling(img, start_pixel, new_color):
    start_x, start_y = start_pixel
    if not 0 <= start_x < img.size.x or not 0 <= start_y < img.size.y:
        raise ValueError('Invalid pixel coordinates.')
    old_color = img[(start_x, start_y)]

    if old_color != new_color:
        pixels_stack = [(start_x, start_y)]

        while pixels_stack:
            x, y = pixels_stack.pop()

            x_iter_left = x
            x_iter_right = x + 1
            right_stop_not_found = True
            left_stop_not_found = True

            while right_stop_not_found or left_stop_not_found:
                if right_stop_not_found:
                    if x_iter_right < img.size.x and img[(x_iter_right, y)] == old_color:
                        img[(x_iter_right, y)] = new_color
                        x_iter_right += 1
                    else:
                        x_iter_right -= 1
                        right_stop_not_found = False

                if left_stop_not_found:
                    if x_iter_left >= 0 and img[(x_iter_left, y)] == old_color:
                        img[(x_iter_left, y)] = new_color
                        x_iter_left -= 1
                    else:
                        x_iter_left += 1
                        left_stop_not_found = False

            prev_pixels = {-1: None, 1: None}

            def find_y_neighbors(y_direction, _x, _y):
                if img[(_x, _y + y_direction)] == old_color:
                    prev_pixels[y_direction] = (_x, _y + y_direction)
                else:
                    if prev_pixels[y_direction] is not None:
                        pixels_stack.append(prev_pixels[y_direction])
                        prev_pixels[y_direction] = None

            directions_func_chain = []

            if y != 0:
                directions_func_chain.append(partial(find_y_neighbors, -1))
            if y != img.size.y - 1:
                directions_func_chain.append(partial(find_y_neighbors, 1))

            for x_iter in xrange(x_iter_left, x_iter_right + 1):
                for func in directions_func_chain:
                    func(x_iter, y)

            if prev_pixels[-1] is not None:
                pixels_stack.append(prev_pixels[-1])

            if prev_pixels[1] is not None:
                pixels_stack.append(prev_pixels[1])

    return img


class FillApplicationInterface(object):

    def __init__(self):
        pass

    def events(self):
        pass


class FillApplication(object):
    DRAW_STATE = 1
    FILL_STATE = 2

    def __init__(self, mode=sf.VideoMode(800, 800), bg=sf.Color.WHITE, algorithm=line_filling):
        self._state = self.DRAW_STATE
        self._bg = bg
        self._mode = mode
        self._algorithm = algorithm
        self._draw_color = sf.Color.GREEN  # TODO give opportunity for user to change it
        self._draw_area = sf.RenderTexture(mode.width, mode.height)
        self._draw_area.clear(self._bg)

    def __call__(self):
        window = sf.RenderWindow(self._mode, "Fill algorithms application.", sf.Style.TITLEBAR + sf.Style.CLOSE)
        line = None
        while window.is_open:
            for event in window.events:
                if type(event) is sf.CloseEvent:
                    window.close()
                elif type(event) is sf.KeyEvent:
                    if sf.Keyboard.is_key_pressed(sf.Keyboard.DELETE):
                        self._draw_area.clear(self._bg)
                    elif sf.Keyboard.is_key_pressed(sf.Keyboard.NUM1):
                        self._state = self.DRAW_STATE
                    elif sf.Keyboard.is_key_pressed(sf.Keyboard.NUM2):
                        self._state = self.FILL_STATE
                else:
                    if self._state == self.DRAW_STATE:

                        if type(event) is sf.MouseMoveEvent and sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
                            if line is None:
                                line = sf.VertexArray(sf.PrimitiveType.LINES_STRIP)
                            line.append(sf.Vertex(event.position, self._draw_color))
                            self._draw_area.draw(line)
                        elif type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.released:
                            line.append(sf.Vertex(event.position, self._draw_color))
                            self._draw_area.draw(line)
                            line = None

                    elif self._state == self.FILL_STATE:

                        if type(event) is sf.MouseButtonEvent and sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
                            current_screen_img = self._draw_area.texture.to_image()
                            print "algorithm started"
                            s = time.time()
                            new_screen_img = self._algorithm(current_screen_img, event.position, self._draw_color)
                            print time.time() - s
                            new_screen_img.flip_vertically()
                            self._draw_area.texture.update_from_image(new_screen_img)

            window.clear(sf.Color.WHITE)
            self._draw_area.display()
            window.draw(sf.Sprite(self._draw_area.texture))
            window.display()

if __name__ == "__main__":
    fill_app = FillApplication()
    fill_app()