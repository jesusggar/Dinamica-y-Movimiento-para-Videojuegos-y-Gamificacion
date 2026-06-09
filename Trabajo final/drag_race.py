import pygame
import sys
import math
import random
import os
from motor_fisico import ferrari, mustang, skyline

# --- CONFIGURACIÓN DE PYGAME ---
pygame.init()
pygame.mixer.init()
try:
    pygame.mixer.music.load("background-music.mp3")
    pygame.mixer.music.set_volume(0.4)  # Volumen muy bajo
    pygame.mixer.music.play(-1)         # Bucle infinito
except FileNotFoundError:
    print("No se encontró el archivo 'background-music.mp3'.")

WIDTH, HEIGHT = 1000, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Drag Race - Menú Animado")
clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 24)
font_small = pygame.font.SysFont("consolas", 18)
font_big = pygame.font.SysFont("consolas", 36, bold=True)
font_huge = pygame.font.SysFont("consolas", 72, bold=True)

# --- FUNCIONES DE GRÁFICOS ---
def cargar_fondo_proporcional(ruta, altura_pantalla):
    img = pygame.image.load(ruta).convert_alpha()
    proporcion = altura_pantalla / img.get_height()
    nuevo_ancho = int(img.get_width() * proporcion)
    return pygame.transform.scale(img, (nuevo_ancho, altura_pantalla))

def dibujar_capa_parallax(pantalla, img, offset_base, multiplicador_vel):
    ancho_img = img.get_width()
    offset = (offset_base * multiplicador_vel) % ancho_img
    x = -offset
    while x < WIDTH:
        pantalla.blit(img, (x, 0))
        x += ancho_img

def cargar_coche_proporcional(ruta, ancho_objetivo, voltear=False):
    img = pygame.image.load(ruta).convert_alpha()
    if voltear: img = pygame.transform.flip(img, True, False) 
    proporcion = ancho_objetivo / img.get_width()
    nuevo_alto = int(img.get_height() * proporcion)
    return pygame.transform.smoothscale(img, (ancho_objetivo, nuevo_alto))

def cargar_rueda(ruta, diametro, voltear=False):
    img = pygame.image.load(ruta).convert_alpha()
    if voltear: img = pygame.transform.flip(img, True, False)
    return pygame.transform.smoothscale(img, (diametro, diametro))

def generar_miniatura(img, ancho_objetivo):
    proporcion = ancho_objetivo / img.get_width()
    nuevo_alto = int(img.get_height() * proporcion)
    return pygame.transform.smoothscale(img, (ancho_objetivo, nuevo_alto))

# --- CARGA DE GRÁFICOS: FONDOS ---
img_back = cargar_fondo_proporcional("back.png", HEIGHT)
img_sun = cargar_fondo_proporcional("sun.png", HEIGHT)
img_buildings = cargar_fondo_proporcional("buildings.png", HEIGHT)
img_palms = cargar_fondo_proporcional("palms.png", HEIGHT)
img_palm_tree = cargar_fondo_proporcional("palm-tree.png", HEIGHT)
img_highway = cargar_fondo_proporcional("highway.png", HEIGHT)

# --- CARGA DE COCHES ---
ANCHO_COCHE = 300
DIAMETRO_RUEDA = 46

img_ferrari_body = cargar_coche_proporcional("ferrari_body.png", ANCHO_COCHE, voltear=False)
img_ferrari_rueda = cargar_rueda("ferrari_rueda.png", DIAMETRO_RUEDA, voltear=False)

img_mustang_body = cargar_coche_proporcional("mustang_body.png", ANCHO_COCHE, voltear=True)
img_mustang_rueda = cargar_rueda("rueda_mustang.png", DIAMETRO_RUEDA, voltear=True)

img_skyline_body = cargar_coche_proporcional("skyline_body.png", ANCHO_COCHE, voltear=True)
img_skyline_rueda = cargar_rueda("rueda_skyline.png", DIAMETRO_RUEDA, voltear=True)

# --- MINIATURAS PARA EL MENÚ ---
ANCHO_MENU = 210
img_ferrari_menu = generar_miniatura(img_ferrari_body, ANCHO_MENU)
img_mustang_menu = generar_miniatura(img_mustang_body, ANCHO_MENU)
img_skyline_menu = generar_miniatura(img_skyline_body, ANCHO_MENU)

# --- VARIABLES DEL JUEGO ---
coche_actual = None
v_coche = 0.0      
marcha_actual = 1
acelerador = 0.0   
freno = 0.0        
FPS = 60
dt = 1 / FPS
px_por_metro = 45  

