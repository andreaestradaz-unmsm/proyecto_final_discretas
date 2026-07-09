# 🎮 Tetris Educativo - Laboratorio de Matemática Discreta

¡Bienvenido al proyecto de **Tetris Educativo**! Este repositorio no es solo un clon web de Tetris; es un **laboratorio interactivo de Matemática Discreta**. Toda la lógica del juego (físicas, colisiones, borrado de líneas, piezas) se ejecuta en un servidor Backend escrito en **Python** puro y se renderiza en tiempo real en una interfaz de usuario HTML5 usando un servidor Flask.

El código fuente (principalmente `app.py`) contiene gigantescos comentarios diseñados para uso académico, donde se señala en tiempo real en qué bloque lógico se está aplicando cada principio matemático y computacional.

## 🧮 Conceptos de Matemática Discreta Aplicados

Este proyecto se desarrolló demostrando maestría en los siguientes temas:

1. **Sistemas de Numeración y Álgebra de Boole (Bitboards)**: La matriz del juego no es bidimensional. Se ha optimizado radicalmente para usar "Bitboards": un arreglo unidimensional de 20 enteros (donde cada fila es un binario de 10 bits).
2. **Conteo (Principio de Multiplicación)**: Cálculo del espacio de figuras finitas (7 Tetrominós x 4 posibles rotaciones).
3. **Eficiencia y Notación O(1)**: Evaluación de filas completadas comprobando la igualdad del entero base (1023) reduciendo la complejidad del peor caso de $O(N \times M)$ a $O(1)$ por fila.
4. **Teoría de Conjuntos**: Operaciones booleanas a nivel de bit (Operador `|` OR) para asentar las celdas de las piezas dentro del superconjunto del tablero general.
5. **Aritmética Modular**: Regulación del ciclo de rotación biyectivo empleando aritmética módulo 4 (`(estado + 1) % 4`).
6. **Sucesiones y Funciones por Partes**: Funciones discretas que controlan el sistema de puntaje según las líneas limpiadas de forma simultánea, y sucesiones geométricas para el aumento gradual de la gravedad.

---

## 🚀 Requisitos

Para poder ejecutar este proyecto de manera local solo requieres tener instalado:
* **Python 3.x**
* **Flask** (La librería estándar de Python para desarrollo Web)

## 🛠️ Instrucciones de Instalación y Ejecución

Sigue estos simples pasos para iniciar el proyecto después de clonar el repositorio:

### 1. Descarga el repositorio y abre la carpeta
Si descargaste el `.zip`, descomprímelo. Abre una terminal (o Símbolo del Sistema) y ubícate en la raíz del proyecto.

### 2. Crea y activa un entorno virtual (Recomendado)
Es una buena práctica en Python crear un entorno virtual para instalar dependencias sin afectar tu sistema global:

**En Windows (CMD o PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**En Mac o Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instala las dependencias
Una vez activado el entorno (verás un `(.venv)` a la izquierda en tu terminal), instala el framework Flask:
```bash
pip install flask
```

### 3. Inicia el servidor Backend
Ejecuta el archivo principal en Python, el cual actuará como el cerebro de las operaciones matemáticas del juego:
```bash
python app.py
```

### 4. ¡A jugar!
Si todo salió bien, la consola te avisará que el servidor está corriendo localmente. 
Abre tu navegador web favorito (Chrome, Firefox, Edge, etc.) e ingresa a:

👉 **http://127.0.0.1:5000**

## 🕹️ Controles

Una vez dentro de la página, usa las **Flechas del Teclado**:
* ⬅️ **Flecha Izquierda**: Mover bloque a la izquierda
* ➡️ **Flecha Derecha**: Mover bloque a la derecha
* ⬆️ **Flecha Arriba**: Rotar bloque 90 grados
* ⬇️ **Flecha Abajo**: Caída rápida (Acelerar gravedad)

---

> **Nota para estudiantes y profesores**: Si deseas auditar el código fuente, dirígete directamente al archivo `app.py`. Los comentarios educativos están resaltados con la etiqueta `CONCEPTO` en formato gigante para una fácil lectura.
