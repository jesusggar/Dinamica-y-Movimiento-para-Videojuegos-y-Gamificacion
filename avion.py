import math
import sys

import pygame
import pymunk


WIDTH, HEIGHT = 1200, 700
FPS = 60
SCALE = 20.0

# Environment
G = 9.81
RHO = 1.225

# Runway (Malaga-like, simplified)
RUNWAY_Y = 0.0
RUNWAY_START = -100.0
RUNWAY_END = 800.0

# Airframe approximations (2D side view)
MASS = 1100.0
WING_AREA = 16.2
CD0 = 0.03
K = 0.06
CL_ALPHA = 5.5
CL_MAX = 1.4
CL_MIN = -1.2
MAX_ELEVATOR = math.radians(12.0)

THRUST_MAX = 15000.0

# Control
PITCH_RATE = math.radians(50.0)
THROTTLE_RATE = 0.35
FLAP_CL = 0.4


def clamp(value, low, high):
	return max(low, min(high, value))


def vec_len(v):
	return math.hypot(v[0], v[1])


def vec_norm(v):
	length = vec_len(v)
	if length < 1e-6:
		return (0.0, 0.0)
	return (v[0] / length, v[1] / length)


def vec_perp(v):
	return (-v[1], v[0])


def make_airplane_body(space, position):
	moment = pymunk.moment_for_box(MASS, (6.5, 1.5))
	body = pymunk.Body(MASS, moment)
	body.position = position
	body.angle = 0.0

	fuselage = pymunk.Poly.create_box(body, (6.5, 1.5))
	fuselage.friction = 0.6
	fuselage.elasticity = 0.1

	tail = pymunk.Poly(
		body,
		[(2.8, 0.2), (3.5, 0.2), (3.1, 1.0)],
	)
	tail.friction = 0.6
	tail.elasticity = 0.1

	space.add(body, fuselage, tail)
	return body


def make_ground(space):
	ground = pymunk.Segment(
		space.static_body,
		(RUNWAY_START - 300.0, RUNWAY_Y),
		(RUNWAY_END + 300.0, RUNWAY_Y),
		0.2,
	)
	ground.friction = 1.0
	ground.elasticity = 0.2
	space.add(ground)


def compute_aero_forces(body, elevator, flap, thrust):
	velocity = body.velocity
	speed = vec_len(velocity)
	if speed < 0.5:
		return (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)

	vel_dir = vec_norm(velocity)
	wing_dir = (math.cos(body.angle), math.sin(body.angle))

	vel_angle = math.atan2(vel_dir[1], vel_dir[0])
	aoa = body.angle - vel_angle + elevator
	aoa = clamp(aoa, math.radians(-25.0), math.radians(25.0))

	cl = CL_ALPHA * aoa
	if flap > 0.0:
		cl += FLAP_CL
	cl = clamp(cl, CL_MIN, CL_MAX)

	cd = CD0 + K * (cl ** 2)

	q = 0.5 * RHO * speed * speed
	lift_mag = q * WING_AREA * cl
	drag_mag = q * WING_AREA * cd

	lift_dir = vec_perp(vel_dir)
	if lift_dir[1] < 0:
		lift_dir = (-lift_dir[0], -lift_dir[1])

	lift = (lift_dir[0] * lift_mag, lift_dir[1] * lift_mag)
	drag = (-vel_dir[0] * drag_mag, -vel_dir[1] * drag_mag)

	thrust_vec = (wing_dir[0] * thrust, wing_dir[1] * thrust)

	return lift, drag, thrust_vec


def draw_hud(screen, font, throttle, elevator, flap, speed, altitude):
	text = [
		"Runway: Malaga (LEMG) - 2D",
		f"Throttle: {throttle * 100:5.1f}%",
		f"Elevator: {math.degrees(elevator):5.1f} deg",
		f"Flap: {flap * 100:4.0f}%",
		f"Speed: {speed:6.1f} m/s",
		f"Altitude: {altitude:6.1f} m",
	]

	x, y = 15, 10
	for line in text:
		surf = font.render(line, True, (20, 20, 20))
		screen.blit(surf, (x, y))
		y += 20


def world_to_screen(point, camera):
	x = (point[0] - camera[0]) * SCALE + WIDTH * 0.5
	y = HEIGHT - ((point[1] - camera[1]) * SCALE + HEIGHT * 0.5)
	return (x, y)


