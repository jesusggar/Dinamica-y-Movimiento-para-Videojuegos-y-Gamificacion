"""Ejercicio: bola de bolos con rozamiento.

Se implementan exactamente los apartados del enunciado:
1) Fórmulas teóricas (caso ideal).
2) Simulación ideal con Pymunk mostrando t, v, w y estado.
3) Simulación con efectos más reales y comparación con el caso ideal.
"""

import math
import pygame
import pymunk
import pymunk.pygame_util


# =========================
# PARÁMETROS (datos realistas)
# =========================
MASA_KG = 7.26          # Bola de bolos estándar (máx reglamentaria)
RADIO_CM = 10.85        # Diámetro ~21.7 cm
GRAVEDAD_CM = 981.0     # 9.81 m/s^2 en cm/s^2
V0_CM_S = 600.0         # ~6 m/s, permite ver rodadura pura antes del final de pista


# Caso ideal (apartado 1 y 2)
MU_IDEAL = 0.08
OMEGA0_IDEAL = 0.0      # lanzamiento sin giro inicial
K_IDEAL = 2.0 / 5.0     # esfera maciza uniforme


# Caso realista (apartado 3)
MU_INICIO = 0.03        # pista aceitada al principio
MU_FINAL = 0.12         # más agarre al final
X_CAMBIO_MU = 900.0     # cm: cambio de coeficiente a mitad-final
K_REAL = 0.36           # I = k m R^2 (núcleo no uniforme)
OMEGA0_REAL = -30.0     # jugadores lanzan con spin (rad/s)
C_RODADURA = 0.0015     # rozamiento de rodadura (coef. pequeño)


# Pantalla
ANCHO = 1500
ALTO = 450
FPS = 60
DT = 1.0 / FPS
ESPERA_INICIAL_S = 1.2
TOL_U_RODADURA = 1.0   # cm/s, tolerancia numerica para u = v + wR


def formulas_rodadura(masa, radio, mu, g, v0, omega0, k):
	"""Devuelve t* y estado al inicio de rodadura pura para el modelo ideal.

	Modelo durante deslizamiento:
	- F_t = -mu * m * g * sign(u), con u = v + w R
	- dv/dt = F_t / m
	- dw/dt = (R * F_t) / I, I = k m R^2

	Rodadura pura cuando u = v + w R = 0.
	"""
	_ = masa  # masa se cancela en las fórmulas ideales
	u0 = v0 + omega0 * radio

	if abs(u0) < 1e-12:
		return {
			"u0": u0,
			"t_rod": 0.0,
			"v_rod": v0,
			"w_rod": omega0,
		}

	# |du/dt| = mu g (1 + 1/k)
	du_dt_mag = mu * g * (1.0 + 1.0 / k)
	t_rod = abs(u0) / du_dt_mag

	signo = 1.0 if u0 > 0 else -1.0
	a = -mu * g * signo
	alpha = -(mu * g / (k * radio)) * signo

	v_rod = v0 + a * t_rod
	w_rod = omega0 + alpha * t_rod

	return {
		"u0": u0,
		"t_rod": t_rod,
		"v_rod": v_rod,
		"w_rod": w_rod,
	}


def imprimir_apartado_1():
	"""Muestra la explicación física y resultados del apartado 1."""
	res = formulas_rodadura(
		masa=MASA_KG,
		radio=RADIO_CM,
		mu=MU_IDEAL,
		g=GRAVEDAD_CM,
		v0=V0_CM_S,
		omega0=OMEGA0_IDEAL,
		k=K_IDEAL,
	)

	print("\n=== APARTADO 1: MODELO TEORICO (IDEAL) ===")
	print("Hipotesis:")
	print("- Bola esferica maciza uniforme: I = (2/5) m R^2")
	print("- Plano horizontal")
	print("- Rozamiento cinetico constante mu")
	print("- Sin rozamiento de rodadura ni resistencia del aire")
	print("- Mientras desliza: u = v + wR != 0")
	print("- Rodadura pura cuando: v + wR = 0")

	print("\nExpresiones generales (k = I/(mR^2)):")
	print("u0 = v0 + w0*R")
	print("t_rod = |u0| / [mu*g*(1 + 1/k)]")
	print("v_rod = v0 - sign(u0)*mu*g*t_rod")
	print("w_rod = w0 - sign(u0)*(mu*g/(kR))*t_rod")

	print("\nPara esfera maciza (k=2/5) y w0=0:")
	print("t_rod = 2*V0/(7*mu*g)")
	print("v_rod = 5*V0/7")

	print("\nValores numericos (ideal):")
	print(f"t_rod_teorico = {res['t_rod']:.3f} s")
	print(f"v_rod_teorica = {res['v_rod']:.3f} cm/s ({res['v_rod']/100:.3f} m/s)")
	print(f"w_rod_teorica = {res['w_rod']:.3f} rad/s")

	return res


