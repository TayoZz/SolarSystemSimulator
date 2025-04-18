# main.py

import sys, time
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtOpenGLWidgets import *
import random
import numpy as np
import math
from overlay import Ui_Overlay as ui
from Moon import Moon
from planet_class import PlanetObject as Planet
from Planet_Update_Worker import PlanetUpdateWorker
from Moon_Update_Worker import MoonUpdateWorker

class SolarSystem(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showMaximized()
        self.planets = []
        self.moons = []
        self.base_sim_speed = 0.1  # Base multiplier for simulation speed # Small physics timestep in seconds (for accuracy)
        self.simulation_speed = self.base_sim_speed
        self.setup_ui()
        self.initialize_planets()
        self.is_hovering_ui = False
        self.create_stars()
        self.moons_active = True
        self.thread_pool = QThreadPool.globalInstance()

        # Physics configuration
          # Actual simulation speed multiplier (adjustable via slider)

        # Timing for update loop and FPS calculation
        self.last_update_time = time.time()  # For physics accumulator
        self.last_frame_time = time.time()     # For FPS calculation
        self.fps_counter = 0
        self.fps_accumulator = 0.0

        # Timer for animation (rendering updates)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # Attempt ~60 FPS (or as fast as possible)

        self.is_following = False  # Flag to track if following a planet
        self.following_planet = None

        self.ObjectAttributeList = ["<html><head/><body><p>Mass: 3,301e23 kg</p><p>Orbitradius: 5.7e9 km</p><p>Radius: 2440km</p><p>Surface Gravity: 3.7 N/kg</p><p>Day (Rotation): 58d</p><p>Year (Revolution): 88d</p><p>nat. Satellites: 0</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 4.87e24 kg</p><p>Orbitradius: 1.08e11 km</p><p>Radius: 6050 km</p><p>Surface Gravity: 8.87 N/kg</p><p>Day (Rotation): 243d</p><p>Year (Revolution): 224d</p><p>nat. Satellites: 0</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 5.97e24 kg</p><p>Orbitradius: 1.496e8 km</p><p>Radius: 6371 km</p><p>Surface Gravity: 9.81 N/kg</p><p>Day (Rotation): 1d = 24h</p><p>Year (Revolution): 365d</p><p>nat. Satellites: 1 (Moon)</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 6.417e23 kg</p><p>Orbitradius: 2.24e9 km</p><p>Radius: 3396 km</p><p>Surface Gravity: 3.7 N/kg</p><p>Day (Rotation): 1d</p><p>Year (Revolution): 687d</p><p>nat. Satellites: 2 (Phobos, Deimos)</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 1.89e27 kg</p><p>Orbitradius: 7.85e10 km</p><p>Radius: 71490 km</p><p>Surface Gravity: 24.8 N/kg</p><p>Day (Rotation): 9.9h</p><p>Year (Revolution): 12y</p><p>nat. Satellites: 95+</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 5.68e26 kg</p><p>Orbitradius: 1.421e10 km</p><p>Radius: 16238 km</p><p>Surface Gravity: 10.4 N/kg</p><p>Day (Rotation): 10.7h</p><p>Year (Revolution): 29.4y</p><p>nat. Satellites: 274+</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 8.681e25 kg</p><p>Orbitradius: 2.84e9 km</p><p>Radius: 25559km</p><p>Surface Gravity: 8.87 N/kg</p><p>Day (Rotation): 17h</p><p>Year (Revolution): 84d</p><p>nat. Satellites: 25+</p><p><br/></p><p><br/></p></body></html>", "<html><head/><body><p>Mass: 1.024e26 kg</p><p>Orbitradius: 4.48e9 km</p><p>Radius: 24787km</p><p>Surface Gravity: 11.15 N/kg</p><p>Day (Rotation): 16</p><p>Year (Revolution): 165y</p><p>nat. Satellites: 16+</p><p><br/></p><p><br/></p></body></html>"]

    def setup_ui(self):
        self.setWindowTitle("Solar System Simulation")
        self.showFullScreen()

        # Create a central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Graphics scene and view
        self.scene = QGraphicsScene(-50000, -50000, 100000, 100000)
        self.scene.setBackgroundBrush(QColor("#000008"))
        self.view = ZoomableView(self.scene, self)
        self.view.setViewport(QOpenGLWidget())
        self.view.setStyleSheet("border: none;")
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(self.view)

        # UI overlay from Designer
        self.ui_overlay = QWidget(central_widget)
        self.ui_obj = ui()  # Instantiate your Designer UI class
        self.ui_obj.setupUi(self.ui_overlay)
        self.ui_overlay.setGeometry(0, 0, self.width(), self.height())
        self.ui_overlay.raise_()

        # Connect planet-following buttons
        self.ui_obj.sunButton.clicked.connect(lambda: self.start_follow_planet(self.planets[0]))
        self.ui_obj.mercuryButton.clicked.connect(lambda: self.start_follow_planet(self.planets[1]))
        self.ui_obj.venusButton.clicked.connect(lambda: self.start_follow_planet(self.planets[2]))
        self.ui_obj.earthButton.clicked.connect(lambda: self.start_follow_planet(self.planets[3]))
        self.ui_obj.marsButton.clicked.connect(lambda: self.start_follow_planet(self.planets[4]))
        self.ui_obj.jupiterButton.clicked.connect(lambda: self.start_follow_planet(self.planets[5]))
        self.ui_obj.saturnButton.clicked.connect(lambda: self.start_follow_planet(self.planets[6]))
        self.ui_obj.uranusButton.clicked.connect(lambda: self.start_follow_planet(self.planets[7]))
        self.ui_obj.neptuneButton.clicked.connect(lambda: self.start_follow_planet(self.planets[8]))



        # Slider for simulation speed
        self.sliderValues = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1,
                             1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30]
        self.timeSlider = self.ui_obj.timeSlider
        self.timeSlider.setMinimum(-13)
        self.timeSlider.setMaximum(13)
        self.timeSlider.setValue(0)

        self.ui_obj.simulation_speed_text.setText(str(self.simulation_speed))

        # FPS text display from UI
        self.fps_text = self.ui_obj.fps_text

        # Hover timer to update UI interactivity
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self.update_hover_status)
        self.hover_timer.start(16)

    def update_hover_status(self):
        cursor_pos = QCursor.pos()
        hovering = False
        for widget in self.ui_overlay.findChildren(QWidget):
            if not widget.isVisible():
                continue
            global_rect = QRect(widget.mapToGlobal(widget.rect().topLeft()), widget.size())
            if global_rect.contains(cursor_pos):
                hovering = True
                break
        self.is_hovering_ui = hovering
        if self.is_hovering_ui:
            self.ui_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        else:
            self.ui_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'ui_overlay'):
            self.ui_overlay.setGeometry(self.centralWidget().rect())

    def start_follow_planet(self, planet):
        if self.view.zoom_factor < 1.0:
            self.view.zoom_factor = 1.0
        self.view.resetTransform()
        self.is_following = True
        self.following_planet = planet
        self.follow_planet(planet)

    def follow_planet(self, planet):
        self.view.centerOn(planet)

    def initialize_planets(self):
        # Add the Sun at the origin
        initial_x, initial_y = 0, 0
        sun = Planet("sun", 1.989e30, self.scene, initial_x, initial_y, 400, "NORMAL", "sun.svg")
        self.planets.append(sun)

        self.add_planet("mercury", 3.3011e23, 0.39 + Planet.SCALE / 10000, 0, 80, "SCALE", "mercury.svg", sun)
        self.add_planet("venus", 4.867e24, 0.72 + Planet.SCALE / 10000, 0, 130, "SCALE", "venus.svg", sun)
        self.add_planet("earth", 5.9722e24, 1 + Planet.SCALE / 10000, 0, 150, "SCALE", "earth.svg", sun)
        self.add_planet("mars", 6.417e23, 1.52 + Planet.SCALE / 10000, 0, 130, "SCALE", "mars.svg", sun)
        self.add_planet("jupiter", 1.898e27, 5.2, 0, 180, "HIGHSCALE", "jupiter.svg", sun)
        self.add_planet("saturn", 5.683e26, 9.54, 0, 370, "HIGHSCALE", "saturn.svg", sun) # extra größer weil grafik vergleichsweise kleiner (wegen den ringen)
        self.add_planet("uranus", 8.681e25, 19.22, 0, 340, "HIGHSCALE", "uranus.svg", sun)
        self.add_planet("neptune", 1.024e26, 30.1, 0, 150, "HIGHSCALE", "neptune.svg", sun)
        #self.add_planet("pluto", 1.3e22, 35, 0, 60, "HIGHSCALE", "mercury.svg", sun)
        #self.add_planet("charon", 1.586e21, 35.00013369174, 0, 50, "HIGHSCALE", "mercury.svg", sun)

        self.add_moons()


    def add_moons(self):
        self.add_moon("moon", 7.346e22, 0.002694, 0, 20, "moon.svg", self.planets[3])
        self.add_moon("ganymed", 1.4819e23, 0.00714782901, 0, 30, "moon.svg", self.planets[5])
        self.add_moon("io", 8.931e22, 0.0028195588481728, 0, 25, "moon.svg", self.planets[5])
        self.add_moon("europa", 4.8e22, 0.004486026417754, 0, 18, "moon.svg", self.planets[5])
        self.add_moon("titan", 1.345e23, 0.00816742908360125, 0, 28, "moon.svg", self.planets[6])
        """
        self.add_moon("triton", 2.14e22, 0.00237, 0, 14, "moon.svg", self.planets[8])  # Neptune
        self.add_moon("rhea", 2.31e21, 0.0014, 0, 80, "moon.svg", self.planets[6])  # Saturn
        self.add_moon("oberon", 3.01e21, 0.0014, 0, 70, "moon.svg", self.planets[7])  # Uranus
        self.add_moon("iapetus", 1.81e21, 0.00356, 0, 90, "moon.svg", self.planets[6])  # Saturn
        self.add_moon("dione", 1.1e21, 0.00152, 0, 60, "moon.svg", self.planets[6])  # Saturn
        self.add_moon("tethys", 6.17e20, 0.00122, 0, 50, "moon.svg", self.planets[6])  # Saturn
        self.add_moon("enceladus", 1.08e20, 0.0006, 0, 40, "moon.svg", self.planets[6])  # Saturn
        self.add_moon("ariel", 1.35e21, 0.00191, 0, 70, "moon.svg", self.planets[7])  # Uranus
        self.add_moon("miranda", 6.4e19, 0.00129, 0, 30, "moon.svg", self.planets[7])  # Uranus
        self.add_moon("phobos", 1.08e16, 0.00006, 0, 20, "moon.svg", self.planets[4])  # Mars
        self.add_moon("deimos", 2.0e15, 0.00023, 0, 10, "moon.svg", self.planets[4])  # Mars
        """
        self.moons_active = True

    def add_planet(self, name, mass, x, y, size, scaletype, texture_path, sun):
        planet = Planet(name, mass, self.scene, x, y, size, scaletype, texture_path)
        sun_radius_AU = sun.size / Planet.SCALE
        effective_distance_AU = x + sun_radius_AU
        effective_distance_pixels = effective_distance_AU * Planet.SCALE
        planet.setPos(effective_distance_pixels, 0)

        # Compute orbital velocity around the Sun (using pixels-to-meters conversion)
        r_pixels = np.linalg.norm(np.array([planet.x() - sun.x(), planet.y() - sun.y()]))
        r_meters = r_pixels * Planet.METER_PER_PIXEL
        orbital_velocity = math.sqrt(Planet.G * sun.mass / r_meters)
        radial_vector = np.array([planet.x() - sun.x(), planet.y() - sun.y()])
        radial_unit = radial_vector / np.linalg.norm(radial_vector)
        tangential_unit = np.array([-radial_unit[1], radial_unit[0]])
        planet.velocity = orbital_velocity * tangential_unit

        self.planets.append(planet)

    def add_moon(self, name, mass, x, y, size, texture_path, planet):
        moon = Moon(name, mass, self.scene, x, y, size, texture_path, planet)
        # x and y are given in AU relative to the planet
        moon.sim_pos = planet.sim_pos + np.array([x * moon.AU, y * moon.AU])
        moon.rel_pos = np.array([x * moon.AU, y * moon.AU])
        moon.setPos(moon.sim_pos[0] / moon.METER_PER_PIXEL, moon.sim_pos[1] / moon.METER_PER_PIXEL)
        r_meters = np.linalg.norm(moon.rel_pos)
        orbital_velocity = math.sqrt(moon.G * planet.mass / r_meters)
        radial_unit = moon.rel_pos / np.linalg.norm(moon.rel_pos)
        tangential_unit = np.array([-radial_unit[1], radial_unit[0]])
        moon.rel_velocity = orbital_velocity * tangential_unit
        moon.velocity = planet.velocity + moon.rel_velocity
        self.moons.append(moon)

    def remove_moons(self):
        for moon in self.moons:
            self.scene.removeItem(moon)
            self.scene.removeItem(moon.text_item)
        self.moons.clear()

    def create_stars(self):
        for _ in range(10000):
            x = random.randint(-50000, 50000)
            y = random.randint(-50000, 50000)
            size = random.randint(5, 8)
            star = QGraphicsEllipseItem(x, y, size, size)
            star.setBrush(QColor("white"))
            star.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(star)

    def update(self):
        self.update_positions()
        self.base_sim_speed = 1 / (math.sqrt(self.view.zoom_factor)) / 10

    @pyqtSlot(object, object, int)
    def on_planet_updated(self, planet, new_state, update_id):
        # Only update if update_id matches planet's current_update_id:
        if update_id != planet.current_update_id:
            return  # Outdated update; ignore it.
        new_position, new_velocity = new_state
        # Update the planet's simulation state:
        planet.sim_pos = new_position
        planet.velocity = new_velocity

        # Compute the new on-screen position (example for SCALE type):
        screen_pos = QPointF(new_position[0] / planet.METER_PER_PIXEL,
                             new_position[1] / planet.METER_PER_PIXEL)
        planet.updatePosition(screen_pos)
        planet.update()

        if self.is_following and self.following_planet:
            if not self.view._panning and self.view.zoom_factor > 0.3:
                self.view.centerOn(self.following_planet.x() + 350 / self.view.zoom_factor,
                                   self.following_planet.y())
                if self.following_planet.type == Planet:
                    self.updateInfoText(self.planets.index(self.following_planet) - 1)
            else:
                self.is_following = False
                self.following_planet = None

    @pyqtSlot(object, object, int)
    def on_moon_updated(self, moon, new_state, update_id):
        if update_id != moon.current_update_id:
            return
        new_position, new_velocity = new_state
        moon.sim_pos = new_position
        moon.velocity = new_velocity
        # Compute the new on-screen position for the moon here.
        # (Assuming similar scaling logic as before.)
        screen_pos = QPointF(new_position[0] / moon.METER_PER_PIXEL,
                             new_position[1] / moon.METER_PER_PIXEL)
        moon.updatePosition(screen_pos)
        moon.update()

    def update_positions(self):
        # Update simulation speed based on slider (multiplier)
        self.simulation_speed = self.base_sim_speed * self.sliderValues[self.timeSlider.value() + 13]
        self.ui_obj.simulation_speed_text.setText(str(self.sliderValues[self.timeSlider.value() + 13]))

        if self.simulation_speed > 5:
            self.remove_moons()
            self.moons_active = False
        elif not self.moons_active:
            self.add_moons()

        fixed_dt = 1 / 60 # Assume 60 updates per second
        physics_update_rate = 5
        dt = fixed_dt * self.simulation_speed

        for planet in self.planets:
            # Increment the update id for this planet.
            if not hasattr(planet, 'current_update_id'):
                planet.current_update_id = 0
            else:
                planet.current_update_id += 1

            worker = PlanetUpdateWorker(planet, self.planets, self.simulation_speed,physics_update_rate, fixed_dt, planet.current_update_id)
            worker.signals.finished.connect(self.on_planet_updated)
            self.thread_pool.start(worker)

            # Moon updates: (similar approach if needed; here add an update_id for moons too)
        for moon in self.moons:
            if not hasattr(moon, 'current_update_id'):
                moon.current_update_id = 0
            else:
                moon.current_update_id += 1

            worker = MoonUpdateWorker(moon, self.simulation_speed, physics_update_rate, fixed_dt, moon.current_update_id)
            worker.signals.finished.connect(self.on_moon_updated)
            self.thread_pool.start(worker)

        # Follow a planet if enabled
        """
        if self.is_following and self.following_planet:
            if not self.view._panning and self.view.zoom_factor > 0.3:
                self.view.centerOn(self.following_planet.x() + 350 / self.view.zoom_factor,
                                   self.following_planet.y())
                if self.following_planet.type == Planet:
                    self.updateInfoText(self.planets.index(self.following_planet) - 1)
            else:
                self.is_following = False
                self.following_planet = None"""

        # FPS Calculation
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        self.fps_counter += 1
        self.fps_accumulator += dt
        if self.fps_accumulator >= 1.0:
            fps = int(round(self.fps_counter / self.fps_accumulator))
            self.fps_text.setText("FPS: " + str(fps))
            self.fps_counter = 0
            self.fps_accumulator = 0.0

    def updateInfoText(self, index):
        self.ui_obj.ObjectAttributeLabel.setText(self.ObjectAttributeList[index])