def draw_runway(screen, camera):
	rwy_height = 18.0
	rwy_rect_world = (
		RUNWAY_START,
		RUNWAY_Y - 0.1,
		RUNWAY_END - RUNWAY_START,
		rwy_height,
	)

	(x, y) = world_to_screen((rwy_rect_world[0], rwy_rect_world[1]), camera)
	width = rwy_rect_world[2] * SCALE
	height = rwy_rect_world[3] * SCALE
	rect = pygame.Rect(x, y - height, width, height)
	pygame.draw.rect(screen, (70, 70, 75), rect)

	# Centerline markings
	mark_length = 20.0
	mark_gap = 15.0
	mark_x = RUNWAY_START + 20.0
	while mark_x < RUNWAY_END - 20.0:
		p1 = world_to_screen((mark_x, RUNWAY_Y + 8.5), camera)
		p2 = world_to_screen((mark_x + mark_length, RUNWAY_Y + 8.5), camera)
		pygame.draw.line(screen, (230, 230, 230), p1, p2, 3)
		mark_x += mark_length + mark_gap


def main():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Cessna 172 - Pymunk/Pygame")
	clock = pygame.time.Clock()
	font = pygame.font.SysFont("consolas", 18)

	space = pymunk.Space()
	space.gravity = (0.0, -G)

	make_ground(space)
	plane = make_airplane_body(space, (40.0, RUNWAY_Y + 0.9))

	throttle = 0.0
	elevator = 0.0
	flap = 0.0
	running = True

	while running:
		dt = clock.tick(FPS) / 1000.0

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False

		keys = pygame.key.get_pressed()

		if keys[pygame.K_UP] or keys[pygame.K_w]:
			elevator += PITCH_RATE * dt
		if keys[pygame.K_DOWN] or keys[pygame.K_s]:
			elevator -= PITCH_RATE * dt
		if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
			elevator *= 0.95

		if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
			throttle += THROTTLE_RATE * dt
		if keys[pygame.K_LEFT] or keys[pygame.K_a]:
			throttle -= THROTTLE_RATE * dt

		if keys[pygame.K_f]:
			flap = clamp(flap + 0.5 * dt, 0.0, 1.0)
		if keys[pygame.K_g]:
			flap = clamp(flap - 0.5 * dt, 0.0, 1.0)

		elevator = clamp(elevator, -MAX_ELEVATOR, MAX_ELEVATOR)
		throttle = clamp(throttle, 0.0, 1.0)

		lift, drag, thrust_vec = compute_aero_forces(
			plane,
			elevator,
			flap,
			throttle * THRUST_MAX,
		)

		# Pymunk uses arbitrary units; forces are tuned for this scale.
		force_scale = 1.0
		plane.apply_force_at_world_point(
			(lift[0] * force_scale, lift[1] * force_scale),
			plane.position,
		)
		plane.apply_force_at_world_point(
			(drag[0] * force_scale, drag[1] * force_scale),
			plane.position,
		)
		plane.apply_force_at_world_point(
			(thrust_vec[0] * force_scale, thrust_vec[1] * force_scale),
			plane.position,
		)

		# Small stabilizing pitch torque to avoid runaway rotation.
		plane.torque -= plane.angular_velocity * 1200.0

		space.step(dt)

		screen.fill((200, 220, 245))

		# Camera follows the plane with a slight downward bias.
		camera_x = plane.position.x
		camera_y = plane.position.y - (HEIGHT * 0.35) / SCALE
		min_cam_y = RUNWAY_Y - (HEIGHT - 140) / SCALE
		camera_y = max(camera_y, min_cam_y)
		camera = (camera_x, camera_y)

		draw_runway(screen, camera)

		# Draw airplane
		pos = plane.position
		angle = -plane.angle
		cos_a = math.cos(angle)
		sin_a = math.sin(angle)
		points = [(-3.25, -0.75), (3.25, -0.75), (3.25, 0.75), (-3.25, 0.75)]
		scaled = []
		for x, y in points:
			world_x = (x * cos_a - y * sin_a) + pos.x
			world_y = (x * sin_a + y * cos_a) + pos.y
			scaled.append(world_to_screen((world_x, world_y), camera))
		pygame.draw.polygon(screen, (220, 220, 220), scaled)
		pygame.draw.polygon(screen, (20, 20, 20), scaled, 2)

		# Simple wing line
		wing_pts = [(-0.5, 0.0), (0.5, 0.0)]
		wing_scaled = []
		for x, y in wing_pts:
			world_x = (x * cos_a - y * sin_a) * 2.0 + pos.x
			world_y = (x * sin_a + y * cos_a) * 2.0 + pos.y
			wing_scaled.append(world_to_screen((world_x, world_y), camera))
		pygame.draw.line(screen, (30, 30, 30), wing_scaled[0], wing_scaled[1], 4)

		speed = vec_len(plane.velocity)
		altitude = max(0.0, plane.position.y - RUNWAY_Y)
		draw_hud(screen, font, throttle, elevator, flap, speed, altitude)

		pygame.display.flip()

	pygame.quit()
	sys.exit(0)


if __name__ == "__main__":
	main()