def setup_simulation():
	"""Crea espacio físico horizontal y bola, siguiendo la idea del ejemplo de clase."""
	space = pymunk.Space()
	# La dinamica del ejercicio se integra manualmente (1D), sin fuerzas del motor.
	space.gravity = (0.0, 0.0)

	# Suelo horizontal
	y_suelo = ALTO - 90
	x_ini = 40
	x_fin = ANCHO - 40
	suelo = pymunk.Segment(space.static_body, (x_ini, y_suelo), (x_fin, y_suelo), 6)
	suelo.friction = 1.0
	space.add(suelo)

	return space, suelo, y_suelo, x_ini, x_fin


def crear_bola(space, y_suelo, k_inercia, v0, omega0):
	"""Crea bola con momento de inercia configurable: I = k m R^2."""
	momento = k_inercia * MASA_KG * (RADIO_CM ** 2)
	body = pymunk.Body(MASA_KG, momento)
	body.position = (130.0, y_suelo - RADIO_CM)
	body.velocity = (v0, 0.0)
	body.angular_velocity = omega0

	shape = pymunk.Circle(body, RADIO_CM)
	shape.friction = 0.0
	space.add(body, shape)

	return body


def actualizar_dinamica_manual(body, modo, t):
	"""Aplica la dinámica 1D del problema en cada paso temporal."""
	v = body.velocity.x
	w = body.angular_velocity
	u = v + w * RADIO_CM

	if abs(u) > TOL_U_RODADURA:
		estado = "DESLIZAMIENTO"
	else:
		estado = "RODADURA PURA"

	if modo == "ideal":
		mu = MU_IDEAL
		k = K_IDEAL
		c_rr = 0.0
	else:
		# Coeficiente distinto según zona de pista
		mu = MU_INICIO if body.position.x < X_CAMBIO_MU else MU_FINAL
		k = K_REAL
		c_rr = C_RODADURA

	# Si desliza, actúa rozamiento cinético que reduce u hasta cero
	if estado == "DESLIZAMIENTO":
		signo = 1.0 if u > 0 else -1.0
		a = -mu * GRAVEDAD_CM * signo
		alpha = -(mu * GRAVEDAD_CM / (k * RADIO_CM)) * signo
	else:
		# Una vez en rodadura pura, mantenemos la restricción v + wR = 0
		a = 0.0
		alpha = 0.0

	# Rozamiento de rodadura (solo en modo real): frena tras iniciar rodadura
	if modo == "real" and estado == "RODADURA PURA":
		if abs(v) > 1e-6:
			a_rr = -c_rr * GRAVEDAD_CM * (1.0 if v > 0 else -1.0)
		else:
			a_rr = 0.0
		a += a_rr
		alpha = -a / RADIO_CM

	v_nuevo = v + a * DT
	w_nuevo = w + alpha * DT

	# Impone rodadura exacta al cruzar la condición
	u_nuevo = v_nuevo + w_nuevo * RADIO_CM
	if estado == "DESLIZAMIENTO" and (u * u_nuevo < 0.0 or abs(u_nuevo) < TOL_U_RODADURA):
		# Ajuste mínimo sin inyectar energia: solo forzamos la restriccion v + wR = 0.
		w_nuevo = -v_nuevo / RADIO_CM

	body.velocity = (v_nuevo, 0.0)
	body.angular_velocity = w_nuevo

	mu_txt = MU_IDEAL if modo == "ideal" else (MU_INICIO if body.position.x < X_CAMBIO_MU else MU_FINAL)
	return estado, mu_txt, v_nuevo, w_nuevo


