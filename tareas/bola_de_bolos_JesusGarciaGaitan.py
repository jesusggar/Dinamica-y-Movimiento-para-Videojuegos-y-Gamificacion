''' Ejercicio de bola de bolos.

Apartado 1 (modelo ideal, esfera maciza):
- I = (2/5) m R^2
- Plano horizontal, rozamiento cinetico constante mu
- Sin aire ni otras fuerzas

Mientras desliza:
	v(t) = v0 - mu*g*sign(u0)*t
	omega(t) = omega0 + (5/2)*(mu*g/R)*sign(u0)*t
	donde u0 = v0 - omega0*R

Inicio de rodadura pura (u=0):
	t_rod = 2*|u0|/(7*mu*g)
	v_rod = v0 - (2/7)*u0
	omega_rod = omega0 + (5/7)*(u0/R)
'''

import math
import pygame
import pymunk
import pymunk.pygame_util


# --- PARAMETROS EDITABLES (SI) ---
G = 9.81

# Apartado 2 (ideal)
MASA = 7.0
RADIO_M = 0.1085
V0_M_S = 8.0
OMEGA0_IDEAL = 0.0
MU_IDEAL = 0.12

# Apartado 3 (realidad)
K_INERCIA_REAL = 0.33          # a) Inercia distinta de esfera uniforme
MU_RODADURA_REAL = 0.003       # b) Rozamiento por rodadura
MU_TRAMO_INICIAL = 0.04        # c) Tramo inicial aceitado
MU_TRAMO_FINAL = 0.22          # c) Tramo final seco
X_CAMBIO_TRAMO_M = 8.0         # c) Cambio de tramo en metros
OMEGA0_REAL = 18.0             # d) Lanzamiento con giro inicial

# Pantalla
ANCHO = 1500
ALTO = 500
FPS = 60
DT = 1.0 / FPS
SCALE = 120.0                  # pixeles por metro
Y_PISTA = 360
X_INICIO = 120
EPS_SLIP = 1e-3
PAUSA_INICIO_S = 1.5
FRAMES_CONFIRM_RODADURA = 20
MARGEN_CAMARA_PX = 520
LARGO_PISTA_EXTRA_PX = 8000
BOLA_ESCALA_VISUAL = 2
AGUJERO_RADIO_REL = 0.14


def ideal_transition(v0, omega0, mu, radius):
	"""Prediccion analitica del apartado 1 para esfera maciza uniforme."""
	if mu <= 0.0:
		raise ValueError("mu debe ser mayor que 0")

	u0 = v0 - omega0 * radius
	if abs(u0) < 1e-12:
		return 0.0, v0, omega0

	t_rod = 2.0 * abs(u0) / (7.0 * mu * G)
	v_rod = v0 - (2.0 / 7.0) * u0
	omega_rod = omega0 + (5.0 / 7.0) * (u0 / radius)
	return t_rod, v_rod, omega_rod


def print_apartado_1(masa, radio, v0, mu, omega0):
	"""Imprime suposiciones, expresiones y resultado numerico del apartado 1."""
	u0 = v0 - omega0 * radio
	t_rod, v_rod, omega_rod = ideal_transition(v0, omega0, mu, radio)

	print("\n" + "=" * 78)
	print("APARTADO 1: MODELO IDEAL (ESFERA MACIZA, ROZAMIENTO CINETICO CONSTANTE)")
	print("=" * 78)
	print("Suposiciones:")
	print("1) Esfera uniforme con I=(2/5)mR^2")
	print("2) Plano horizontal con coeficiente de rozamiento cinetico mu constante")
	print("3) Sin resistencia del aire ni efectos adicionales")
	print("4) El rozamiento se opone al deslizamiento en el contacto")
	print("\nDurante deslizamiento:")
	print("v(t)=v0-mu*g*sign(u0)*t")
	print("omega(t)=omega0+(5/2)*(mu*g/R)*sign(u0)*t")
	print("\nRodadura pura cuando v-omega*R=0:")
	print("t_rod=2*|u0|/(7*mu*g)")
	print("v_rod=v0-(2/7)*u0")
	print("omega_rod=omega0+(5/7)*(u0/R)")
	print("\nDatos usados:")
	print(f"m={masa:.3f} kg, R={radio:.4f} m, v0={v0:.3f} m/s, omega0={omega0:.3f} rad/s, mu={mu:.3f}")
	print(f"u0=v0-omega0*R={u0:.6f} m/s")
	print("\nResultado ideal:")
	print(f"t_rod={t_rod:.6f} s")
	print(f"v_rod={v_rod:.6f} m/s")
	print(f"omega_rod={omega_rod:.6f} rad/s")


