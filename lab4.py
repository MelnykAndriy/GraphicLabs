__author__ = 'mandriy'


import sfml.sf as sf
import math


class SerpinskiTriangle(sf.Drawable):

    def __init__(self, level, top, left, right):
        super(SerpinskiTriangle, self).__init__()
        self._triangles = []
        self._calc_triangle(level, top, left, right)

    def _calc_triangle(self, level, top, left, right):
        if level == 0:
            triangle = sf.VertexArray(sf.PrimitiveType.LINES_STRIP)
            triangle.append(sf.Vertex(top, sf.Color.BLACK))
            triangle.append(sf.Vertex(left, sf.Color.BLACK))
            triangle.append(sf.Vertex(right, sf.Color.BLACK))
            triangle.append(sf.Vertex(top, sf.Color.BLACK))
            self._triangles.append(triangle)
        else:
            left_mid = self._mid_point(top, left)
            right_mid = self._mid_point(top, right)
            top_mid = self._mid_point(left, right)

            self._calc_triangle(level - 1, top, left_mid, right_mid)
            self._calc_triangle(level - 1, left_mid, left, top_mid)
            self._calc_triangle(level - 1, right_mid, top_mid, right)


    def _mid_point(self, point1, point2):
        return (point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2


    def draw(self, target, states):
        for triangle in self._triangles:
            target.draw(triangle, states)


class KochSnowflake(sf.Drawable):

    def __init__(self, n):
        super(KochSnowflake, self).__init__()
        self._koch = sf.VertexArray(sf.PrimitiveType.LINES_STRIP)

        angles = [math.radians(60*x) for x in range(6)]
        sines = [math.sin(x) for x in angles]
        cosin = [math.cos(x) for x in angles]

        def L(angle, *_):
            return (angle + 1) % 6
        def R(angle, *_):
            return (angle + 4) % 6
        def F(angle, coords, jump):
            coords.append(
                (coords[-1][0] + jump * cosin[angle],
                 coords[-1][1] + jump * sines[angle]))
            return angle

        decode = dict(L=L, R=R, F=F)

        def grow(steps, length=500, startPos=(80, 480)):
            pathcodes="FRFRF"
            for i in xrange(steps):
                pathcodes = pathcodes.replace("F", "FLFRFLF")

            jump = float(length) / (3 ** steps)
            coords = [startPos]
            angle = 0

            for move in pathcodes:
                angle = decode[move](angle, coords, jump)

            return coords

        showflake = grow(n)
        for coord in showflake:
            self._koch.append(sf.Vertex((int(coord[0]), int(coord[1])), sf.Color.BLACK))

    def draw(self, target, states):
        target.draw(self._koch, states)


class MandelbrotSet(sf.Drawable):

    def __init__(self, w, h, iterations=100, center=(-0.7, 0), diameter=2.5):
        super(MandelbrotSet, self).__init__()
        self._iterations = iterations
        mandelbrot_drawing = sf.Image.create(w, h)
        real = center[0] - 0.5 * diameter
        imag = center[1] - 0.5 * diameter

        for x in range(w):
            for y in range(h):
                i = self._mandel(complex(real, imag))
                mandelbrot_drawing[(x, h-y)] = self._color(i)
                imag += diameter / h
            imag = center[1] - 0.5 * diameter
            real += diameter / w

        self._mandelbrot_texture = sf.Texture.from_image(mandelbrot_drawing)

    def _color(self, i):
        colors = (sf.Color(0x00, 0x00, 0xAA), sf.Color(0x88, 0xDD, 0xFF), sf.Color(0xFF, 0x88, 0x00),  sf.Color.BLACK)
        if i == self._iterations:
            return colors[-1]
        else:
            choice = (i//2) % len(colors)
        return colors[choice]

    def _mandel(self, c):
        z = 0
        for i in range(self._iterations):
            z = z**2 + c
            if abs(z) > 2:
                return i
        return self._iterations

    def draw(self, target, states):
        target.draw(sf.Sprite(self._mandelbrot_texture), states)


class FractalApp(object):

    def __init__(self, mode=sf.VideoMode(640, 640)):
        self._mode = mode
        self._fractal = SerpinskiTriangle(7, (320, 100), (100, 500), (540, 500))

    def __call__(self, scrollSpeed=50):
        current_view = sf.View()
        current_view.reset(sf.Rectangle((0, 0), (self._mode.width, self._mode.width)))
        window = sf.RenderWindow(self._mode, "Fractal Application.", sf.Style.TITLEBAR + sf.Style.CLOSE)
        while window.is_open:

            for event in window.events:
                if type(event) is sf.CloseEvent:
                    window.close()
                elif type(event) is sf.KeyEvent and event.pressed:
                    if sf.Keyboard.is_key_pressed(sf.Keyboard.NUM1):
                        self._fractal = MandelbrotSet(self._mode.width, self._mode.height)
                    elif sf.Keyboard.is_key_pressed(sf.Keyboard.NUM2):
                        self._fractal = KochSnowflake(5)
                    elif sf.Keyboard.is_key_pressed(sf.Keyboard.NUM3):
                        self._fractal = SerpinskiTriangle(0, (320, 100), (100, 500), (540, 500))

                elif type(event) is sf.MouseWheelEvent:
                    if event.delta > 0:
                        current_view.size = (current_view.size.x - scrollSpeed, current_view.size.y - scrollSpeed)
                    elif event.delta < 0:
                        current_view.size = (current_view.size.x + scrollSpeed, current_view.size.y + scrollSpeed)
                elif type(event) is sf.MouseMoveEvent:
                    if sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
                        x, y = event.position
                        current_view.center = self._mode.width - x, self._mode.height - y

            window.view = current_view
            window.clear(sf.Color.WHITE)
            window.draw(self._fractal)
            window.display()



if __name__ == "__main__":
    fill_app = FractalApp()
    fill_app()