def simular(modo, teorico_ideal):
	"""Ejecuta una simulación y devuelve magnitudes al entrar en rodadura pura."""
	pygame.init()
	screen = pygame.display.set_mode((ANCHO, ALTO))
	pygame.display.set_caption(f"Bola de bolos - modo {modo}")
	clock = pygame.time.Clock()
	draw_options = pymunk.pygame_util.DrawOptions(screen)
	fuente = pygame.font.SysFont("consolas", 22)

	space, _, y_suelo, _, x_fin = setup_simulation()
	if modo == "ideal":
		body = crear_bola(space, y_suelo, K_IDEAL, V0_CM_S, OMEGA0_IDEAL)
	else:
		body = crear_bola(space, y_suelo, K_REAL, V0_CM_S, OMEGA0_REAL)

	tiempo = 0.0
	tiempo_espera = 0.0
	t_rod_sim = None
	v_rod_sim = None
	w_rod_sim = None

	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		y_contacto = y_suelo - RADIO_CM
		en_tramo_pista = body.position.x <= (x_fin - RADIO_CM)
		ha_caido = body.position.y > (y_suelo + 0.6 * RADIO_CM)
		en_espera = tiempo_espera < ESPERA_INICIAL_S

		if en_espera:
			estado = "PREPARADO"
			mu_actual = 0.0
			v = body.velocity.x
			w = body.angular_velocity
		elif en_tramo_pista and not ha_caido:
			estado, mu_actual, v, w = actualizar_dinamica_manual(body, modo, tiempo)
		else:
			estado = "FUERA DE PISTA"
			mu_actual = 0.0
			v = body.velocity.x
			w = body.angular_velocity

		if t_rod_sim is None and estado == "RODADURA PURA":
			t_rod_sim = tiempo
			v_rod_sim = v
			w_rod_sim = w

		# Avance cinemático manual para que el movimiento siga solo el modelo 1D.
		if en_espera:
			tiempo_espera += DT
		else:
			body.position = (body.position.x + v * DT, y_contacto)
			body.angle += w * DT
			tiempo += DT

		# Dibujo
		screen.fill((245, 245, 245))
		space.debug_draw(draw_options)

		color_estado = (180, 20, 20) if estado == "DESLIZAMIENTO" else (20, 120, 20)
		lineas = [
			f"MODO: {modo.upper()}",
			f"t = {tiempo:.2f} s",
			f"v = {v:.2f} cm/s ({v/100:.2f} m/s)",
			f"w = {w:.2f} rad/s",
			f"estado: {estado}",
			f"mu actual = {mu_actual:.3f}",
		]

		if modo == "ideal":
			lineas.append(f"t_rod teorico = {teorico_ideal['t_rod']:.3f} s")
			lineas.append(
				f"v_rod teorica = {teorico_ideal['v_rod']:.2f} cm/s"
			)

		for i, txt in enumerate(lineas):
			if "estado:" in txt:
				img = fuente.render(txt, True, color_estado)
			else:
				img = fuente.render(txt, True, (15, 15, 15))
			screen.blit(img, (35, 20 + i * 28))

		pygame.display.flip()
		clock.tick(FPS)

		# Terminación automática al comparar rodadura y evitar esperas innecesarias
		if t_rod_sim is not None and tiempo > t_rod_sim + 0.6:
			running = False

		# Fin del tramo útil de pista o pérdida de contacto
		if estado == "FUERA DE PISTA" or body.position.x >= (x_fin - RADIO_CM):
			running = False

		# Si en el modo real se detiene casi por completo, termina
		if modo == "real" and abs(v) < 1.0 and abs(w) < 0.1 and tiempo > 1.0:
			running = False

		# Seguridad para no alargar si se cierra tarde
		if tiempo > 15.0:
			running = False

	pygame.quit()

	return {
		"t_rod_sim": t_rod_sim,
		"v_rod_sim": v_rod_sim,
		"w_rod_sim": w_rod_sim,
	}


def imprimir_comparaciones(res_teorico_ideal, res_sim_ideal, res_sim_real):
	"""Comparaciones pedidas en apartados 2 y 3."""
	print("\n=== APARTADO 2: COMPARACION IDEAL (FORMULA vs SIMULACION) ===")
	if res_sim_ideal["t_rod_sim"] is None:
		print("No se detecto rodadura pura en la simulacion ideal.")
	else:
		dt = res_sim_ideal["t_rod_sim"] - res_teorico_ideal["t_rod"]
		dv = res_sim_ideal["v_rod_sim"] - res_teorico_ideal["v_rod"]
		print(f"t_rod teorico = {res_teorico_ideal['t_rod']:.3f} s")
		print(f"t_rod sim     = {res_sim_ideal['t_rod_sim']:.3f} s")
		print(f"diferencia dt = {dt:.3f} s")
		print(f"v_rod teorica = {res_teorico_ideal['v_rod']:.3f} cm/s")
		print(f"v_rod sim     = {res_sim_ideal['v_rod_sim']:.3f} cm/s")
		print(f"diferencia dv = {dv:.3f} cm/s")

	print("\n=== APARTADO 3: COMPARACION REAL vs IDEAL ===")
	print("Cambios realistas implementados:")
	print("a) Momento de inercia no uniforme: I = k m R^2 con k=0.36")
	print("b) Rozamiento por rodadura: coeficiente C_RODADURA")
	print("c) Coeficiente de friccion variable en la pista (mu inicio/final)")
	print("d) Lanzamiento con giro inicial (omega0 != 0)")

	if res_sim_real["t_rod_sim"] is None:
		print("No se detecto rodadura pura en la simulacion realista.")
	else:
		print(
			f"Ideal: t_rod={res_sim_ideal['t_rod_sim']:.3f} s, "
			f"v_rod={res_sim_ideal['v_rod_sim']:.3f} cm/s"
		)
		print(
			f"Real : t_rod={res_sim_real['t_rod_sim']:.3f} s, "
			f"v_rod={res_sim_real['v_rod_sim']:.3f} cm/s"
		)


def main():
	res_teorico_ideal = imprimir_apartado_1()

	print("\nAbriendo simulacion IDEAL (apartado 2)...")
	res_sim_ideal = simular("ideal", res_teorico_ideal)

	print("\nAbriendo simulacion REALISTA (apartado 3)...")
	res_sim_real = simular("real", res_teorico_ideal)

	imprimir_comparaciones(res_teorico_ideal, res_sim_ideal, res_sim_real)


if __name__ == "__main__":
	main()
