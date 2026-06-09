import numpy as np
import math
from scipy.interpolate import interp1d
from simulaciones_genericas import Tsim
import pygame,time,pymunk
from pymunk import Vec2d

# =============================================================================
# PARAMETROS_CONFIGURACION: Constantes aerodinámicas ampliadas para los modelos
# =============================================================================
DATOS_AVIONES = {
	"cessna_172": {
		"pendiente_cl": 0.10,     # Incremento de CL por grado
		"alpha_0": -2.0,          # Ángulo de sustentación cero (grados)
		"alpha_stall": 16.0,      # Ángulo de entrada en pérdida (grados)
		"cd_base": 0.025,         # CD a sustentación cero (resistencia parásita)
		"aspect_ratio": 7.38,     # Esbeltez del ala (AR = envergadura^2 / superficie)
		"eficiencia_oswald": 0.75 # Factor de eficiencia del ala (e)
	},
	"boeing_747": {
		"pendiente_cl": 0.09,
		"alpha_0": -1.5,
		"alpha_stall": 15.0,
		"cd_base": 0.022,
		"aspect_ratio": 6.96,
		"eficiencia_oswald": 0.82
	},
	"f16_falcon": {
		"pendiente_cl": 0.06,
		"alpha_0": 0.0,
		"alpha_stall": 25.0,
		"cd_base": 0.015,
		"aspect_ratio": 3.20,     # Ala en delta muy corta y ancha (bajo AR)
		"eficiencia_oswald": 0.85 # Alta eficiencia estructural a altas velocidades
	},
	"asw27_planeador": {
		"pendiente_cl": 0.11,
		"alpha_0": -3.0,
		"alpha_stall": 12.0,
		"cd_base": 0.008,
		"aspect_ratio": 25.0,     # Ala extremadamente larga y estrecha (alto AR)
		"eficiencia_oswald": 0.95 # Diseño optimizado para minimizar torbellinos
	}
}

#-------------------------------------------------------------------------------------
def calcular_cl_avion(alpha_grados,modelo='cessna_172'):
	"""
	Calcula el Coeficiente de Sustentación (CL) para un modelo de avión específico
	en función de su Ángulo de Ataque (alpha) en grados.
	"""
	if modelo not in DATOS_AVIONES:
		print(f"Error: El modelo '{modelo}' no está definido en la librería.")
		return 0.0
		
	config = DATOS_AVIONES[modelo]
	cl_lineal = config["pendiente_cl"] * (alpha_grados - config["alpha_0"])
	factor_aerodinamico = 1.0 / (1.0 + np.exp((alpha_grados - config["alpha_stall"]) * 0.4))
	
	return cl_lineal * factor_aerodinamico

#-----------------------------------------------------------------------------------------
def calcular_cd_avion(alpha_grados,modelo='cessna_172'):
	"""
	Calcula el Coeficiente de Resistencia Aerodinámica (CD) total para un modelo
	de avión basándose en la ecuación de la polar: CD = CD_base + CD_inducido.
	
	El término inducido se calcula a partir del CL actual del avión.
	
	Parámetros:
	-----------
	modelo : str
		Identificador del avión ('cessna_172', 'boeing_747', 'f16_falcon', 'asw27_planeador')
	alpha_grados : float o numpy.ndarray
		Ángulo de ataque medido en grados.
		
	Retorna:
	--------
	float o numpy.ndarray
		El valor del CD total (sin unidades). Retorna 0.0 si el modelo no existe.
	"""
		
	if modelo not in DATOS_AVIONES:
		print(modelo)
		print(f"Error: El modelo '{modelo}' no está definido en la librería.")
		return 0.0
	
		
	config = DATOS_AVIONES[modelo]
	
	# 1. Obtener el CL correspondiente para este ángulo de ataque
	cl = calcular_cl_avion(alpha_grados)
	
	# 2. Extraer parámetros geométricos de la polar
	cd_base = config["cd_base"]
	ar = config["aspect_ratio"]
	e = config["eficiencia_oswald"]
	
	# 3. Aplicar la ecuación de la resistencia inducida: CL^2 / (pi * AR * e)
	cd_inducido = (cl ** 2) / (np.pi * ar * e)
	
	# 4. El CD total es la suma de la resistencia parásita y la inducida
	cd_total = cd_base + cd_inducido
	
	return cd_total
#-----------------------------------------------------------------------	
def fuerza_rodadura(masa_kg=1100,incl_rad=0.0,flift=0):
	mu_rr = 0.02
	g = 9.81
	normal = masa_kg * g * math.cos(incl_rad)-flift
	fuerza = mu_rr * normal
	return fuerza