def setup_simulation(escenario):
	"""Misma idea de estructura que el ejercicio de bolos de clase: crea espacio, pista y bola."""
	space = pymunk.Space()
	space.gravity = (0, 0)
	x_fin_pista = ANCHO + LARGO_PISTA_EXTRA_PX

	# Pista horizontal
	static_body = space.static_body
	if escenario == "ideal":
		pista = pymunk.Segment(static_body, (0, Y_PISTA), (x_fin_pista, Y_PISTA), 6)
		pista.friction = MU_IDEAL
		pista.color = (170, 170, 170, 255)
		space.add(pista)
	else:
		x_cambio_px = X_INICIO + X_CAMBIO_TRAMO_M * SCALE
		pista_1 = pymunk.Segment(static_body, (0, Y_PISTA), (x_cambio_px, Y_PISTA), 6)
		pista_2 = pymunk.Segment(static_body, (x_cambio_px, Y_PISTA), (x_fin_pista, Y_PISTA), 6)
		pista_1.friction = MU_TRAMO_INICIAL
		pista_2.friction = MU_TRAMO_FINAL
		pista_1.color = (170, 190, 230, 255)
		pista_2.color = (230, 200, 170, 255)
		space.add(pista_1, pista_2)

	# Bola
	radio_px = RADIO_M * SCALE
	if escenario == "ideal":
		k_inercia = 2.0 / 5.0
		omega0 = OMEGA0_IDEAL
	else:
		k_inercia = K_INERCIA_REAL
		omega0 = OMEGA0_REAL

	# Usamos momento en unidades de pantalla para evitar inestabilidad numerica.
	moment = k_inercia * MASA * (radio_px ** 2)
	bola = pymunk.Body(MASA, moment)
	bola.position = (X_INICIO, Y_PISTA - radio_px)
	bola.velocity = (V0_M_S * SCALE, 0.0)
	bola.angular_velocity = omega0

	shape_bola = pymunk.Circle(bola, radio_px)
	shape_bola.friction = 0.0
	shape_bola.color = (30, 70, 190, 255)

	space.add(bola, shape_bola)
	return space, bola


def mu_actual(escenario, x_rel_m):
	if escenario == "ideal":
		return MU_IDEAL
	if x_rel_m < X_CAMBIO_TRAMO_M:
		return MU_TRAMO_INICIAL
	return MU_TRAMO_FINAL


def k_inercia_actual(escenario):
	if escenario == "ideal":
		return 2.0 / 5.0
	return K_INERCIA_REAL


def step_modelo(bola, escenario, dt):
	"""Actualiza v y omega con el modelo del enunciado y devuelve magnitudes en SI."""
	x_rel_m = max(0.0, (bola.position.x - X_INICIO) / SCALE)
	v = bola.velocity.x / SCALE
	omega = bola.angular_velocity

	mu = mu_actual(escenario, x_rel_m)
	k = k_inercia_actual(escenario)
	slip = v - omega * RADIO_M
	a = 0.0
	alpha = 0.0

	if abs(slip) > EPS_SLIP:
		s = math.copysign(1.0, slip)
		a = -mu * G * s
		alpha = (mu * G / (k * RADIO_M)) * s
	elif escenario == "real" and abs(v) > 1e-8 and MU_RODADURA_REAL > 0.0:
		s = math.copysign(1.0, v)
		a = -MU_RODADURA_REAL * G * s
		alpha = a / RADIO_M

	v_nuevo = v + a * dt
	omega_nueva = omega + alpha * dt
	slip_nuevo = v_nuevo - omega_nueva * RADIO_M

	if abs(slip_nuevo) <= EPS_SLIP or (slip * slip_nuevo < 0.0):
		omega_nueva = v_nuevo / RADIO_M
		slip_nuevo = 0.0

	bola.velocity = (v_nuevo * SCALE, 0.0)
	bola.angular_velocity = omega_nueva

	return x_rel_m, v_nuevo, omega_nueva, slip_nuevo, mu


