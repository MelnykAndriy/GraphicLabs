__author__ = 'mandriy'

import sfml.sf as sf
import pycurve


class BezierApplication(object):
    POINT_COLLECTING = 1
    DISPLAYING = 2

    def __init__(self, step_number=1000, connect=True):
        self._connect = connect
        self._basic_bezier_points = []
        self._draw_bezier_nodes = []
        self._draw_bezier_points = sf.VertexArray(sf.PrimitiveType.POINTS)
        self._state = self.POINT_COLLECTING
        self._step_number = step_number
        self._basic_point_connections = sf.VertexArray(sf.PrimitiveType.LINES_STRIP)

    def _add_basic_point(self, point):
        mark = sf.CircleShape(5)
        mark.position = point[0]-5, point[1]-5
        mark.fill_color = sf.Color.RED
        self._draw_bezier_nodes.append(mark)
        self._basic_bezier_points.append(point)

    def _clear_basic_points(self):
        self._basic_bezier_points = []
        self._draw_bezier_nodes = []
        self._basic_point_connections = sf.VertexArray(sf.PrimitiveType.LINES_STRIP)

    def _clear_bezier_points(self):
        self._draw_bezier_points = sf.VertexArray(sf.PrimitiveType.POINTS)

    def _spline_degree(self):
            if len(self._basic_bezier_points) == 2:
                return 1
            elif len(self._basic_bezier_points) == 3:
                return 2
            else:
                return 3

    def _calculate_bezier_points(self):
        points = self._basic_bezier_points
        if len(points) > 1:
            n = len(points) - 1
            k = self._spline_degree()
            m = n + k + 1
            _t = 1.0 / (m - k * 2)
            t = k * [0] + [t_ * _t for t_ in xrange(m - (k * 2) + 1)] + [1] * k
            bezier_curve = pycurve.Bspline(points, t, k)
            step = 1.0 / self._step_number
            for i in xrange(self._step_number):
                x, y = bezier_curve(i * step)
                self._draw_bezier_points.append(sf.Vertex((int(x), int(y)), sf.Color.BLUE))

    def _calculate_basic_points_connections(self):
        if self._connect:
            for basic_point in self._basic_bezier_points:
                self._basic_point_connections.append(sf.Vertex(basic_point, sf.Color.GREEN))

    def __call__(self):
        window = sf.RenderWindow(sf.VideoMode(640, 480), "Bezier Draw Application.", sf.Style.TITLEBAR + sf.Style.CLOSE)
        while window.is_open:
            for event in window.events:
                if type(event) is sf.CloseEvent:
                    window.close()
                elif type(event) is sf.MouseButtonEvent and event.pressed:
                    if self._state == self.POINT_COLLECTING:
                        self._add_basic_point(event.position)
                elif type(event) is sf.KeyEvent and event.pressed and event.code:
                    if sf.Keyboard.is_key_pressed(sf.Keyboard.DELETE):
                        self._state = self.POINT_COLLECTING
                        self._clear_basic_points()
                        self._clear_bezier_points()
                    elif sf.Keyboard.is_key_pressed(sf.Keyboard.RETURN):
                        if len(self._basic_bezier_points) > 1:
                            self._state = self.DISPLAYING
                            self._calculate_bezier_points()
                            self._calculate_basic_points_connections()

            window.clear(sf.Color.WHITE)
            if self._state == self.DISPLAYING:
                window.draw(self._basic_point_connections)
                window.draw(self._draw_bezier_points)

            for mark in self._draw_bezier_nodes:
                window.draw(mark)

            window.display()

if __name__ == "__main__":
    bezier_app = BezierApplication(connect=True)
    bezier_app()