# Variables de Carrera
distancia_recorrida = 0.0
tiempo_carrera = 0.0
opciones_meta = [400.0, 800.0, 1000.0, float('inf')] 
indice_meta = 0
meta_metros = opciones_meta[indice_meta]

# Variables de Partículas y Modos
particulas_humo = []
derrapando = False
launch_control_activo = False  

# --- VARIABLES DE CLASIFICACIÓN ---
texto_nombre = ""
tiempos_cargados = []

# --- MÁQUINA DE ESTADOS ---
estado_juego = "MENU"
tiempo_inicio_juego = 0
tiempo_verde = 3.0

running = True

while running:
    # 1. GESTIÓN DE EVENTOS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                launch_control_activo = not launch_control_activo
                
            if estado_juego == "MENU":
                if event.key == pygame.K_l:
                    indice_meta = (indice_meta + 1) % len(opciones_meta)
                    meta_metros = opciones_meta[indice_meta]
                
                elif event.key == pygame.K_t:
                    tiempos_cargados = []
                    if os.path.exists("tiempos.txt"):
                        with open("tiempos.txt", "r", encoding="utf-8") as f:
                            for linea in f:
                                partes = linea.strip().split(',')
                                if len(partes) == 5:
                                    tiempos_cargados.append(partes)
                        tiempos_cargados.sort(key=lambda x: float(x[4]))
                    estado_juego = "LEADERBOARD"

                elif event.key == pygame.K_1:
                    coche_actual = ferrari
                    estado_juego = "SEMAFORO"
                    tiempo_inicio_juego = pygame.time.get_ticks()
                    tiempo_verde = 2.5 + random.uniform(0.2, 2.0)
                elif event.key == pygame.K_2:
                    coche_actual = mustang
                    estado_juego = "SEMAFORO"
                    tiempo_inicio_juego = pygame.time.get_ticks()
                    tiempo_verde = 2.5 + random.uniform(0.2, 2.0)
                elif event.key == pygame.K_3:
                    coche_actual = skyline
                    estado_juego = "SEMAFORO"
                    tiempo_inicio_juego = pygame.time.get_ticks()
                    tiempo_verde = 2.5 + random.uniform(0.2, 2.0)
            
            elif estado_juego == "LEADERBOARD":
                if event.key == pygame.K_ESCAPE:
                    estado_juego = "MENU"
            
            elif estado_juego == "FIN":
                if event.key == pygame.K_RETURN:
                    texto_nombre = ""
                    estado_juego = "INPUT_NOMBRE"
                elif event.key == pygame.K_ESCAPE:
                    estado_juego = "MENU"
                    coche_actual = None; v_coche = 0.0; marcha_actual = 1
                    distancia_recorrida = 0.0; tiempo_carrera = 0.0; particulas_humo.clear()

            elif estado_juego == "INPUT_NOMBRE":
                if event.key == pygame.K_RETURN:
                    if texto_nombre.strip() == "": texto_nombre = "Piloto"
                    lc_str = "ON" if launch_control_activo else "OFF"
                    
                    with open("tiempos.txt", "a", encoding="utf-8") as f:
                        f.write(f"{coche_actual.nombre},{int(meta_metros)},{lc_str},{texto_nombre},{tiempo_carrera:.3f}\n")
                    
                    estado_juego = "MENU"
                    coche_actual = None; v_coche = 0.0; marcha_actual = 1
                    distancia_recorrida = 0.0; tiempo_carrera = 0.0; particulas_humo.clear()
                    
                elif event.key == pygame.K_BACKSPACE:
                    texto_nombre = texto_nombre[:-1]
                else:
                    if event.unicode.isprintable() and event.unicode != "," and len(texto_nombre) < 10:
                        texto_nombre += event.unicode

            elif estado_juego in ["CARRERA", "FIN"]:
                if event.key == pygame.K_UP and marcha_actual < 6:
                    marcha_actual += 1
                elif event.key == pygame.K_DOWN and marcha_actual > 1:
                    rpm_al_bajar = coche_actual.rpm_desde_velocidad(v_coche, marcha_actual - 1)
                    if rpm_al_bajar <= 8500:
                        marcha_actual -= 1

    # --- CONTROLES PROGRESIVOS ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT] and estado_juego in ["SEMAFORO", "CARRERA", "FIN"]:
        acelerador = min(acelerador + 0.05, 1.0) 
    else:
        acelerador = max(acelerador - 0.1, 0.0) 
        
    if keys[pygame.K_LEFT] and estado_juego in ["SEMAFORO", "CARRERA", "FIN"]:
        freno = min(freno + 0.1, 1.0)
    else:
        freno = max(freno - 0.2, 0.0)

    # 2. LÓGICA DE ESTADOS
    tiempo_actual = pygame.time.get_ticks()
    
    if estado_juego == "SEMAFORO":
        tiempo_transcurrido = (tiempo_actual - tiempo_inicio_juego) / 1000.0
        if v_coche > 0.1:
            estado_juego = "NULA"
        elif tiempo_transcurrido >= tiempo_verde:
            estado_juego = "CARRERA"

    # 3. FÍSICAS COMPLETAS
    derrapando = False  
    
    if estado_juego in ["SEMAFORO", "CARRERA", "FIN", "INPUT_NOMBRE"] and coche_actual is not None:
        rpm = coche_actual.rpm_desde_velocidad(v_coche, marcha_actual)
        if rpm > 8500:
            rpm = 8500; ft = 0 
        else:
            rpm = max(rpm, 1000); ft = acelerador * coche_actual.fuerza_empuje(rpm, marcha_actual)

        fm = 0 if acelerador > 0 else 500  
        fuerza_frenado = freno * 15000.0  
        fd = coche_actual.fuerza_aire(v_coche)
        fr = coche_actual.fuerza_rodadura()
        
        # --- LÓGICA DE DERRAPE Y LAUNCH CONTROL DEFINITIVA ---
        # Neumáticos deportivos de calle (Semi-slicks)
        mu = 0.9 
        
        # Transferencia dinámica de pesos realista para coches de motor delantero:
        # Al acelerar a fondo, alrededor del 70% del peso recae sobre las ruedas traseras.
        friccion_maxima = (coche_actual.masa * 9.81 * 0.70) * mu
        
        if launch_control_activo:
            if ft > friccion_maxima: ft = friccion_maxima * 0.99  
        else:
            if ft > friccion_maxima and v_coche < 15: 
                derrapando = True
                # Si patina, la fricción cae (fricción cinética), pero mantiene un empuje decente
                ft = friccion_maxima * 0.80 
        # ------------------------------------
        
        if estado_juego == "INPUT_NOMBRE": acelerador = 0; freno = 0.5 
            
        a_coche = (ft - fd - fr - fm - fuerza_frenado) / coche_actual.masa
        v_coche += dt * a_coche
        v_coche = max(0, v_coche)

        if estado_juego == "CARRERA":
            tiempo_carrera += dt
            distancia_recorrida += v_coche * dt
            if distancia_recorrida >= meta_metros:
                estado_juego = "FIN"
                
        elif estado_juego in ["FIN", "INPUT_NOMBRE"]:
            distancia_recorrida += v_coche * dt

    # 4. RENDERIZADO
    screen.fill((30, 30, 30))

    if estado_juego == "MENU":
        offset_menu = (tiempo_actual / 1000.0) * (px_por_metro * 0.8)
        
        dibujar_capa_parallax(screen, img_back, offset_menu, 0.02)
        dibujar_capa_parallax(screen, img_sun, offset_menu, 0.03)
        dibujar_capa_parallax(screen, img_buildings, offset_menu, 0.08)
        dibujar_capa_parallax(screen, img_palms, offset_menu, 0.3)
        dibujar_capa_parallax(screen, img_palm_tree, offset_menu, 0.5)
        dibujar_capa_parallax(screen, img_highway, offset_menu, 1.0)
        
        s_menu = pygame.Surface((WIDTH, HEIGHT))
        s_menu.set_alpha(170) 
        s_menu.fill((10, 10, 25))
        screen.blit(s_menu, (0, 0))

        text_titulo = font_huge.render("DRAG RACE", True, (255, 255, 255))
        screen.blit(text_titulo, (WIDTH//2 - text_titulo.get_width()//2, 20))
        
        alpha_pulso = int(abs(math.sin(tiempo_actual / 300.0)) * 255)
        instrucciones = font.render("Pulsa 1, 2 o 3 para elegir tu coche:", True, (0, 255, 255))
        instrucciones.set_alpha(max(50, alpha_pulso)) 
        screen.blit(instrucciones, (WIDTH//2 - instrucciones.get_width()//2, 100))
        
        txt_pista = "Infinita" if meta_metros == float('inf') else f"{int(meta_metros)} m"
        instrucciones_pista = font_small.render(f"Pista actual: {txt_pista} (Pulsa 'L' para cambiar)", True, (200, 200, 200))
        screen.blit(instrucciones_pista, (WIDTH//2 - instrucciones_pista.get_width()//2, 130))

        txt_lc = "ON" if launch_control_activo else "OFF"
        color_lc = (0, 255, 0) if launch_control_activo else (150, 150, 150)
        instrucciones_lc = font_small.render(f"Launch Control: {txt_lc} (Pulsa 'C' para cambiar)", True, color_lc)
        screen.blit(instrucciones_lc, (WIDTH//2 - instrucciones_lc.get_width()//2, 155))
        
        instrucciones_leaderboard = font_small.render("Pulsa 'T' para ver los Mejores Tiempos", True, (255, 215, 0))
        screen.blit(instrucciones_leaderboard, (WIDTH//2 - instrucciones_leaderboard.get_width()//2, 180))

        # --- TARJETAS DE SELECCIÓN DE COCHES ---
        pygame.draw.rect(screen, (80, 0, 0), (100, 210, 240, 160), border_radius=10) 
        pygame.draw.rect(screen, (255, 50, 50), (100, 210, 240, 160), 2, border_radius=10) 
        screen.blit(font_big.render("[1] Ferrari", True, (255, 255, 255)), (110, 215))
        screen.blit(img_ferrari_menu, (115, 260)) 
        screen.blit(font_small.render(f"Peso: {ferrari.masa} kg", True, (200, 200, 200)), (110, 345))

        pygame.draw.rect(screen, (0, 80, 0), (380, 210, 240, 160), border_radius=10)
        pygame.draw.rect(screen, (50, 255, 50), (380, 210, 240, 160), 2, border_radius=10)
        screen.blit(font_big.render("[2] Mustang", True, (255, 255, 255)), (390, 215))
        screen.blit(img_mustang_menu, (395, 260))
        screen.blit(font_small.render(f"Peso: {mustang.masa} kg", True, (200, 200, 200)), (390, 345))

        pygame.draw.rect(screen, (0, 0, 100), (660, 210, 240, 160), border_radius=10)
        pygame.draw.rect(screen, (50, 50, 255), (660, 210, 240, 160), 2, border_radius=10)
        screen.blit(font_big.render("[3] Skyline", True, (255, 255, 255)), (670, 215))
        screen.blit(img_skyline_menu, (675, 260))
        screen.blit(font_small.render(f"Peso: {skyline.masa} kg", True, (200, 200, 200)), (670, 345))

    elif estado_juego == "LEADERBOARD":
        screen.fill((20, 20, 40)) 
        titulo = font_huge.render("MEJORES TIEMPOS", True, (255, 215, 0))
        screen.blit(titulo, (WIDTH//2 - titulo.get_width()//2, 30))
        
        x_pos = 180; x_coche = 260; x_pista = 420; x_lc = 530; x_nombre = 620; x_tiempo = 760

        screen.blit(font.render("POS", True, (0, 255, 255)), (x_pos, 120))
        screen.blit(font.render("COCHE", True, (0, 255, 255)), (x_coche, 120))
        screen.blit(font.render("PISTA", True, (0, 255, 255)), (x_pista, 120))
        screen.blit(font.render("LC", True, (0, 255, 255)), (x_lc, 120))
        screen.blit(font.render("NOMBRE", True, (0, 255, 255)), (x_nombre, 120))
        screen.blit(font.render("TIEMPO", True, (0, 255, 255)), (x_tiempo, 120))

        pygame.draw.line(screen, (0, 255, 255), (150, 150), (860, 150), 2)
        
        if not tiempos_cargados:
            vacio = font.render("Aún no hay tiempos registrados.", True, (150, 150, 150))
            screen.blit(vacio, (WIDTH//2 - vacio.get_width()//2, 200))
        else:
            for i, t in enumerate(tiempos_cargados[:7]): 
                y_fila = 160 + (i * 30)
                
                nombre_completo = t[0].lower()
                if "ferrari" in nombre_completo: nombre_corto = "Ferrari"
                elif "mustang" in nombre_completo: nombre_corto = "Mustang"
                elif "skyline" in nombre_completo: nombre_corto = "Skyline"
                else: nombre_corto = t[0][:10] 
                
                screen.blit(font.render(str(i+1), True, (255, 255, 255)), (x_pos, y_fila))
                screen.blit(font.render(nombre_corto, True, (255, 255, 255)), (x_coche, y_fila))
                screen.blit(font.render(f"{t[1]}m", True, (255, 255, 255)), (x_pista, y_fila))
                screen.blit(font.render(t[2], True, (255, 255, 255)), (x_lc, y_fila))
                screen.blit(font.render(t[3], True, (255, 255, 255)), (x_nombre, y_fila))
                screen.blit(font.render(f"{t[4]}s", True, (255, 255, 255)), (x_tiempo, y_fila))
                
        msg_volver = font_small.render("Pulsa ESC para volver al menú", True, (150, 150, 150))
        screen.blit(msg_volver, (WIDTH//2 - msg_volver.get_width()//2, HEIGHT - 40))

    else:
        # --- PANTALLA DE CARRERA Y DERIVADOS (Parallax) ---
        offset_base = distancia_recorrida * px_por_metro
        
        dibujar_capa_parallax(screen, img_back, offset_base, 0.02)
        dibujar_capa_parallax(screen, img_sun, offset_base, 0.03)
        dibujar_capa_parallax(screen, img_buildings, offset_base, 0.08)
        dibujar_capa_parallax(screen, img_palms, offset_base, 0.3)
        dibujar_capa_parallax(screen, img_palm_tree, offset_base, 0.5)
        dibujar_capa_parallax(screen, img_highway, offset_base, 1.0)

        if coche_actual == ferrari:
            img_carroceria = img_ferrari_body; img_rueda = img_ferrari_rueda
            posicion_carroceria = (100, 255); centro_trasera = (151, 329); centro_delantera = (336, 329)     
        elif coche_actual == mustang:
            img_carroceria = img_mustang_body; img_rueda = img_mustang_rueda
            posicion_carroceria = (100, 264); centro_trasera = (168, 329); centro_delantera = (343, 329)
        elif coche_actual == skyline:
            img_carroceria = img_skyline_body; img_rueda = img_skyline_rueda
            posicion_carroceria = (100, 264); centro_trasera = (163, 329); centro_delantera = (335, 329)

        if derrapando and estado_juego == "CARRERA" and random.random() < 0.3: 
            particulas_humo.append([centro_trasera[0], centro_trasera[1] + 15, 4.0, 150.0])

        for particula in particulas_humo:
            particula[0] -= (v_coche * px_por_metro) * dt; particula[0] -= 2; particula[1] -= 1 
            particula[2] += 0.8; particula[3] -= 6 
            if particula[3] > 0:
                radio = int(particula[2])
                surf_humo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_humo, (200, 200, 200, int(particula[3])), (radio, radio), radio)
                screen.blit(surf_humo, (int(particula[0]) - radio, int(particula[1]) - radio))
        particulas_humo = [p for p in particulas_humo if p[3] > 0]

        screen.blit(img_carroceria, posicion_carroceria)
        circunferencia = 2 * math.pi * coche_actual.radio_rueda
        angulo_grados = -(distancia_recorrida / circunferencia) * 360  
        rueda_rotada = pygame.transform.rotate(img_rueda, angulo_grados)
        screen.blit(rueda_rotada, rueda_rotada.get_rect(center=centro_trasera).topleft)
        screen.blit(rueda_rotada, rueda_rotada.get_rect(center=centro_delantera).topleft)

        # --- HUD ---
        s = pygame.Surface((350, 195))
        s.set_alpha(150); s.fill((0, 0, 0))
        screen.blit(s, (10, 10))

        color_rpm = (255, 0, 0) if rpm > 8000 else (255, 255, 255)
        screen.blit(font_big.render(f"{v_coche * 3.6:.0f} km/h", True, (255, 255, 255)), (20, 20))
        screen.blit(font_big.render(f"RPM: {rpm:.0f}", True, color_rpm), (20, 60))
        screen.blit(font.render(f"Marcha: {marcha_actual}", True, (200, 200, 200)), (230, 65))
        txt_meta_hud = "∞" if meta_metros == float('inf') else f"{int(meta_metros)}m"
        screen.blit(font.render(f"{distancia_recorrida:.0f}m / {txt_meta_hud}", True, (255, 255, 0)), (20, 100))
        screen.blit(font_big.render(f"{tiempo_carrera:.2f}s", True, (0, 255, 255)), (20, 125))
        
        screen.blit(font.render("Acelerador:", True, (200, 200, 200)), (20, 170))
        pygame.draw.rect(screen, (255, 255, 255), (180, 175, 150, 18), 2)  
        if acelerador > 0: pygame.draw.rect(screen, (0, 200, 0), (182, 177, int(acelerador * 146), 14)) 
        
        screen.blit(font_small.render(f"Vehículo: {coche_actual.nombre}", True, (200, 200, 200)), (WIDTH - 350, 20))
        color_lc_hud = (0, 255, 0) if launch_control_activo else (150, 150, 150)
        screen.blit(font_small.render("LC: ON" if launch_control_activo else "LC: OFF", True, color_lc_hud), (WIDTH - 350, 45))
        color_derrape = (255, 0, 0) if derrapando else (0, 255, 0)
        screen.blit(font_small.render("Derrapando: SÍ" if derrapando else "Derrapando: NO", True, color_derrape), (WIDTH - 350, 70))

        # --- EVENTOS DENTRO DE CARRERA ---
        if estado_juego == "SEMAFORO":
            t_semaforo = (tiempo_actual - tiempo_inicio_juego) / 1000.0
            pygame.draw.rect(screen, (30, 30, 30), (WIDTH//2 - 60, 50, 120, 100), border_radius=10)
            pygame.draw.circle(screen, (255, 0, 0) if t_semaforo > 0.5 else (50, 0, 0), (WIDTH//2 - 30, 100), 15)
            pygame.draw.circle(screen, (255, 0, 0) if t_semaforo > 1.5 else (50, 0, 0), (WIDTH//2, 100), 15)
            pygame.draw.circle(screen, (255, 0, 0) if t_semaforo > 2.5 else (50, 0, 0), (WIDTH//2 + 30, 100), 15)

        elif estado_juego == "CARRERA" and (tiempo_actual - tiempo_inicio_juego) / 1000.0 < (tiempo_verde + 1.0):
            pygame.draw.rect(screen, (30, 30, 30), (WIDTH//2 - 60, 50, 120, 100), border_radius=10)
            pygame.draw.circle(screen, (0, 255, 0), (WIDTH//2, 100), 30)

        elif estado_juego == "NULA":
            v_coche = 0 
            screen.blit(font_huge.render("¡SALIDA NULA!", True, (255, 0, 0)), (WIDTH//2 - 250, HEIGHT//2 - 50))
            screen.blit(font.render("Pulsa ESC para volver al menú", True, (200, 200, 200)), (WIDTH//2 - 180, HEIGHT//2 + 20))
            if pygame.key.get_pressed()[pygame.K_ESCAPE]:
                estado_juego = "MENU"; coche_actual = None; v_coche = 0.0; marcha_actual = 1
                distancia_recorrida = 0.0; tiempo_carrera = 0.0; particulas_humo.clear()

        # ==============================================================
        # ESTADO FIN CON TEXTO PARPADEANTE
        # ==============================================================
        elif estado_juego == "FIN":
            screen.blit(font_huge.render("¡META!", True, (255, 215, 0)), (WIDTH//2 - 120, HEIGHT//2 - 60))
            screen.blit(font_big.render(f"Tiempo final: {tiempo_carrera:.3f} s", True, (255, 255, 255)), (WIDTH//2 - 180, HEIGHT//2 + 20))
            
            # Efecto de parpadeo (pulso) matemático
            alpha_pulso = int(abs(math.sin(tiempo_actual / 300.0)) * 255)
            txt_guardar = font.render("Pulsa ENTER para guardar o ESC para descartar", True, (0, 255, 255))
            txt_guardar.set_alpha(max(50, alpha_pulso))
            screen.blit(txt_guardar, (WIDTH//2 - txt_guardar.get_width()//2, HEIGHT//2 + 70))

        elif estado_juego == "INPUT_NOMBRE":
            s_osc = pygame.Surface((WIDTH, HEIGHT))
            s_osc.set_alpha(150); s_osc.fill((0, 0, 0))
            screen.blit(s_osc, (0, 0))
            
            pygame.draw.rect(screen, (20, 20, 20), (WIDTH//2 - 250, HEIGHT//2 - 120, 500, 240), border_radius=10)
            pygame.draw.rect(screen, (0, 255, 255), (WIDTH//2 - 250, HEIGHT//2 - 120, 500, 240), 2, border_radius=10)
            
            t1 = font_big.render("¡NUEVO RÉCORD!", True, (255, 215, 0))
            t2 = font.render("Introduce tu nombre y pulsa ENTER:", True, (200, 200, 200))
            t3 = font_huge.render(texto_nombre + "_", True, (0, 255, 255))
            
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//2 - 100))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 - 40))
            screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2 + 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()