def draw_info(screen, font, lineas):
	x = 30
	y = 20
	for linea in lineas:
		txt = font.render(linea, True, (20, 20, 20))
		screen.blit(txt, (x, y))
		y += 28


def draw_bola_bolos(screen, bola, cam_x):
	"""Dibuja una bola de bolos mas grande con 3 agujeros que giran con el angulo."""
	radio_base = RADIO_M * SCALE
	radio_vis = radio_base * BOLA_ESCALA_VISUAL
	x_c = bola.position.x - cam_x
	y_c = bola.position.y

	# Cuerpo de la bola (superpuesto al debug draw para mejor visibilidad).
	pygame.draw.circle(screen, (40, 80, 210), (int(x_c), int(y_c)), int(radio_vis))
	pygame.draw.circle(screen, (15, 35, 110), (int(x_c), int(y_c)), int(radio_vis), width=3)

	# Agujeros (disposicion triangular) en coordenadas locales.
	r_hole = max(2, int(radio_vis * AGUJERO_RADIO_REL))
	holes_local = [
		(-0.26 * radio_vis, -0.22 * radio_vis),
		(0.00 * radio_vis, -0.34 * radio_vis),
		(0.26 * radio_vis, -0.22 * radio_vis),
	]

	ang = bola.angle
	c = math.cos(ang)
	s = math.sin(ang)
	for ox, oy in holes_local:
		rx = c * ox - s * oy
		ry = s * ox + c * oy
		pygame.draw.circle(screen, (10, 10, 15), (int(x_c + rx), int(y_c + ry)), r_hole)


def pausa_inicio(screen, clock, draw_options, space, nombre):
	"""Pausa breve antes de arrancar cada ejecucion de escenario."""
	font = pygame.font.SysFont("Arial", 26)
	inicio_ms = pygame.time.get_ticks()
	duracion_ms = int(PAUSA_INICIO_S * 1000)

	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return False

		transcurrido = pygame.time.get_ticks() - inicio_ms
		restante_ms = max(0, duracion_ms - transcurrido)

		screen.fill((240, 240, 240))
		space.debug_draw(draw_options)
		msg = f"{nombre} inicia en {restante_ms / 1000.0:.1f} s"
		txt = font.render(msg, True, (30, 30, 30))
		screen.blit(txt, (30, 26))
		pygame.display.flip()
		clock.tick(FPS)

		if restante_ms <= 0:
			running = False

	return True