class ZoomableView(QGraphicsView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.zoom_factor = 1.0
        self._panning = False
        self._last_mouse_pos = None
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.updateFocusStates)
        self.focus_timer.start(32)  # roughly 60 updates per second

    def updateFocusStates(self):
        # Get the center of the viewport in scene coordinates
        scene_center = self.mapToScene(self.viewport().rect().center())

        # Define a threshold distance (in scene coordinates) for what counts as "focused"
        focus_threshold = 300  # Example: adjust based on zoom behavior
        focused_objects = []

        # Iterate through planets (assuming they are stored in the main window)
        for planet in self.window().planets:
            dx = planet.x() - (scene_center.x() - 350)
            dy = planet.y() - scene_center.y()
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if planet.scaletype == "HIGHSCALE":
                focus_threshold *= 2

            if distance < focus_threshold and self.zoom_factor > 0.8:
                planet.setFocusState(True)
                planet.distance = distance
                focused_objects.append(planet)
            elif planet.hover_state == True and self.zoom_factor > 0.4:
                planet.setFocusState(True)
                planet.distance = distance
                focused_objects.append(planet)
            else:
                planet.setFocusState(False)

            if planet.scaletype == "HIGHSCALE":
                focus_threshold /= 2

        # Iterate through moons
        for moon in self.window().moons:
            dx = moon.x() - (scene_center.x() - 350)
            dy = moon.y() - scene_center.y()
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < (focus_threshold * 2) and self.zoom_factor > 1:
                moon.distance = distance
                focused_objects.append(moon)
                moon.setFocusState(True)
            elif moon.hover_state == True and self.zoom_factor > 0.8:
                moon.setFocusState(True)
                moon.distance = distance
                focused_objects.append(moon)
            else:
                moon.setFocusState(False)

        # Ensure only the closest object remains focused
        if len(focused_objects) > 1:
            for obj in focused_objects:
                obj.setFocusState(True)

    def wheelEvent(self, event: QWheelEvent):
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            if self.zoom_factor <= 3:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = 1
        else:
            if self.zoom_factor >= 0.04:
                zoom_factor = zoom_out_factor
            else:
                zoom_factor = 1
        self.scale(zoom_factor, zoom_factor)
        self.zoom_factor *= zoom_factor

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self._panning = True
            self._last_mouse_pos = event.pos()
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            # Check if any planet is hovered (assuming each planet has a "hover_state" attribute)
            for planet in self.window().planets:
                if hasattr(planet, 'hover_state') and planet.hover_state:
                    self.window().start_follow_planet(planet)
                    event.accept()
                    return  # Stop processing after following one planet
            for moon in self.window().moons:
                if hasattr(moon, 'hover_state') and moon.hover_state:
                    self.window().start_follow_planet(moon)
                    event.accept()
                    return  # Stop processing after following one planet
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        scene_pos = self.mapToScene(event.pos())

        for planet in self.window().planets:
            # Get the planet's center position (if planet.pos() returns its center)
            planet_center = planet.pos()  # Adjust if needed based on your Planet implementation

            # Calculate Euclidean distance between the mouse and the planet center
            dx = scene_pos.x() - planet_center.x()
            dy = scene_pos.y() - planet_center.y()
            distance = math.hypot(dx, dy)

            # Define a tolerance (e.g., half the planet's bounding rect width plus extra margin)
            # You might store the planet's radius as an attribute or calculate it from the bounding rect.
            planet_radius = planet.boundingRect().width() / 2
            tolerance = planet_radius  # 20 pixels extra margin

            # Check if the mouse is near the planet
            if distance <= tolerance:
                # For example, update a hover state on the planet
                planet.setHoverState(True)
            else:
                planet.setHoverState(False)

        for moon in self.window().moons:
            # Get the planet's center position (if planet.pos() returns its center)
            moon_center = moon.pos()  # Adjust if needed based on your Planet implementation

            # Calculate Euclidean distance between the mouse and the planet center
            dx = scene_pos.x() - moon_center.x()
            dy = scene_pos.y() - moon_center.y()
            distance = math.hypot(dx, dy)

            # Define a tolerance (e.g., half the planet's bounding rect width plus extra margin)
            # You might store the planet's radius as an attribute or calculate it from the bounding rect.
            moon_radius = moon.boundingRect().width() / 2
            tolerance = moon_radius  # 20 pixels extra margin

            # Check if the mouse is near the planet
            if distance <= tolerance:
                # For example, update a hover state on the planet
                moon.setHoverState(True)
            else:
                moon.setHoverState(False)

        if self._panning and self._last_mouse_pos:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SolarSystem()
    window.show()
    sys.exit(app.exec())