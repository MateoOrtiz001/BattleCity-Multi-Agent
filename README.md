# BattleCity-Multi-Agent
Un agente basado en búsqueda adversaria para jugar el clásico juego Battle City.


## Vídeo de muestra
Ejemplo del agente a velocidad $\times 8$.

[![Vídeo de Muestra](https://img.youtube.com/vi/Zb67iN6kHw8/sddefault.jpg)](https://youtube.com/shorts/Zb67iN6kHw8?feature=share)

## Ejecutar el visual tester
Puedes lanzar una simulación visual usando `visual_test.py`. El script acepta argumentos para elegir el algoritmo, la profundidad, el nivel y el tiempo límite por decisión.

Ejemplos (PowerShell):

```powershell
# Ejecutar con los valores por defecto (expectimax, depth=3, level=1, time=10s)
python visual_test.py

# Expectimax profundidad 4 nivel 2 con 5s por decisión
python visual_test.py -a expectimax -d 4 -l 2 -t 5

# Alpha-beta profundidad 3 nivel 1
python visual_test.py -a alphabeta -d 3 -l 1

# Minimax profundidad 2 nivel 3 (se ajusta time_limit por atributo)
python visual_test.py -a minimax -d 2 -l 3 -t 2.5
```

Argumentos disponibles:
- `--algorithm/-a`: `minimax`, `alphabeta`, `expectimax` (por defecto: `expectimax`).
- `--depth/-d`: Número de profundidad en turnos completos (entero, por defecto: 3).
- `--level/-l`: Nivel a simular (1..4, por defecto: 1).
- `--time/-t`: Límite de tiempo por decisión en segundos (float, por defecto: 10.0).


## Instalar dependencias

He incluido un `requirements.txt` con las dependencias principales usadas por el proyecto. La forma más sencilla de instalarlas es:

```powershell
# Instalar con pip (Windows PowerShell)
python -m pip install -r requirements.txt
```

Notas específicas por paquete:
- `pygame`: interfaz gráfica. En Windows suele instalarse bien con pip.
- `numba`: se usa en `src/utils/util.py`. En Windows puede ser más fiable instalar con conda si tienes Anaconda/Miniconda:

```powershell
conda install -c conda-forge numba
```

- `numpy`: dependencia requerida por `numba` y usada internamente.

Si encuentras problemas al instalar `numba` con pip en Windows, recomiendo usar conda o instalar las dependencias de compilación (Visual C++ Build Tools). Si quieres, puedo añadir una sección con pasos detallados para entornos Windows o para crear un entorno virtual recomendado.
