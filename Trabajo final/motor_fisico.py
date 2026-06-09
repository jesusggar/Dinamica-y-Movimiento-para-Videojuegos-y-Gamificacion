import numpy as np
import math
from scipy.interpolate import interp1d
import time

class Coche:
    def __init__(self, nombre, rpm_datos, par_datos, relaciones, final_drive, radio_rueda, cd, area_frontal, masa):
        self.nombre = nombre
        self.relaciones = relaciones
        self.final_drive = final_drive
        self.radio_rueda = radio_rueda
        self.cd = cd
        self.area_frontal = area_frontal
        self.masa = masa
        
        # Generamos la curva de par suavizada
        self.interp_par = interp1d(rpm_datos, par_datos, kind='cubic', fill_value="extrapolate")

    def calcular_par(self, rpm):
        return float(self.interp_par(rpm))

    def fuerza_aire(self, v_ms):
        rho = 1.225
        return 0.5 * rho * (v_ms**2) * self.cd * self.area_frontal

    def carga_aerodinamica(self, v_ms):
        # Asumimos un Cl promedio de 0.30 para todos en esta prueba
        rho = 1.225
        cl = 0.30
        return 0.5 * rho * (v_ms**2) * cl * self.area_frontal

    def fuerza_rodadura(self):
        mu_rr = 0.015 
        g = 9.81
        normal = self.masa * g
        return mu_rr * normal

    def fuerza_empuje(self, rpm, marcha):
        if marcha not in self.relaciones:
            return 0.0
        torque_motor = self.calcular_par(rpm)
        eficiencia = 0.88 
        reduccion_total = self.relaciones[marcha] * self.final_drive
        return (torque_motor * reduccion_total * eficiencia) / self.radio_rueda

    def rpm_desde_velocidad(self, v_ms, marcha):
        if marcha not in self.relaciones or v_ms <= 0:
            return 1000.0
        w_rueda = v_ms / self.radio_rueda
        reduccion_total = self.relaciones[marcha] * self.final_drive
        w_motor = w_rueda * reduccion_total
        return (w_motor * 60) / (2 * math.pi)

# ==========================================
# CATÁLOGO DE COCHES
# ==========================================

# 1. Ferrari F430 (Equilibrado)
ferrari = Coche(
    nombre="Ferrari F430 V8",
    rpm_datos = np.array([1000, 2000, 3000, 4000, 5250, 6000, 7000, 8500]),
    par_datos = np.array([320, 370, 415, 445, 465, 455, 440, 390]),
    relaciones = {1: 3.29, 2: 2.16, 3: 1.61, 4: 1.26, 5: 1.03, 6: 0.85},
    final_drive = 4.30,
    radio_rueda = 0.38,
    cd = 0.33,
    area_frontal = 2.03,
    masa = 1450
)

# 2. Ford Mustang Shelby GT500 (Pura fuerza bruta, pesado)
mustang = Coche(
    nombre="Ford Mustang Shelby",
    rpm_datos = np.array([1000, 2000, 3000, 4000, 5000, 6000, 7000]),
    par_datos = np.array([500, 650, 750, 840, 800, 700, 600]), # Par salvaje
    relaciones = {1: 2.66, 2: 1.82, 3: 1.30, 4: 1.00, 5: 0.77, 6: 0.50},
    final_drive = 3.31,
    radio_rueda = 0.40,
    cd = 0.38, # Peor aerodinámica
    area_frontal = 2.30,
    masa = 1850 # Muy pesado
)

# 3. Nissan Skyline GT-R R34 (Ligero, revolucionado, marchas cortas)
skyline = Coche(
    nombre="Nissan Skyline GT-R R34",
    rpm_datos = np.array([1000, 2500, 4000, 5000, 6500, 8000, 9000]),
    par_datos = np.array([200, 280, 350, 392, 380, 320, 280]),
    relaciones = {1: 3.82, 2: 2.36, 3: 1.68, 4: 1.31, 5: 1.00, 6: 0.79}, # Marchas muy cortas
    final_drive = 3.54,
    radio_rueda = 0.35,
    cd = 0.34,
    area_frontal = 2.10,
    masa = 1530 
)

# ==========================================
# BUCLE DE PRUEBA (0 a 100 km/h)
# ==========================================

def simular_0_a_100(coche):
    print(f"\n--- Probando {coche.nombre} ---")
    dt = 1/60
    v_coche = 0
    tiempo = 0
    marcha = 1
    
    while v_coche * 3.6 < 100:
        rpm = coche.rpm_desde_velocidad(v_coche, marcha)
        
        # Cambio automático al corte (simplificado para la prueba)
        if rpm > 8000 and marcha < 6:
            marcha += 1
            rpm = coche.rpm_desde_velocidad(v_coche, marcha)
            print(f"[{tiempo:.2f}s] ¡Cambio a marcha {marcha}!")

        # Si las RPM caen por debajo del ralentí
        rpm = max(rpm, 1000)

        # Físicas
        ft = coche.fuerza_empuje(rpm, marcha)
        fd = coche.fuerza_aire(v_coche)
        fr = coche.fuerza_rodadura()
        
        fuerza_neta = ft - fd - fr
        a_coche = fuerza_neta / coche.masa
        
        v_coche += dt * a_coche
        tiempo += dt

    print(f"¡{coche.nombre} ha alcanzado los 100 km/h en {tiempo:.3f} segundos!\n")

if __name__ == "__main__":
    simular_0_a_100(ferrari)
    simular_0_a_100(mustang)
    simular_0_a_100(skyline)