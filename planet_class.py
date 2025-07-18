from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtSvg import *
import math
import numpy as np

class PlanetObject(QGraphicsObject):
    # Simulation constants
    G = 6.67428e-11
    TIMESTEP = 3600 * 24  # 24 hours per physics update (in simulation units)
    AU = 1.496e11
    SCALE = 2000
    HIGHSCALE = 1000
    METER_PER_PIXEL = AU / SCALE
    METER_PER_PIXEL_HIGHSCALE = AU / HIGHSCALE

    def __init__(self, name, mass, scene, x, y, size, scaletype, texture_path, solar_system):
        super().__init__()
        self.name = name
        self.mass = mass
        self.size = size  # This represents the radius
        self.solar_system = solar_system
        self.sim_pos = np.array([x * self.AU, y * self.AU])
        self.scaletype = scaletype
        self.hover_state = False
        self.distance = math.hypot(0, 0)
        self.is_followed = False
        self.type = PlanetObject

        if self.name != "sun":
            self.text_item = QGraphicsSimpleTextItem(self.name.upper(), self)
            self.text_item.setBrush(QColor("white"))
            if self.scaletype == "SCALE":
                self.text_item.setFont(QFont("Bahnschrift", 20))
            else:
                self.text_item.setFont(QFont("Bahnschrift", 20))
            # Position the text item a bit under and to the right of the planet
            if self.name == "uranus" or self.name == "saturn":
                self.text_item.setPos(self.boundingRect().width() / 4, self.boundingRect().height() / 4)
            else:
                self.text_item.setPos(self.boundingRect().width() / 2, self.boundingRect().height() / 2)

            scene.addItem(self.text_item)
            self.text_item.setVisible(False)

        # Check if the texture is an SVG
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

        # Special case: the sun uses a custom pixmap (not SVG)
        if self.name == "sun":
            diameter = int(size * 2)
            self.pixmap = create_sun_pixmap(diameter)
            self.is_svg = False

        # Apply dro shadow effects based on the object type

        if self.name == "sun":
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(30)
            glow.setColor(QColor(255, 80, 0))
            glow.setOffset(0)
            self.setGraphicsEffect(glow)
        else:
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(15)
            glow.setColor(QColor(255, 255, 255))
            glow.setOffset(0)
            self.setGraphicsEffect(glow)

        # Set the initial position based on the simulation coordinates
        if self.scaletype == "SCALE":
            self.setPos(self.sim_pos[0] / self.METER_PER_PIXEL,
                        self.sim_pos[1] / self.METER_PER_PIXEL)
        else:
            self.setPos(self.sim_pos[0] / self.METER_PER_PIXEL_HIGHSCALE,
                        self.sim_pos[1] / self.METER_PER_PIXEL_HIGHSCALE)

        self.velocity = np.array([0.0, 0.0])
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
            if self.solar_system.view.zoom_factor < 1.2:
                self.setScale(1.2)
            else:
                self.setScale(1.05)
        else:
            self.setScale(1.0)

    def setFocusState(self, focused: bool):
        if self.name != "sun":
            self.text_item.setVisible(focused)

    def attraction(self, other):
        if self == other:
            return np.array([0.0, 0.0])
        own_pos = self.sim_pos
        other_pos = other.sim_pos
        distance_vector = other_pos - own_pos
        # Calculate the distance vector and its magnitude
        # Use np.linalg.norm for better readability and efficiency
        # Also, avoid using math.hypot as it is not necessary here
        distance = np.linalg.norm(distance_vector)
        if distance == 0:
            return np.array([0.0, 0.0])
        force = PlanetObject.G * self.mass * other.mass / (distance ** 2)
        return (force / distance) * distance_vector

    def update_position(self, planets, custom_objects, simulation_speed):
        net_force = np.array([0.0, 0.0])
        for planet in planets:
            if self != planet and planet.name == "sun":
                net_force += self.attraction(planet)
        for custom_object in custom_objects:
            net_force += self.attraction(custom_object)
        self.acceleration = net_force / self.mass
        self.velocity += self.acceleration * self.TIMESTEP * simulation_speed
        self.sim_pos += self.velocity * self.TIMESTEP * simulation_speed

        if self.scaletype == "SCALE":
            new_pos = QPointF(self.sim_pos[0] / self.METER_PER_PIXEL,
                              self.sim_pos[1] / self.METER_PER_PIXEL)
        else:
            new_pos = QPointF(self.sim_pos[0] / self.METER_PER_PIXEL_HIGHSCALE,
                              self.sim_pos[1] / self.METER_PER_PIXEL_HIGHSCALE)

            # Update both the planet and its text position
        self.updatePosition(new_pos)
        self.update()  # Request a redraw

    def updatePosition(self, new_pos: QPointF):
        """Call this whenever the planet's position is updated."""
        self.setPos(new_pos)
        if self.name != "sun":
            # Update text position relative to the planet.
            if self.name == "uranus" or self.name == "saturn":
                offset = QPointF(self.boundingRect().width() / 4, self.boundingRect().height() / 4)
            else:
                offset = QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)

            self.text_item.setPos(self.pos() + offset)

def create_sun_pixmap(diameter):
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.GlobalColor.transparent)
    gradient = QRadialGradient(diameter / 2, diameter / 2, diameter / 2)
    gradient.setColorAt(0, QColor(255, 255, 0))
    gradient.setColorAt(0.7, QColor(255, 150, 0))
    gradient.setColorAt(1, QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)
    painter.end()
    return pixmap
