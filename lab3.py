

__author__ = 'mandriy'

import sfml.sf as sf
import time
import lab1
from functools import partial
import multiprocessing
import multiprocessing.queues as mqueues
import sys
from Tkinter import Tk, Button, Label
from tkFileDialog import askopenfilename, asksaveasfilename
import math


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


class ChangeDrawColorEvent(object):

    def __init__(self, color):
        self._color = color.r, color.g, color.b, color.a

    def color(self):
        return sf.Color(*self._color)


class ChangeStateEvent(object):

    def __init__(self, state):
        self.state = state


class OpenImageEvent(object):

    def __init__(self, path):
        self.path = path


class SaveImageEvent(object):

    def __init__(self, path):
        self.path = path


class ClearEvent(object):

    def __init__(self):
        pass


class FillApplicationInterface(object):

    def __init__(self, controller):
        self._controller = controller
        self._controller_process = None
        self._events_queue = None
        self._listeners = {}
        self._opened = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def add_listener(self, event_type, func):
        if event_type in self._listeners:
            self._listeners[event_type].append(func)
        else:
            self._listeners[event_type] = [func]

    def open(self):
        if not self._opened:
            self._events_queue = mqueues.Queue()
            self._controller_process = multiprocessing.Process(target=self._controller, args=(self._events_queue, ))
            self._controller_process.start()
            self._opened = True

    def close(self):
        if self._controller_process is not None:
            self._controller_process.terminate()
        self._opened = False

    def handle_events(self):
        for event in self.events():
            if type(event) in self._listeners:
                event_listeners = self._listeners[type(event)]
                for listener in event_listeners:
                    listener(event)

    def events(self):
        events = []
        while not self._events_queue.empty():
            events.append(self._events_queue.get())
        return events


def tkinter_controller(events_queue):
    window = Tk()
    window.title('Tools')

    def change_color(color):
        events_queue.put(ChangeDrawColorEvent(color))

    def change_state(state):
        events_queue.put(ChangeStateEvent(state))

    def choose_image_file(file_event, dialog):
        filename = dialog()
        if filename:
            events_queue.put(file_event(filename))

    file_dialog_options = {
        'defaultextension': '.jpg',
        'filetypes': (('all files', '.*'),
                      ('Bitmap Picture', '.bmp'),
                      ('Portable network graphics', '.png'),
                      ('Truevision', '.tga'),
                      ('Joint Photographic Experts Group', '.jpg')),
        'parent': window
    }

    Label(window, text='Menu').pack()
    Button(window, text='Save Image',
           command=partial(choose_image_file, SaveImageEvent,
                           partial(asksaveasfilename, title='Save Image', **file_dialog_options))).pack()
    Button(window, text='Open Image',
           command=partial(choose_image_file, OpenImageEvent,
                           partial(askopenfilename, title='Open Image', **file_dialog_options))).pack()
    Label(window, text='Drawing').pack()
    Button(window, text='Pencil', command=partial(change_state, 'pencil')).pack()
    Button(window, text='Fill', command=partial(change_state, 'fill')).pack()
    Button(window, text='Rectangle', command=partial(change_state, 'rectangle')).pack()
    Button(window, text='Circle', command=partial(change_state, 'circle')).pack()
    Button(window, text='Polygonal', command=partial(change_state, 'polygonal')).pack()
    Button(window, text='Eraser', command=partial(change_state, 'eraser')).pack()
    Button(window, text='Clear', command=lambda: events_queue.put(ClearEvent())).pack()
    Label(window, text='Colors').pack()
    Button(window, activebackground='red', bg='red', command=partial(change_color, sf.Color.RED)).pack()
    Button(window, activebackground='blue', bg='blue', command=partial(change_color, sf.Color.BLUE)).pack()
    Button(window, activebackground='black', bg='black', command=partial(change_color, sf.Color.BLACK)).pack()
    Button(window, activebackground='green', bg='green', command=partial(change_color, sf.Color.GREEN)).pack()
    Button(window, activebackground='yellow', bg='yellow', command=partial(change_color, sf.Color.YELLOW)).pack()
    Button(window, activebackground='cyan', bg='cyan', command=partial(change_color, sf.Color.CYAN)).pack()
    Button(window, activebackground='white', bg='white', command=partial(change_color, sf.Color.WHITE)).pack()
    Button(window, activebackground='magenta', bg='magenta', command=partial(change_color, sf.Color.MAGENTA)).pack()
    window.mainloop()


