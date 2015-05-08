__author__ = 'mandriy'

import sfml.sf as sf
import math


class IntPoint(object):

    def __init__(self, x, y):
        self._x = int(x)
        self._y = int(y)

    def getX(self):
        return self._x

    def getY(self):
        return self._y


class Scalable(object):

    def __init__(self, scale=1, **_):
        self._scale = scale

    def scale(self):
        return self._scale

    def scaled_pixel(self, pos):
        pixel = sf.RectangleShape((self._scale, self._scale))
        pixel.position = (pos[0]*self._scale, pos[1]*self._scale)
        return pixel


class PixelScalable(Scalable):

    def __init__(self, **kwargs):
        super(PixelScalable, self).__init__(**kwargs)

    def _make_pixel(self, point, color):
        pixel = self.scaled_pixel(point)
        pixel.fill_color = color
        return pixel


class CompositeDrawable(sf.Drawable):

    def __init__(self):
        super(CompositeDrawable, self).__init__()

    def _get_components(self):
        return []

    def draw(self, target, states):
        for component in self._get_components():
            target.draw(component, states)


class BresenhamLine(CompositeDrawable, PixelScalable):

    def __init__(self, a, b, color=sf.Color.BLACK, **kwargs):
        super(BresenhamLine, self).__init__()
        PixelScalable.__init__(self, **kwargs)
        self._pixels = []

        dx = abs(b.getX() - a.getX())
        dy = abs(b.getY() - a.getY())
        x_step = get_step(a.getX(), b.getX())
        y_step = get_step(a.getY(), b.getY())
        pdx, pdy = 0, 0

        if dx > dy:
            pdx = x_step(0)
            es = dy
            el = dx
        else:
            pdy = y_step(0)
            es = dx
            el = dy

        current_x = a.getX()
        current_y = a.getY()
        err = el / 2

        self._pixels.append(self._make_pixel((current_x, current_y), color))

        for _ in xrange(0, el):
            err -= es
            if err < 0:
                err += el
                current_x = x_step(current_x)
                current_y = y_step(current_y)
            else:
                current_x += pdx
                current_y += pdy
            self._pixels.append(self._make_pixel((current_x, current_y), color))

    def _get_components(self):
        return self._pixels


def get_step(_from, _to):
    if _from < _to:
        return lambda x, step_size=1: x + step_size
    return lambda x, step_size=1: x - step_size


class BresenhamCircle(CompositeDrawable, PixelScalable):

    def __init__(self, center, radius, color=sf.Color.BLACK, **kwargs):
        super(BresenhamCircle, self).__init__()
        PixelScalable.__init__(self, **kwargs)
        self._pixels = []
        current_x = 0
        current_y = int(radius)
        delta = 1 - 2 * int(radius)
        while current_y >= 0:
            self._pixels.extend([
                self._make_pixel((center.getX() + current_x, center.getY() + current_y), color),
                self._make_pixel((center.getX() + current_x, center.getY() - current_y), color),
                self._make_pixel((center.getX() - current_x, center.getY() + current_y), color),
                self._make_pixel((center.getX() - current_x, center.getY() - current_y), color)
            ])
            error = 2 * (delta + current_y) - 1
            if delta < 0 and error <= 0:
                current_x += 1
                delta += 2 * current_x + 1
                continue
            error = 2 * (delta - current_x) - 1
            if delta > 0 and error > 0:
                current_y -= 1
                delta += 1 - 2 * current_y
                continue
            current_x += 1
            delta += 2 * (current_x - current_y)
            current_y -= 1

    def _get_components(self):
        return self._pixels


class WuLine(CompositeDrawable, PixelScalable):

    def __init__(self, a, b, color=sf.Color.BLACK, **kwargs):
        super(WuLine, self).__init__()
        Scalable.__init__(self, **kwargs)
        self._pixels = []

        def mute_color(coef):
            return sf.Color(color.r, color.g, color.b, coef * color.a)

        dx = abs(b.getX() - a.getX())
        dy = abs(b.getY() - a.getY())
        x_step = get_step(a.getX(), b.getX())
        y_step = get_step(a.getY(), b.getY())

        if dx == 0:
            y_direction = y_step(0)
            for y_shift in xrange(0, dy + 1):
                self._pixels.append(self._make_pixel((a.getX(), a.getY() + y_shift * y_direction), color))
        elif dy == 0:
            x_direction = x_step(0)
            for x_shift in xrange(0, dx + 1):
                self._pixels.append(self._make_pixel((a.getX() + x_shift * x_direction, a.getY()), color))
        else:
            self._pixels.append(self._make_pixel((a.getX(), a.getY()), color))
            if dy > dx:
                grad = float(dx) / float(dy)
                current_x = x_step(float(a.getX()), grad)
                current_y = y_step(a.getY())
                while current_y != b.getY():
                    xfpart, xipart = math.modf(current_x)
                    self._pixels.append(self._make_pixel((int(xipart), current_y), mute_color(1 - xfpart)))
                    self._pixels.append(self._make_pixel((int(xipart) + 1, current_y), mute_color(xfpart)))
                    current_y = y_step(current_y)
                    current_x = x_step(current_x, grad)
            else:
                grad = float(dy) / float(dx)
                current_y = y_step(float(a.getY()), grad)
                current_x = x_step(a.getX())
                while current_x != b.getX():
                    yfpart, yipart = math.modf(current_y)
                    self._pixels.append(self._make_pixel((current_x, int(yipart)), mute_color(1 - yfpart)))
                    self._pixels.append(self._make_pixel((current_x, int(yipart) + 1), mute_color(yfpart)))
                    current_x = x_step(current_x)
                    current_y = y_step(current_y, grad)
            self._pixels.append(self._make_pixel((b.getX(), b.getY()), color))

    def _get_components(self):
        return self._pixels


