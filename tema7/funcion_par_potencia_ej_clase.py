import numpy as np
from scipy.interpolate import interp1d

def par_potencia_ferrari_f430(rpm_consulta):
	"""
	Calcula el par motor (Nm) y la potencia (CV) del Ferrari F430 para unas RPM dadas.
	Utiliza interpolación de spline cúbica basada en datos técnicos reales.
	"""
	# Datos maestros del Ferrari F430 V8
	rpm_datos = np.array([1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5250, 5500, 6000, 6500, 7000, 7500, 8000, 8500])
	par_datos = np.array([320, 345, 370, 400, 415, 430, 445, 455, 465, 465, 460, 455, 450, 440, 430, 415, 390])

	# Creamos la función de interpolación (spline cúbica)
	# Esto permite que la curva sea suave: T = f(RPM)
	interp_par = interp1d(rpm_datos, par_datos, kind='cubic', fill_value="extrapolate")

	# 1. Calculamos el Par (T) para la consulta
	par = float(interp_par(rpm_consulta))

	# 2. Calculamos la Potencia (P) en CV
	# Aplicamos la relación física: P = (T * omega) / 735.5
	# Donde omega = (RPM * 2 * pi) / 60
	# Simplificando: P(CV) \simeq \dfrac{T \cdot RPM}{7023}
	potencia = (par * rpm_consulta * 2 * np.pi) / (60 * 735.5)

	return par, potencia

# Nueva función: calcula el par en rueda según la marcha
def calcular_par_por_marcha(rpm_consulta, marcha, relaciones=None, diferencial=4.30, eficiencia=0.88):
	"""
	Devuelve una tupla (par_motor_Nm, par_en_rueda_Nm) para unas RPM y una marcha dada.

	- `marcha`: entero 1..N (índice 1-based)
	- `relaciones`: lista de relaciones de caja por marcha (por defecto valores ejemplo de 6 marchas)
	- `diferencial`: relación del eje final (por defecto 3.30)
	- `eficiencia`: eficiencia de transmisión (por defecto 0.95)

	Si la marcha está fuera de rango se lanzará `IndexError`.
	"""
	if relaciones is None:
		# Relaciones reales proporcionadas por el usuario:
		# marchas 1..6 y marcha atrás al final
		relaciones = [3.29, 2.16, 1.61, 1.27, 1.03, 0.82, 2.73]

	# Si marcha == 0 -> neutra: no hay par transmitido a rueda
	par_motor, potencia = par_potencia_ferrari_f430(rpm_consulta)
	if marcha == 0:
		return par_motor, 0.0

	if marcha < 0 or marcha > len(relaciones):
		raise IndexError(f"Marcha inválida: {marcha}. Debe estar entre 0 y {len(relaciones)}")
	relacion_marcha = relaciones[marcha - 1]

	# Par en rueda = par_motor * relación_marcha * diferencial * eficiencia
	par_rueda = par_motor * relacion_marcha * diferencial * eficiencia

	return par_motor, par_rueda

# Ejemplo de uso:
if __name__ == "__main__":
	revs = 5250
	t, p = par_potencia_ferrari_f430(revs)
	print(f"A {revs} RPM:")
	print(f"\tPar Motor: {t:.2f} Nm")
	print(f"\tPotencia: {p:.2f} CV")

	# Ejemplo: calcular par en rueda para la marcha 3 (por defecto relaciones de ejemplo)
	marcha = 3
	par_motor, par_rueda = calcular_par_por_marcha(revs, marcha)
	print(f"\nPara la marcha {marcha}:")
	print(f"\tPar en rueda: {par_rueda:.2f} Nm (par motor {par_motor:.2f} Nm)")

	# Ejemplo adicional: marcha atrás (última posición)
	marcha_atras = len([3.29, 2.16, 1.61, 1.27, 1.03, 0.82, 2.73])
	par_motor, par_rueda = calcular_par_por_marcha(revs, marcha_atras)
	print(f"\nPara la marcha {marcha_atras} (atrás):")
	print(f"\tPar en rueda: {par_rueda:.2f} Nm (par motor {par_motor:.2f} Nm)")
