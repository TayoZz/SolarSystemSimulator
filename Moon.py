from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtSvg import *
import numpy as np
import math


class Moon(QGraphicsPixmapItem):
    G = 6.67428e-11  # Gravitational constant
    # Using a small timestep for physics updates; adjust as needed.
    TIMESTEP = 3600 * 24 / 20 # Example: one day per physics step
    AU = 1.496e11
    SCALE = 90000
    #37400
    METER_PER_PIXEL = AU / SCALE

    def __init__(self, name, mass, scene, x, y, size, texture_path, planet):
        super().__init__()

        self.planet = planet
        self.name = name
        self.mass = mass
        self.size = size
        self.hover_state = False
        self.distance = math.hypot(0, 0)
        self.type = Moon

        self.text_item = QGraphicsSimpleTextItem(self.name.upper(), self)
        self.text_item.setBrush(QColor("white"))
        self.text_item.setFont(QFont("Bahnschrift", 10))
        self.text_item.setPos(self.boundingRect().width() / 2, self.boundingRect().height() / 2)
        scene.addItem(self.text_item)
        self.text_item.setVisible(False)

        # Set the moon's absolute simulation position (in meters)
        self.sim_pos = planet.sim_pos + np.array([x * self.AU, 0])
        # Also, store the relative position (moon relative to planet)
        self.rel_pos = self.sim_pos - self.planet.sim_pos
        # Initialize the relative velocity to zero (or set an initial value as needed)
        self.rel_velocity = np.array([0.0, 0.0])

        if texture_path.lower().endswith('.svg'):
            self.is_svg = True
            self.svg_renderer = QSvgRenderer(texture_path)
            self.pixmap = None
        else:
            self.is_svg = False
            pixmap = QPixmap(texture_path)
            if pixmap.isNull():
                self.pixmap = QPixmap()
            else:
                # Convert to QImage and scale for better quality
                image = pixmap.toImage()
                image = image.scaled(int(size * 2), int(size * 2),
                                     aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                     transformMode=Qt.TransformationMode.SmoothTransformation)
                self.pixmap = QPixmap.fromImage(image)
            self.svg_renderer = None



        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(10)
        glow.setColor(QColor(255, 255, 255))
        glow.setOffset(0)
        self.setGraphicsEffect(glow)

        # Position the moon on-screen relative to its planet
        self.setOffset(-int(size), -int(size))
        self.setPos((self.sim_pos[0] - self.planet.sim_pos[0]) / self.METER_PER_PIXEL + self.planet.x(),
                    (self.sim_pos[1] - self.planet.sim_pos[1]) / self.METER_PER_PIXEL + self.planet.y())
        self.velocity = np.array([0.0, 0.0])  # Absolute velocity (for reference)
        self.acceleration = np.array([0.0, 0.0])
        scene.addItem(self)
        self.scene = scene
        self.setZValue(1)

    def boundingRect(self):
        # The item is centered at (0, 0) with width and height equal to size * 2.
        return QRectF(-self.size, -self.size, self.size * 2, self.size * 2)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Define the target rectangle for SVG rendering
        rect = self.boundingRect()

        if self.is_svg and self.svg_renderer is not None:
            # Compute aspect-ratio-preserved target rect (as before)
            viewBox = self.svg_renderer.viewBoxF()
            scale = min(rect.width() / viewBox.width(), rect.height() / viewBox.height())
            target_width = viewBox.width() * scale
            target_height = viewBox.height() * scale
            target_rect = QRectF(
                rect.center().x() - target_width / 2,
                rect.center().y() - target_height / 2,
                target_width,
                target_height,
            )

            # Manually clip to the desired shape (e.g. an ellipse)
            clip_path = QPainterPath()
            clip_path.addEllipse(rect)
            painter.setClipPath(clip_path)

            self.svg_renderer.render(painter, target_rect)
        elif self.pixmap and not self.pixmap.isNull():
            painter.drawPixmap(self.boundingRect().topLeft(), self.pixmap)
        else:
            painter.setBrush(QColor(255, 0, 0))
            painter.drawEllipse(self.boundingRect())

    def setHoverState(self, hovered):
        self.hover_state = hovered
        if hovered and self.name != "sun":
            self.setScale(1.15)
        else:
            self.setScale(1.0)

    def setFocusState(self, focused: bool):
        self.text_item.setVisible(focused)

    def attraction(self, other):
        own_pos = self.sim_pos
        other_pos = other.sim_pos
        distance_vector = other_pos - own_pos
        distance = np.linalg.norm(distance_vector)
        if distance == 0:
            return np.array([0.0, 0.0])
        force = Moon.G * self.mass * other.mass / (distance ** 2)
        return (force / distance) * distance_vector

    def update_position(self, simulation_speed):
        # Compute gravitational force and update relative motion
        net_force = self.attraction(self.planet)
        a_rel = net_force / self.mass
        self.rel_velocity += a_rel * self.TIMESTEP * simulation_speed
        self.rel_pos += self.rel_velocity * self.TIMESTEP * simulation_speed

        # Recompute the absolute simulation position
        self.sim_pos = self.planet.sim_pos + self.rel_pos

        # Compute new on-screen position relative to the planet's position
        new_pos = QPointF(
            (self.sim_pos[0] - self.planet.sim_pos[0]) / self.METER_PER_PIXEL + self.planet.x(),
            (self.sim_pos[1] - self.planet.sim_pos[1]) / self.METER_PER_PIXEL + self.planet.y()
        )

        self.updatePosition(new_pos)
        self.update()

    def updatePosition(self, new_pos: QPointF):
        """Call this whenever the planet's position is updated."""
        self.setPos(new_pos)
        # Update text position relative to the planet.
        offset = QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)
        self.text_item.setPos(self.pos() + offset)