class Ellipse(CompositeDrawable, Scalable):

    def __init__(self, center, height, width, color=sf.Color.BLACK, **kwargs):
        super(Ellipse, self).__init__()
        Scalable.__init__(self, **kwargs)
        self._ellipse_lines = []
        self._color = color
        base_point = IntPoint(center.getX() - (int(width)) / 2, center.getY() - (int(height)) / 2)
        sqr_root, prev_sr = 0, 0
        doubled_height = int(height) ** 2
        doubled_width = int(width) ** 2
        for i in xrange(1, 2 * width + 1):
            sqr_root = int(math.sqrt(doubled_height - (((doubled_height * (width - i)) * (width - i)) / doubled_width)))
            self._ellipse_lines.append(
                self.make_line(IntPoint(base_point.getX() + i - 1 - width / 2,
                                        base_point.getY() + height / 2 + prev_sr),
                               IntPoint(base_point.getX() + i - width / 2, base_point.getY() + height / 2 + sqr_root))
            )
            self._ellipse_lines.append(
                self.make_line(IntPoint(base_point.getX() + i - 1 - width / 2,
                                        base_point.getY() + height / 2 - prev_sr),
                               IntPoint(base_point.getX() + i - width / 2, base_point.getY() + height / 2 - sqr_root))
            )
            prev_sr = sqr_root

    def _get_components(self):
        return self._ellipse_lines

    def make_line(self, from_point, to_point):
        return BresenhamLine(from_point, to_point, scale=self.scale(), color=self._color)


class WuEllipse(Ellipse):

    def __init__(self, *args, **kwargs):
        super(WuEllipse, self).__init__(*args, **kwargs)

    def make_line(self, from_point, to_point):
        return WuLine(from_point, to_point, scale=self.scale(), color=self._color)


class DrawApp(object):

    def __init__(self, draw_entities):
        self._draw_entities = draw_entities

    def __call__(self):

        window = sf.RenderWindow(sf.VideoMode(800, 800), "Primitives", sf.Style.TITLEBAR + sf.Style.CLOSE)
        while window.is_open:
            for event in window.events:
                if type(event) is sf.CloseEvent:
                    window.close()

            window.clear(sf.Color.WHITE)
            for drawable in self._draw_entities:
                window.draw(drawable)
            window.display()


if __name__ == '__main__':
    app = DrawApp([
        WuLine(IntPoint(50, 350), IntPoint(100, 100), color=sf.Color.GREEN),
        WuLine(IntPoint(150, 350), IntPoint(100, 100), color=sf.Color.GREEN),
        WuLine(IntPoint(65, 275), IntPoint(135, 275), color=sf.Color.GREEN),

        BresenhamLine(IntPoint(170, 350), IntPoint(220, 100), color=sf.Color.MAGENTA),
        BresenhamLine(IntPoint(270, 350), IntPoint(220, 100), color=sf.Color.MAGENTA),
        BresenhamLine(IntPoint(185, 275), IntPoint(255, 275), color=sf.Color.MAGENTA),

        WuLine(IntPoint(290, 350), IntPoint(340, 100), color=sf.Color.RED),
        WuLine(IntPoint(340, 100), IntPoint(360, 200), color=sf.Color.RED),
        WuLine(IntPoint(360, 200), IntPoint(380, 100), color=sf.Color.RED),
        WuLine(IntPoint(380, 100), IntPoint(430, 350), color=sf.Color.RED),

        # WuLine(IntPoint(20, 60), IntPoint(60, 10), scale=8),
        # BresenhamLine(IntPoint(40, 60), IntPoint(80, 10), scale=8),
        # Ellipse(IntPoint(50, 50), 40, 20, scale=8),
        # BresenhamCircle(IntPoint(50, 50), 20, scale=8),
        # BresenhamCircle(IntPoint(50, 50), 40, scale=8)
        # WuEllipse(IntPoint(150, 50), 40, 40, scale=1)
        # BresenhamCircle(Point(400, 400), radius=100, scale=1),
        # Ellipse(Point(400, 400), 100, 300, scale=1),
        # BresenhamCircle(IntPoint(400, 400), radius=300, scale=1),
        #
        # BresenhamLine(Point(100, 100), Point(700, 700), scale=1)
    ])
    app()