#------------------------------------------------    
#------------------------------------------------
def fuerza_drag(v_ms,alpha_grados): 
	rho = 1.225      # Densidad del aire en kg/m^3
	Cd = calcular_cd_avion(alpha_grados)        # Coeficiente de arrastre
	area = 16.2 # Área alar m²
	
	fuerza = 0.5 * rho * (v_ms**2) * Cd * area
	return fuerza
#------------------------------------------------    
#------------------------------------------------
def fuerza_lift(v_ms,alpha_grados): 
	rho = 1.225      # Densidad del aire en kg/m^3
	Cl = calcular_cl_avion(alpha_grados)        # Coeficiente de arrastre
	area = 16.2 # Área alar m²
	
	fuerza = 0.5 * rho * (v_ms**2) * Cl * area
	return fuerza	
#---------------------------------------------------
########################################################################
########################################################################

THRUST=0
STICK=0



#--------------------------------------------
def acelera():
	global THRUST
	THRUST=min(THRUST+0.05,1)
#--------------------------------------------			
def decelera():
	global THRUST
	THRUST=max(0,THRUST-0.05)
#--------------------------------------------			
def alante():
	global STICK
	STICK=min(STICK+0.01,1)
#--------------------------------------------		
def atras():
	global STICK
	STICK=max(STICK-0.01,-1)
#--------------------------------------------		

	
WIDTH=500
HEIGHT=300
sim=Tsim(height=HEIGHT,width=WIDTH)
sim.add_evento_tecla(pygame.K_q,acelera)
sim.add_evento_tecla(pygame.K_a,decelera)
sim.add_evento_tecla(pygame.K_UP,alante)
sim.add_evento_tecla(pygame.K_DOWN,atras)

img = pygame.image.load("tema8/cessna_sinfondo.png").convert_alpha()
w, h = img.get_size()
img = pygame.transform.smoothscale(img, (w // 3, h // 3))
rect = img.get_rect()


reloj = pygame.time.Clock()
FPS=60
substep=10
dt=1/(FPS*substep)
masa=1100     #kg
Iavion=2427   #kg·m²
tiempo=0
Fe_max=2300   #N
A_alas=16.2   #m²
THRUST=1.0
alpha0=1.5     #valor del ángulo de ataque en posición horizontal
v=Vec2d(20,0)           #velocidad m/s
alpha_vel=0
pos=Vec2d(0,0)
g=Vec2d(0,-9.81)
theta=0    #inclinacion del morro del avion
omega=0

C_cola_max=0.7  #Coef. aerodinamico max de la cola
A_cola=2  #m²
rho=1.225  #kg/m³
r_cola=4.09  #distancia de la cola al CM

Ce=12000
Cstab=6000
Cdamp=2500



while sim.actualizar_eventos():
		
	#-----------------------------------------
	for _ in range(substep):
		
		fuerza=Vec2d(0,0)
		
		
		
		
		#time.sleep(1*dt)
		tiempo += dt
				
	#------------------------------------------	
	
	#imagen rotada
	rotated = pygame.transform.rotate(img, theta)
	rect = rotated.get_rect(center=(WIDTH//2, HEIGHT//2+70))
	sim.screen.fill((135, 206, 235))  # cielo
	sim.screen.blit(rotated, rect)
	# Dibuja una línea roja desde (x1, y1) hasta (x2, y2) con un grosor de 3 píxeles
	suelo=275+pos.y*125/2.7   #275  nota: 125px es aprox 2.7 m
	pygame.draw.line(sim.screen, (0, 0, 0), (0,suelo), (WIDTH, suelo), 3)
	
	
	pygame.display.flip()
	reloj.tick(FPS)
		
	print(f'{tiempo:7.2f}  |  ',end='')
	print(f'v =({v.x*1.94384:5.1f},{v.y*1.94384:5.1f}) kt  |  ',end='')
	print(f'Pos =({pos.x:3.0f},{pos.y:3.0f}) m  |  ',end='')
	print(f'F = =({fuerza.x:3.0f},{fuerza.y:3.0f}) N  |  ',end='')
	print(f'Theta = {theta:4.2f} grados  |  ',end='')
	print('')






################################################################################
################################################################################
################################################################################
################################################################################
exit(0)

# =============================================================================
# EJEMPLO DE EVALUACIÓN
# =============================================================================
if __name__ == "__main__":
	print("--- Prueba de resistencia aerodinámica (CD) ---")
	angulo = 6.0  # grados de cabeceo/ataque
	
	for av in DATOS_AVIONES.keys():
		cl_res = calcular_cl_avion(av, angulo)
		cd_res = calcular_cd_avion(av, angulo)
		print(f"[{av}] alpha={angulo}° -> CL={cl_res:.3f} | CD_Total={cd_res:.4f}")
