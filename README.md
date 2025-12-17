#  Fantasy story generator

Este proyecto es un framework de generación de historias que aprovecha los LLMs para generar narrativas de fantasía.

### Prerrequisitos

* Python 3.x instalado
* Una clave API de OpenRouter
* Instalar el modelo `en_core_web_sm` de Spacy: `python -m spacy download en_core_web_sm`

### Instalación

1. Clona el repositorio:
```bash
git clone <url_del_repositorio>
cd <directorio_del_repositorio>

```


2. Instala los paquetes de Python requeridos:
```bash
pip install -r requirements.txt

```


3. Configura la clave API de OpenRouter como una variable de entorno:
```bash
export OPENROUTER_API_KEY=<tu_clave_api_openrouter>

```

### Ejecución Local

1. Configura el archivo `requests.yml` con los parámetros de generación de historia deseados.
2. Ejecuta el script `run.py`:

Esto ejecutará el flujo de trabajo de generación de historias basado en la configuración en `requests.yml`. Los datos generados se guardarán en el directorio de salida.
