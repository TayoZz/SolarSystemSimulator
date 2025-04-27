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
from custom_object_class import CustomObject as CustomObject

class SolarSystem(QMainWindow):
    def __init__(self):
        super().__init__()

        self.planets = []
        self.moons = []
        self.custom_objects = []
        self.base_sim_speed = 0.1  # Base multiplier for simulation speed # Small physics timestep in seconds (for accuracy)
        self.simulation_speed = self.base_sim_speed
        self.simulation_days = 0  # Tracks total simulation time in days
        self.years_passed = 0  # Earth years passed in
        self.setup_ui()
        self.initialize_planets()
        self.is_hovering_ui = False
        self.create_stars()
        self.moons_active = True
        self.create_panel_shown = False
        self.nextclick = False
        self.dir_click = False
        self.performance_mode_active = False


        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)


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
        self.timer.start(8)  # alle 8 ms --> max 125 FPS

        self.is_following = False  # Flag to track if following a planet
        self.following_planet = None

        self.ObjectAttributeList = [
            "<html><head/><body><p>Mass: 1.989e30 kg</p><p>Orbitradius: 8.3kpc</p><p>Radius: 695700km</p><p>Surface Gravity: 274 N/kg</p><p>Day (Rotation): 25d (Äquator)</p><p>Year (Revolution): 225 Mio.y</p><p>nat. Satellites: 0</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 3,301e23 kg</p><p>Orbitradius: 5.7e9 km</p><p>Radius: 2440km</p><p>Surface Gravity: 3.7 N/kg</p><p>Day (Rotation): 58d</p><p>Year (Revolution): 88d</p><p>nat. Satellites: 0</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 4.87e24 kg</p><p>Orbitradius: 1.08e11 km</p><p>Radius: 6050 km</p><p>Surface Gravity: 8.87 N/kg</p><p>Day (Rotation): 243d</p><p>Year (Revolution): 224d</p><p>nat. Satellites: 0</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 5.97e24 kg</p><p>Orbitradius: 1.496e8 km</p><p>Radius: 6371 km</p><p>Surface Gravity: 9.81 N/kg</p><p>Day (Rotation): 1d = 24h</p><p>Year (Revolution): 365d</p><p>nat. Satellites: 1 (Moon)</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 6.417e23 kg</p><p>Orbitradius: 2.24e9 km</p><p>Radius: 3396 km</p><p>Surface Gravity: 3.7 N/kg</p><p>Day (Rotation): 1d</p><p>Year (Revolution): 687d</p><p>nat. Satellites: 2 (Phobos, Deimos)</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 1.89e27 kg</p><p>Orbitradius: 7.85e10 km</p><p>Radius: 71490 km</p><p>Surface Gravity: 24.8 N/kg</p><p>Day (Rotation): 9.9h</p><p>Year (Revolution): 12y</p><p>nat. Satellites: 95+</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 5.68e26 kg</p><p>Orbitradius: 1.421e10 km</p><p>Radius: 16238 km</p><p>Surface Gravity: 10.4 N/kg</p><p>Day (Rotation): 10.7h</p><p>Year (Revolution): 29.4y</p><p>nat. Satellites: 274+</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 8.681e25 kg</p><p>Orbitradius: 2.84e9 km</p><p>Radius: 25559km</p><p>Surface Gravity: 8.87 N/kg</p><p>Day (Rotation): 17h</p><p>Year (Revolution): 84d</p><p>nat. Satellites: 25+</p><p><br/></p><p><br/></p></body></html>",
            "<html><head/><body><p>Mass: 1.024e26 kg</p><p>Orbitradius: 4.48e9 km</p><p>Radius: 24787km</p><p>Surface Gravity: 11.15 N/kg</p><p>Day (Rotation): 16</p><p>Year (Revolution): 165y</p><p>nat. Satellites: 16+</p><p><br/></p><p><br/></p></body></html>"]

        self.ObjectNameList = ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]

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

        self.updatePanelStatus(True)

        self.ui_obj.Create_Button.clicked.connect(lambda: self.showCreatePanel(True))
        self.ui_obj.CreateAftertInputButton.clicked.connect(self.click_create)

        self.ui_obj.lineEditName.setMaxLength(15)

        int_validator_mass = QIntValidator(0, 1_000_000_000, self)  # e.g. 0–1M
        self.ui_obj.lineEditName_2.setValidator(int_validator_mass)

        int_validator_size = QIntValidator(0, 999, self)  # e.g. 0–1M
        self.ui_obj.lineEditName_3.setValidator(int_validator_size)

        int_validator_vel = QIntValidator(0, 1_000_000, self)  # e.g. 0–1M
        self.ui_obj.lineEditName_4.setValidator(int_validator_vel)

        self.ui_obj.RerunButton.clicked.connect(lambda: self.rerunSimulation())

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
        self.hover_timer.start(64)  # Update every 32 ms (30 FPS)

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
        if self.following_planet.type == Planet:
            self.updatePanelStatus(False)



    def initialize_planets(self):
        # Add the Sun at the origin
        initial_x, initial_y = 0, 0
        sun = Planet("sun", 1.989e30, self.scene, initial_x, initial_y, 400, "NORMAL", "sun.svg", self)
        self.planets.append(sun)

        self.add_planet("mercury", 3.3011e23, 0.39 + Planet.SCALE / 10000, 0, 80, "SCALE", "mercury.svg", sun)
        self.add_planet("venus", 4.867e24, 0.72 + Planet.SCALE / 10000, 0, 130, "SCALE", "venus.svg", sun)
        self.add_planet("earth", 5.9722e24, 1 + Planet.SCALE / 10000, 0, 150, "SCALE", "earth.svg", sun)
        self.add_planet("mars", 6.417e23, 1.52 + Planet.SCALE / 10000, 0, 130, "SCALE", "mars.svg", sun)
        self.add_planet("jupiter", 1.898e27, 5.2, 0, 180, "HIGHSCALE", "jupiter.svg", sun)
        self.add_planet("saturn", 5.683e26, 9.54, 0, 370, "HIGHSCALE", "saturn.svg", sun) # extra größer weil grafik vergleichsweise kleiner (wegen den ringen)
        self.add_planet("uranus", 8.681e25, 19.22, 0, 340, "HIGHSCALE", "uranus.svg", sun)
        self.add_planet("neptune", 1.024e26, 30.1, 0, 150, "HIGHSCALE", "neptune.svg", sun)

        self.add_moons()


    def add_moons(self) -> object:
        self.add_moon("moon", 7.346e22, 0.0026, 0, 20, "moon.svg", self.planets[3])
        self.add_moon("ganymed", 1.4819e23, 0.0071, 0, 30, "moon.svg", self.planets[5])
        self.add_moon("io", 8.931e22, 0.0028, 0, 25, "moon.svg", self.planets[5])
        self.add_moon("europa", 4.8e22, 0.0045, 0, 18, "moon.svg", self.planets[5])
        self.add_moon("titan", 1.345e23, 0.00817, 0, 28, "moon.svg", self.planets[6])
        self.add_moon("triton", 2.14e22, 0.0024, 0, 18, "moon.svg", self.planets[8])
        self.add_moon("titania", 3.46e21, 0.0018, 0, 20, "moon.svg", self.planets[7])
        self.add_moon("oberon", 3.11e21, 0.0039, 0, 23, "moon.svg", self.planets[7])
        self.add_moon("umbriel", 1.17e21, 0.00178, 0, 15, "moon.svg", self.planets[7])
        self.add_moon("rhea", 2.31e21, 0.0035, 0, 18, "moon.svg", self.planets[6])
        self.add_moon("dione", 1.1e21, 0.0025, 0, 20, "moon.svg", self.planets[6])

        self.moons_active = True

    def add_planet(self, name, mass, x, y, size, scaletype, texture_path, sun):
        planet = Planet(name, mass, self.scene, x, y, size, scaletype, texture_path, self)
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
        self.moons_active = False
        for moon in self.moons:
            self.scene.removeItem(moon)
            self.scene.removeItem(moon.text_item)
        self.moons.clear()

    def create_stars(self):
        for _ in range(12000):
            x = random.randint(-50000, 50000)
            y = random.randint(-50000, 50000)
            size = random.randint(4, 8)
            star = QGraphicsEllipseItem(x, y, size, size)
            star.setBrush(QColor("white"))
            star.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(star)

    def click_create(self):
        self.nextclick = True

    def mousePressEvent(self, event: QMouseEvent):
        if self.dir_click:
            self.getDirectionPosition()
            self.dir_click = False
        if self.nextclick:
            self.nextclick = False
            self.getPosition()
            self.dir_click = True


    def update(self):
        self.update_positions()
        self.base_sim_speed = 1 / (math.sqrt(self.view.zoom_factor))
        if self.ui_obj.CreationModeCheckbox.isChecked():
            self.showNonCreationModeOnly(False)
            if self.moons_active:
                self.remove_moons()
        else:
            self.showNonCreationModeOnly(True)

            self.showCreatePanel(False)
            if not self.moons_active and not self.performance_mode_active:
                self.add_moons()

        self.check_for_warning()

        if self.ui_obj.PerformanceModeCheckbox.isChecked():
            self.performance_mode_active = True
        else:
            self.performance_mode_active = False

        if self.moons_active and self.performance_mode_active:
            self.remove_moons()


    def showNonCreationModeOnly(self, dontshow):
        if dontshow:
            self.ui_obj.Create_Button.hide()
            self.ui_obj.sunButton.show()
            self.ui_obj.mercuryButton.show()
            self.ui_obj.venusButton.show()
            self.ui_obj.earthButton.show()
            self.ui_obj.marsButton.show()
            self.ui_obj.jupiterButton.show()
            self.ui_obj.saturnButton.show()
            self.ui_obj.uranusButton.show()
            self.ui_obj.neptuneButton.show()
        else:
            self.ui_obj.Create_Button.show()
            self.ui_obj.sunButton.hide()
            self.ui_obj.mercuryButton.hide()
            self.ui_obj.venusButton.hide()
            self.ui_obj.earthButton.hide()
            self.ui_obj.marsButton.hide()
            self.ui_obj.jupiterButton.hide()
            self.ui_obj.saturnButton.hide()
            self.ui_obj.uranusButton.hide()
            self.ui_obj.neptuneButton.hide()


    def check_for_warning(self):
        if self.ui_obj.lineEditName_3.text().isdigit() and int(self.ui_obj.lineEditName_3.text()) < 30 or self.ui_obj.lineEditName_2.text().isdigit() and int(self.ui_obj.lineEditName_2.text()) == 0 or self.ui_obj.lineEditName_2.text().isdigit() and int(self.ui_obj.lineEditName_2.text()) > 1000000:
            if self.ui_obj.lineEditName_3.text().isdigit() and int(self.ui_obj.lineEditName_3.text()) < 30:
                self.ui_obj.WarningText.setText("WARNING: Size is very low")
                self.ui_obj.WarningText.setStyleSheet(
                "QLabel { color: yellow; font-size: 20px; font-family: Bahnschrift; }")
            if self.ui_obj.lineEditName_2.text().isdigit() and int(self.ui_obj.lineEditName_2.text()) == 0:
                self.ui_obj.WarningText.setText("WARNING: Mass cant be 0")
                self.ui_obj.WarningText.setStyleSheet(
                    "QLabel { color: red; font-size: 20px; font-family: Bahnschrift; }")
            if self.ui_obj.lineEditName_2.text().isdigit() and int(self.ui_obj.lineEditName_2.text()) > 1000000:
                self.ui_obj.WarningText.setText("WARNING: Mass is extreemly high")
                self.ui_obj.WarningText.setStyleSheet(
                    "QLabel { color: yellow; font-size: 20px; font-family: Bahnschrift; }")

        else:
            self.ui_obj.WarningText.setText("")

    def getDirectionPosition(self):
        self.create_object(self.init_x, self.init_y, self.view.mapToScene(QCursor.pos()).x(), self.view.mapToScene(QCursor.pos()).y())

    def getPosition(self):
        #self.create_object(self.view.mapToScene(QCursor.pos()).x(), self.view.mapToScene(QCursor.pos()).y())
        self.init_x = self.view.mapToScene(QCursor.pos()).x()
        self.init_y = self.view.mapToScene(QCursor.pos()).y()

    def create_object(self, x, y, x_dir, y_dir):
        name_raw = self.ui_obj.lineEditName.text()
        mass_raw = self.ui_obj.lineEditName_2.text()
        size_raw = self.ui_obj.lineEditName_3.text()
        speed_raw = self.ui_obj.lineEditName_4.text()

        if not name_raw.strip() or not mass_raw.strip() or not size_raw.strip() or not speed_raw.strip() or int(mass_raw) == 0:
            return

        name = name_raw
        mass = int(mass_raw) * 1_000_000_000_000_000_000_000_000 #* 10e23
        size = int(size_raw)
        speed = int(speed_raw)

        p1 = np.array([x, y])
        p2 = np.array([x_dir, y_dir])

        # 1) get the vector from p1 to p2
        direction = p2 - p1

        # 2) normalize to a unit vector
        dist = np.linalg.norm(direction)
        if dist == 0:
            unit = np.zeros(2)  # overlapping points: no movement
        else:
            unit = direction / dist

        x = x * (CustomObject.METER_PER_PIXEL / CustomObject.AU)
        y = y * (CustomObject.METER_PER_PIXEL / CustomObject.AU)

        new_object = CustomObject(name, mass, self.scene, x, y, size, "object.svg")


        new_object.velocity = unit * speed
        print(str(new_object.x()))
        self.custom_objects.append(new_object)
        self.scene.addItem(new_object)



    def showCreatePanel(self, show):

        if self.create_panel_shown == True and show == True:
            self.showCreatePanel(False)
        else:
            if show:
                self.ui_obj.listView_2.show()
                self.ui_obj.NameText.show()
                self.ui_obj.MassText.show()
                self.ui_obj.SizeText.show()
                self.ui_obj.VelocityText.show()
                self.ui_obj.lineEditName.show()
                self.ui_obj.lineEditName.clear()
                self.ui_obj.lineEditName_2.show()
                self.ui_obj.lineEditName_2.clear()
                self.ui_obj.lineEditName_3.show()
                self.ui_obj.lineEditName_3.clear()
                self.ui_obj.lineEditName_4.show()
                self.ui_obj.lineEditName_4.clear()
                self.ui_obj.CreateAftertInputButton.show()
                self.ui_obj.WarningText.show()
                self.create_panel_shown = True
            else:
                self.ui_obj.listView_2.hide()
                self.ui_obj.NameText.hide()
                self.ui_obj.MassText.hide()
                self.ui_obj.SizeText.hide()
                self.ui_obj.VelocityText.hide()
                self.ui_obj.lineEditName.hide()
                self.ui_obj.lineEditName_2.hide()
                self.ui_obj.lineEditName_3.hide()
                self.ui_obj.lineEditName_4.hide()
                self.ui_obj.CreateAftertInputButton.hide()
                self.ui_obj.WarningText.hide()
                self.create_panel_shown = False
                for custom_object in self.custom_objects:
                    self.scene.removeItem(custom_object)
                self.custom_objects.clear()



    def update_positions(self):
        # Update simulation speed based on slider (multiplier)

        self.simulation_speed = self.base_sim_speed * self.sliderValues[self.timeSlider.value() + 13]
        self.ui_obj.simulation_speed_text.setText(str(self.sliderValues[self.timeSlider.value() + 13]))

        if self.simulation_speed > 5:
            self.remove_moons()
            self.moons_active = False
        elif not self.moons_active and not self.performance_mode_active:
            self.add_moons()

        fixed_dt = 1 / 120 # Assume 60 updates per second
        physics_update_rate = 3
        for _ in range(physics_update_rate):
            dt = fixed_dt * self.simulation_speed
            for planet in self.planets:
                planet.update_position(self.planets, self.custom_objects, dt)
            for custom_object in self.custom_objects:
                custom_object.update_position(self.planets, self.custom_objects, dt)
            for _ in range(10):
                for moon in self.moons:
                    moon.update_position(dt)

        self.simulation_days += Planet.TIMESTEP / (3600 * 24) * self.simulation_speed / 21.7
        if self.simulation_days >= (self.years_passed + 1) * 365.25:
            self.years_passed += 1
        shown_days = self.simulation_days % 365.25
        self.ui_obj.TimeCounter.setText(f"Simulated Time: {self.years_passed} Years" + f" {int(shown_days)} Days")



        # Follow a planet if enabled
        if self.is_following and self.following_planet:
            if not self.view._panning and self.view.zoom_factor > 0.3:
                self.view.centerOn(self.following_planet.x() + 150 / self.view.zoom_factor,
                                   self.following_planet.y())
                if self.following_planet.type == Planet:
                    self.updateInfoText(self.planets.index(self.following_planet), self.following_planet)
                #else:
                    #self.updateInfoText(self.moons.index(self.following_planet), self.following_planet)
                #print(str(self.planets.index(self.following_planet)))
            else:
                self.is_following = False
                self.following_planet = None
                self.updatePanelStatus(True)

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

    def rerunSimulation(self):
        self.close()
        window = SolarSystem()
        window.show()

    def updateInfoText(self, index, following_planet):
        self.ui_obj.ObjectAttributeLabel.setText(self.ObjectAttributeList[index])
        self.ui_obj.ObjectNameLabel.setText(self.ObjectNameList[index])
        if following_planet.name == "sun":
            self.ui_obj.ObjectTypeLabel.setText("Star")
        elif following_planet.type == Planet:
            self.ui_obj.ObjectTypeLabel.setText("Planet")
        elif following_planet.type == Moon:
            self.ui_obj.ObjectTypeLabel.setText("Moon")

    def updatePanelStatus(self, hide):
        if hide:
            self.ui_obj.ObjectNameLabel.hide()
            self.ui_obj.ObjectAttributeLabel.hide()
            self.ui_obj.ObjectTypeLabel.hide()
            self.ui_obj.listView.hide()
        else:
            self.ui_obj.ObjectNameLabel.show()
            self.ui_obj.ObjectAttributeLabel.show()
            self.ui_obj.ObjectTypeLabel.show()
            self.ui_obj.listView.show()

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
        self.focus_timer.start(64)  # roughly 60 updates per second

    def updateFocusStates(self):
        # Get the center of the viewport in scene coordinates
        scene_center = self.mapToScene(self.viewport().rect().center())

        # Define a threshold distance (in scene coordinates) for what counts as "focused"
        focus_threshold = 300  # Example: adjust based on zoom behavior
        focused_objects = []

        scene_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        # Iterate through planets (assuming they are stored in the main window)
        for planet in self.window().planets:
            if not scene_rect.intersects(planet.sceneBoundingRect()):
                planet.setFocusState(False)
                continue
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
            if not scene_rect.intersects(moon.sceneBoundingRect()):
                moon.setFocusState(False)
                continue
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

        for custom_object in self.window().custom_objects:
            if not scene_rect.intersects(custom_object.sceneBoundingRect()):
                custom_object.setFocusState(False)
                continue
            dx = custom_object.x() - (scene_center.x() - 350)
            dy = custom_object.y() - scene_center.y()
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < (focus_threshold * 2) and self.zoom_factor > 1:
                custom_object.distance = distance
                focused_objects.append(custom_object)
                custom_object.setFocusState(True)
            elif custom_object.hover_state == True and self.zoom_factor > 0.8:
                custom_object.setFocusState(True)
                custom_object.distance = distance
                focused_objects.append(custom_object)
            else:
                custom_object.setFocusState(False)

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
        if event.button() == Qt.MouseButton.MiddleButton:
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
            for custom_object in self.window().custom_objects:
                if hasattr(custom_object, 'hover_state') and custom_object.hover_state:
                    self.window().start_follow_planet(custom_object)
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

        for custom_object in self.window().custom_objects:
            # Get the planet's center position (if planet.pos() returns its center)
            custom_object_center = custom_object.pos()  # Adjust if needed based on your Planet implementation

            # Calculate Euclidean distance between the mouse and the planet center
            dx = scene_pos.x() - custom_object_center.x()
            dy = scene_pos.y() - custom_object_center.y()
            distance = math.hypot(dx, dy)

            # Define a tolerance (e.g., half the planet's bounding rect width plus extra margin)
            # You might store the planet's radius as an attribute or calculate it from the bounding rect.
            custom_object_radius = custom_object.boundingRect().width() / 2
            tolerance = custom_object_radius  # 20 pixels extra margin

            # Check if the mouse is near the planet
            if distance <= tolerance:
                # For example, update a hover state on the planet
                custom_object.setHoverState(True)
            else:
                custom_object.setHoverState(False)

        if self._panning and self._last_mouse_pos:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
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
