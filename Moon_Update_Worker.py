# moon_worker.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import numpy as np

class MoonWorkerSignals(QObject):
    finished = pyqtSignal(object, object, int)  # moon, new state (pos and vel), and update_id

class MoonUpdateWorker(QRunnable):
    def __init__(self, moon, simulation_speed, num_steps, fixed_dt, update_id):
        super().__init__()
        self.moon = moon
        self.simulation_speed = simulation_speed
        self.num_steps = num_steps * 20
        self.fixed_dt = fixed_dt
        self.update_id = update_id
        self.signals = MoonWorkerSignals()  # make sure your signals class is defined accordingly

    @pyqtSlot()
    def run(self):
        local_position = np.copy(self.moon.sim_pos)
        local_velocity = np.copy(self.moon.velocity)
        # Perform the batch of simulation steps.
        for _ in range(self.num_steps):
            dt = self.fixed_dt * self.simulation_speed
            net_force = self.moon.attraction(self.moon.planet)
            a_rel = net_force / self.moon.mass
            local_velocity += a_rel * self.moon.TIMESTEP * self.simulation_speed
            local_position += local_velocity * self.moon.TIMESTEP * self.simulation_speed
        new_state = (local_position, local_velocity)
        self.signals.finished.emit(self.moon, new_state, self.update_id)