def simular_escenario(screen, clock, draw_options, escenario, prediccion_ideal=None):
	"""Ejecuta un escenario y muestra en pantalla t, v, omega y estado."""
	space, bola = setup_simulation(escenario)
	font = pygame.font.SysFont("Arial", 24)
	draw_options.transform = pymunk.Transform()

	t = 0.0
	t_rod = None
	v_rod = None
	omega_rod = None
	frames_rodadura = 0

	if escenario == "ideal":
		nombre = "APARTADO 2 - MODELO IDEAL"
		t_max = 8.0
	else:
		nombre = "APARTADO 3 - MODELO MAS REALISTA"
		t_max = 10.0

	if not pausa_inicio(screen, clock, draw_options, space, nombre):
		return None

	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return None

		x_rel_m, v, omega, slip, mu = step_modelo(bola, escenario, DT)
		space.step(DT)
		# Bloquea la componente vertical para evitar caidas numericas fuera de modelo.
		radio_px = RADIO_M * SCALE
		bola.velocity = (bola.velocity.x, 0.0)
		bola.position = (bola.position.x, Y_PISTA - radio_px)
		t += DT

		if abs(slip) <= EPS_SLIP:
			frames_rodadura += 1
		else:
			frames_rodadura = 0

		rodadura_confirmada = frames_rodadura >= FRAMES_CONFIRM_RODADURA
		estado = "RODADURA PURA" if rodadura_confirmada else "DESLIZAMIENTO"
		if t_rod is None and rodadura_confirmada:
			t_rod = t - (FRAMES_CONFIRM_RODADURA - 1) * DT
			v_rod = v
			omega_rod = omega

		# Camara horizontal para mantener la bola visible en pantalla.
		cam_x = max(0.0, bola.position.x - MARGEN_CAMARA_PX)
		draw_options.transform = pymunk.Transform(tx=-cam_x, ty=0)
		x_pantalla = bola.position.x - cam_x
		visible = 0.0 <= x_pantalla <= ANCHO

		screen.fill((240, 240, 240))
		space.debug_draw(draw_options)
		draw_bola_bolos(screen, bola, cam_x)

		lineas = [
			nombre,
			f"t = {t:6.3f} s",
			f"v = {v:7.4f} m/s",
			f"omega = {omega:7.4f} rad/s",
			f"slip = v-omega*R = {slip: .5f} m/s",
			f"estado = {estado}",
			f"confirmacion rodadura = {frames_rodadura}/{FRAMES_CONFIRM_RODADURA} frames",
			f"mu pista = {mu:.3f}",
			f"bola visible en ventana = {'SI' if visible else 'NO'}",
		]

		if escenario == "real":
			lineas.append(f"x tramo = {x_rel_m:6.3f} m (cambio en {X_CAMBIO_TRAMO_M:.2f} m)")

		if prediccion_ideal is not None and t_rod is not None:
			lineas.append(f"teoria ideal: t={prediccion_ideal[0]:.3f}s, v={prediccion_ideal[1]:.3f}m/s")
			lineas.append(f"simulacion:  t={t_rod:.3f}s, v={v_rod:.3f}m/s")

		draw_info(screen, font, lineas)
		pygame.display.flip()
		clock.tick(FPS)

		if t_rod is not None and t > t_rod + 1.5:
			break
		if t >= t_max:
			break

	return {"t_rod": t_rod, "v_rod": v_rod, "omega_rod": omega_rod}


def print_comparison(titulo, resultado, t_ref, v_ref):
	print("\n" + "-" * 78)
	print(titulo)
	print("-" * 78)
	if resultado is None or resultado["t_rod"] is None or resultado["v_rod"] is None:
		print("No se detecto rodadura pura dentro del tiempo maximo de simulacion.")
		return

	t_sim = resultado["t_rod"]
	v_sim = resultado["v_rod"]
	err_t = 100.0 * (t_sim - t_ref) / t_ref if t_ref != 0.0 else 0.0
	err_v = 100.0 * (v_sim - v_ref) / v_ref if v_ref != 0.0 else 0.0

	print(f"Referencia: t={t_ref:.6f} s, v={v_ref:.6f} m/s")
	print(f"Simulacion: t={t_sim:.6f} s, v={v_sim:.6f} m/s")
	print(f"Error relativo tiempo: {err_t:.3f} %")
	print(f"Error relativo velocidad: {err_v:.3f} %")


def main():
	print_apartado_1(MASA, RADIO_M, V0_M_S, MU_IDEAL, OMEGA0_IDEAL)
	pred_t, pred_v, pred_w = ideal_transition(V0_M_S, OMEGA0_IDEAL, MU_IDEAL, RADIO_M)

	pygame.init()
	screen = pygame.display.set_mode((ANCHO, ALTO))
	pygame.display.set_caption("Bola de bolos - deslizamiento y rodadura")
	clock = pygame.time.Clock()
	draw_options = pymunk.pygame_util.DrawOptions(screen)

	print("\nSe abre la simulacion del APARTADO 2 (ideal).")
	resultado_ideal = simular_escenario(
		screen,
		clock,
		draw_options,
		escenario="ideal",
		prediccion_ideal=(pred_t, pred_v, pred_w),
	)
	print_comparison(
		"Comparacion APARTADO 2: teoria ideal vs simulacion ideal",
		resultado_ideal,
		pred_t,
		pred_v,
	)

	print("\nSe abre la simulacion del APARTADO 3 (mas realista).")
	resultado_real = simular_escenario(
		screen,
		clock,
		draw_options,
		escenario="real",
	)
	print_comparison(
		"Comparacion APARTADO 3: escenario realista vs resultado ideal del apartado 2",
		resultado_real,
		pred_t,
		pred_v,
	)

	pygame.quit()


if __name__ == "__main__":
	main()
