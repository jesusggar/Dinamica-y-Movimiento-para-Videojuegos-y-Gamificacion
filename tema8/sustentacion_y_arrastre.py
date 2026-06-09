import numpy as np

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


def calcular_cl_avion(modelo, alpha_grados):
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


def calcular_cd_avion(modelo, alpha_grados):
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
		print(f"Error: El modelo '{modelo}' no está definido en la librería.")
		return 0.0
		
	config = DATOS_AVIONES[modelo]
	
	# 1. Obtener el CL correspondiente para este ángulo de ataque
	cl = calcular_cl_avion(modelo, alpha_grados)
	
	# 2. Extraer parámetros geométricos de la polar
	cd_base = config["cd_base"]
	ar = config["aspect_ratio"]
	e = config["eficiencia_oswald"]
	
	# 3. Aplicar la ecuación de la resistencia inducida: CL^2 / (pi * AR * e)
	cd_inducido = (cl ** 2) / (np.pi * ar * e)
	
	# 4. El CD total es la suma de la resistencia parásita y la inducida
	cd_total = cd_base + cd_inducido
	
	return cd_total


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