class Line(sf.Drawable):

    def __init__(self, a, b, color):
        super(Line, self).__init__()
        self._rep = sf.VertexArray(sf.PrimitiveType.LINES_STRIP)
        self._rep.append(sf.Vertex(a, color))
        self._rep.append(sf.Vertex(b, color))

    def draw(self, target, states):
        target.draw(self._rep, states)


class FillApplication(object):
    PENCIL_STATE = "pencil"
    FILL_STATE = "fill"
    RECTANGLE_STATE = "rectangle"
    CIRCLE_STATE = "circle"
    POLYGONAL_STATE = "polygonal"
    ERASER_STATE = "eraser"
    SAVE_IMAGE_FORMATS = ['tga', 'png', 'bmp', 'jpg']

    def __init__(self, controller, mode=sf.VideoMode(800, 800), bg=sf.Color.WHITE, algorithm=line_filling):
        self._state = self.PENCIL_STATE
        self._interface = FillApplicationInterface(controller)
        self._bg = bg
        self._mode = mode
        self._algorithm = algorithm
        self._draw_color = sf.Color.GREEN
        self._draw_area = sf.RenderTexture(mode.width, mode.height)
        self._dynamic_screen_objects = []
        self._draw_area.clear(self._bg)
        self._draw_scope = {}
        self._draw_states = {
            self.PENCIL_STATE: self._pencil_handler,
            self.FILL_STATE: self._fill_handler,
            self.CIRCLE_STATE: self._circle_handler,
            self.RECTANGLE_STATE: self._rectangle_handler,
            self.POLYGONAL_STATE: self._polygonal_handler,
            self.ERASER_STATE: self._eraser_handler
        }

    def __call__(self):
        with self._interface as iface:
            iface.add_listener(ChangeDrawColorEvent, self._change_color_listener)
            iface.add_listener(OpenImageEvent, self._open_image)
            iface.add_listener(SaveImageEvent, self._save_image)
            iface.add_listener(ChangeStateEvent, self._change_draw_state)
            iface.add_listener(ClearEvent, lambda _: self._draw_area.clear(self._bg))
            window = sf.RenderWindow(self._mode, "Fill Algorithms Application.", sf.Style.TITLEBAR + sf.Style.CLOSE)
            while window.is_open:
                iface.handle_events()
                for event in window.events:
                    if type(event) is sf.CloseEvent:
                        window.close()
                    else:
                        self._draw_states[self._state](event)

                window.clear(sf.Color.WHITE)
                self._draw_area.display()
                window.draw(sf.Sprite(self._draw_area.texture))
                for dynamic_object in self._dynamic_screen_objects:
                    window.draw(dynamic_object)
                window.display()

    # interface handlers

    def _check_supported_img_formats(self, path):
        for suffix in self.SAVE_IMAGE_FORMATS:
            if path.endswith('.' + suffix):
                return True
        return False

    def _save_image(self, save_img_event):
        if self._check_supported_img_formats(save_img_event.path):
            current_screen_img = self._draw_area.texture.to_image()
            current_screen_img.to_file(save_img_event.path)
        else:
            print >> sys.stderr, 'selected image format is not supported.'

    def _open_image(self, load_img_event):
        try:
            img = sf.Image.from_file(load_img_event.path)
            img.flip_vertically()
            self._draw_area.texture.update_from_image(img)
        except IOError:
            print >> sys.stderr, 'failed to load image %s.' % load_img_event.path

    def _change_color_listener(self, color_event):
        self._draw_color = color_event.color()

    def _change_draw_state(self, state_event):
        if state_event.state in self._draw_states:
            self._state = state_event.state
            self._draw_scope = {}
            self._dynamic_screen_objects = []

    # drawing handlers

    def _figures_handler(self, figure_prototype, event):
        if type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.pressed:
            self._draw_scope['start-point'] = event.position
            self._dynamic_screen_objects.append(figure_prototype())
        elif type(event) is sf.MouseMoveEvent and sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
            if 'start-point' not in self._draw_scope:
                self._draw_scope['start-point'] = event.position
                self._dynamic_screen_objects.append(figure_prototype())
            self._dynamic_screen_objects[0] = figure_prototype()
        elif type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.released:
            self._draw_area.draw(figure_prototype())
            del self._dynamic_screen_objects[0]
            del self._draw_scope['start-point']

    def _rectangle_handler(self, event):
        def get_rectangle():
            start_point_x, start_point_y = self._draw_scope['start-point']
            current_x, current_y = event.position
            rect = sf.RectangleShape((abs(start_point_x - current_x), abs(start_point_y - current_y)))
            rect.outline_color = self._draw_color
            rect.fill_color = sf.Color.TRANSPARENT
            rect.outline_thickness = 1
            rect.position = (min(current_x, start_point_x), min(current_y, start_point_y))
            return rect

        self._figures_handler(get_rectangle, event)

    def _circle_handler(self, event):
        def get_circle():
            start_point_x, start_point_y = self._draw_scope['start-point']
            current_x, current_y = event.position
            diameter = int(math.sqrt(abs(start_point_x - current_x) ** 2 + abs(start_point_y - current_y) ** 2))
            circle = sf.CircleShape()
            circle.outline_color = self._draw_color
            circle.fill_color = sf.Color.TRANSPARENT
            circle.outline_thickness = 1
            circle.radius = diameter / 2
            circle.position = ((start_point_x + current_x) / 2 - circle.radius,
                               (start_point_y + current_y) / 2 - circle.radius)
            return circle

        self._figures_handler(get_circle, event)

    def _pencil_handler(self, event):
        def check_point():
            if 'prev-point' not in self._draw_scope:
                self._draw_scope['prev-point'] = event.position
        if type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.pressed:
            check_point()
        elif type(event) is sf.MouseMoveEvent and sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
            check_point()
            self._draw_area.draw(Line(event.position, self._draw_scope['prev-point'], self._draw_color))
            self._draw_scope['prev-point'] = event.position
        elif type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.released:
            self._draw_area.draw(Line(event.position, self._draw_scope['prev-point'], self._draw_color))
            del self._draw_scope['prev-point']

    def _polygonal_handler(self, event):
        def check_point():
            if 'prev-point' not in self._draw_scope:
                self._draw_scope['prev-point'] = event.position
                self._draw_scope['polygonal-started'] = True
                self._dynamic_screen_objects.append(Line(event.position, event.position, self._draw_color))
            else:
                self._draw_area.draw(Line(self._draw_scope['prev-point'], event.position, self._draw_color))
                self._draw_scope['prev-point'] = event.position

        if type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.pressed:
            check_point()
        elif type(event) is sf.MouseMoveEvent and 'polygonal-started' in self._draw_scope:
            if sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
                check_point()
            self._dynamic_screen_objects[0] = Line(self._draw_scope['prev-point'], event.position, self._draw_color)
        elif type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.RIGHT and event.pressed:
            del self._dynamic_screen_objects[0]
            del self._draw_scope['prev-point']
            del self._draw_scope['polygonal-started']

    def _fill_handler(self, event):
        if type(event) is sf.MouseButtonEvent and sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
            current_screen_img = self._draw_area.texture.to_image()
            new_screen_img = self._algorithm(current_screen_img, event.position, self._draw_color)
            new_screen_img.flip_vertically()
            self._draw_area.texture.update_from_image(new_screen_img)

    def _eraser_handler(self, event):
        erase_size = 16

        def get_erase_circle(_x, _y):
            eraser = sf.CircleShape(erase_size)
            eraser.fill_color = self._bg
            eraser.position = (_x - erase_size, _y - erase_size)
            return eraser

        if type(event) is sf.MouseMoveEvent and sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
            if 'eraser-prev' in self._draw_scope:

                x, y = event.position
                prev_x, prev_y = self._draw_scope['eraser-prev']
                dx = abs(x - prev_x)
                dy = abs(y - prev_y)
                max_change = max(dx, dy)
                if max_change > 0:
                    x_step_func = partial(lab1.get_step(prev_x, x), step_size=float(dx) / (float(max_change)))
                    y_step_func = partial(lab1.get_step(prev_y, y), step_size=float(dy) / (float(max_change)))
                    x_iter = prev_x
                    y_iter = prev_y
                    for _ in xrange(0, max_change):
                        self._draw_area.draw(get_erase_circle(int(round(x_iter)), int(round(y_iter))))
                        x_iter = x_step_func(x_iter)
                        y_iter = y_step_func(y_iter)
            self._draw_scope['eraser-prev'] = event.position
        elif type(event) is sf.MouseButtonEvent and event.button == sf.Mouse.LEFT and event.released:
            self._draw_area.draw(get_erase_circle(*event.position))
            if 'eraser-prev' in self._draw_scope:
                del self._draw_scope['eraser-prev']

if __name__ == "__main__":
    fill_app = FillApplication(tkinter_controller)
    fill_app()