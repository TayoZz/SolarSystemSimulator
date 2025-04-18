# planet_worker.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import numpy as np

class WorkerSignals(QObject):
    # Emit: planet object, new simulation state tuple, and update_id (int)
    finished = pyqtSignal(object, object, int)

class PlanetUpdateWorker(QRunnable):
    def __init__(self, planet, planets, simulation_speed, num_steps, fixed_dt, update_id):
        super().__init__()
        self.planet = planet          # The planet to update
        self.planets = planets        # List of all planets (for force calculations)
        self.simulation_speed = simulation_speed
        self.num_steps = num_steps    # Number of physics steps to batch
        self.fixed_dt = fixed_dt
        self.update_id = update_id    # A unique id for this update cycle
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        # Use local copies so that the update is self-contained.
        local_position = np.copy(self.planet.sim_pos)
        local_velocity = np.copy(self.planet.velocity)
        # Loop for a batch of simulation steps.
        for _ in range(self.num_steps):
            dt = self.fixed_dt * self.simulation_speed
            net_force = np.array([0.0, 0.0])
            for other in self.planets:
                if self.planet != other:
                    net_force += self.planet.attraction(other)
            local_acceleration = net_force / self.planet.mass
            local_velocity += local_acceleration * self.planet.TIMESTEP * self.simulation_speed
            local_position += local_velocity * self.planet.TIMESTEP * self.simulation_speed

        # Prepare new simulation state: we update both position and velocity.
        new_state = (local_position, local_velocity)
        # Emit a signal with the updated state and update_id.
        self.signals.finished.emit(self.planet, new_state, self.update_id)
