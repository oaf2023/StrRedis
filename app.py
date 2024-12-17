import streamlit as st
import redis
import json
from datetime import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode 
import os
import time
# Conectar a Redis
#redis_client = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)
#redis_client = redis.StrictRedis(host="192.168.151.58", port=6379, password="montecristo", db=10, decode_responses=True)

# Variables globales para el caché
cached_tasks = None
last_key_count = None
bd_old = None

###### Nuevo



def load_tasks_to_dataframe(redis_client):
    """
    Leer todas las tareas de Redis y cargarlas en un DataFrame de Pandas.
    Utiliza caché almacenado en st.session_state para mejorar el rendimiento.
    """
    # Inicializar variables en st.session_state si no existen
    if "cached_tasks_df" not in st.session_state:
        st.session_state.cached_tasks_df = None
        st.session_state.last_key_count = None

    # Obtener el número de claves actuales en Redis
    info = redis_client.info("keyspace")
    dbase = f"db{numeros}"
    key_count = info.get(dbase, {}).get("keys", 0)

    # Verificar si hay cambios en Redis o si es la primera vez
    if st.session_state.last_key_count == key_count and st.session_state.cached_tasks_df is not None:
        #st.info("Cargando tareas desde caché...")
        return st.session_state.cached_tasks_df

    # Si hay cambios, recargar los datos desde Redis
    #st.info("Cargando tareas desde Redis...")
    patterns = ["task:*", "celery-task-meta-*"]  # Patrones de claves
    task_keys = set()

    for pattern in patterns:
        task_keys.update(redis_client.scan_iter(pattern))

    tasks = []

    for key in task_keys:
        task_data = None
        task_type = None

        # Intentar cargar como JSON
        task_data = redis_client.get(key)
        if task_data:
            try:
                task = json.loads(task_data)
                task_type = "JSON"
            except json.JSONDecodeError:
                task = None

        # Si no es JSON, intentar como hash
        if not task:
            task_data = redis_client.hgetall(key)
            if task_data:
                task = task_data
                task_type = "Hash"

        if task:
            task["key"] = key
            task["type"] = task_type
            tasks.append(task)

    # Crear el DataFrame
    if tasks:
        df = pd.DataFrame(tasks)
        required_columns = ["key", "type", "status", "result", "args", "kwargs"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
    else:
        df = pd.DataFrame(columns=["key", "type", "status", "result", "args", "kwargs"])

    # Actualizar el caché en st.session_state
    st.session_state.cached_tasks_df = df
    st.session_state.last_key_count = key_count

    st.info("Tareas cargadas y caché actualizado.")
    return df




def load_tasks_to_dataframe_old1(redis_client):
    """
    Leer todas las tareas de Redis y cargarlas en un DataFrame de Pandas.
    Incluye una columna adicional para identificar si cada tarea está almacenada como JSON o hash.
    Utiliza un sistema de caché para mejorar el rendimiento.
    """
    global cached_tasks_df, last_key_count

    # Obtener información sobre la cantidad de claves
    info = redis_client.info("keyspace")
    dbase = f"db{numeros}"
    key_count = info.get(dbase, {}).get("keys", 0)  # Claves en la base de datos db0

    # Si no hay cambios y hay caché, devolver el DataFrame en caché
    if last_key_count == key_count and cached_tasks_df is not None:
        st.write("Cargando tareas desde caché...")
        return cached_tasks_df

    st.write("Cargando tareas desde Redis...")
    # Si hay cambios, actualizar el caché
    patterns = ["task:*", "celery-task-meta-*"]  # Patrones de las claves de tareas
    task_keys = set()  # Usar un conjunto para evitar duplicados

    # Combinar claves de todos los patrones
    for pattern in patterns:
        task_keys.update(redis_client.scan_iter(pattern))

    tasks = []  # Lista para almacenar los datos de las tareas

    # Iterar sobre cada clave y recuperar sus datos
    for key in task_keys:
        task_data = None
        task_type = None

        # Intentar obtener la tarea como JSON
        task_data = redis_client.get(key)
        if task_data:
            try:
                task = json.loads(task_data)  # Decodificar JSON si está presente
                task_type = "JSON"  # Identificar como JSON
            except json.JSONDecodeError:
                task = None  # No es JSON

        # Si no es JSON, intentar obtenerla como hash
        if not task:
            task_data = redis_client.hgetall(key)
            if task_data:
                task = task_data  # Asignar datos del hash
                task_type = "Hash"  # Identificar como hash

        # Si se obtuvo la tarea, agregar al listado
        if task:
            task["key"] = key  # Agregar la clave al diccionario
            task["type"] = task_type  # Agregar el tipo de la tarea
            tasks.append(task)

    # Crear el DataFrame
    if tasks:
        df = pd.DataFrame(tasks)

        # Asegurar que las columnas clave estén presentes
        required_columns = ["key", "type", "status", "result", "args", "kwargs"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
    else:
        # DataFrame vacío con columnas predefinidas
        df = pd.DataFrame(columns=["key", "type", "status", "result", "args", "kwargs"])

    # Actualizar caché
    cached_tasks_df = df
    last_key_count = key_count

    st.write("Tareas cargadas y caché actualizado.")
    return df


def load_tasks_to_dataframe_old(redis_client):
    """
    Leer todas las tareas de Redis y cargarlas en un DataFrame de Pandas.
    Incluye una columna adicional para identificar si cada tarea está almacenada como JSON o hash.
    """
    # Obtener todas las claves relacionadas con tareas
    patterns = ["task:*", "celery-task-meta-*"]  # Patrones de las claves de tareas
    task_keys = set()  # Usar un conjunto para evitar duplicados

    # Combinar claves de todos los patrones
    for pattern in patterns:
        task_keys.update(redis_client.scan_iter(pattern))

    tasks = []  # Lista para almacenar los datos de las tareas

    # Iterar sobre cada clave y recuperar sus datos
    for key in task_keys:
        task_data = None
        task_type = None

        # Intentar obtener la tarea como JSON
        task_data = redis_client.get(key)
        if task_data:
            try:
                task = json.loads(task_data)  # Decodificar JSON si está presente
                task_type = "JSON"  # Identificar como JSON
            except json.JSONDecodeError:
                task = None  # No es JSON

        # Si no es JSON, intentar obtenerla como hash
        if not task:
            task_data = redis_client.hgetall(key)
            if task_data:
                task = task_data  # Asignar datos del hash
                task_type = "Hash"  # Identificar como hash

        # Si se obtuvo la tarea, agregar al listado
        if task:
            task["key"] = key  # Agregar la clave al diccionario
            task["type"] = task_type  # Agregar el tipo de la tarea
            tasks.append(task)

    # Crear el DataFrame
    if tasks:
        df = pd.DataFrame(tasks)

        # Asegurar que las columnas clave estén presentes
        required_columns = ["key", "type", "status", "result"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = None

    else:
        # DataFrame vacío con columnas predefinidas
        df = pd.DataFrame(columns=["key", "type", "status", "result", "args", "kwargs"])

    # Agregar columna "Acción" con valores predeterminados
    #df["Acción"] = "Ninguna"

    return df
 
######





def prepare_dataframe_for_streamlit(df):
    """
    Ajusta los tipos de datos del DataFrame para que sean compatibles con Streamlit.
    """
    # Convertir columnas no numéricas a cadenas
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)

    return df

def highlight_status(val):
    if val == "SUCCESS":
        return "color: lightgreen;"
    elif val == "FAILED":
        return "color: red;"
    elif val == "PENDING":
        return "color: orange;" 
    return ""


def delete_task(task_id):
    """
    Borrar una tarea específica de Redis.
    """
    
    task_key = f"task:{task_id}"
    if redis_client.exists(task_key):
        redis_client.delete(task_key)
        st.write(f"Tarea {task_id} eliminada.")
    else:
        task_key = f"celery-task-meta-{task_id}"

        if redis_client.exists(task_key):
            redis_client.delete(task_key)
            print(f"Tarea {task_id} eliminada de Redis.")
        else:
            st.write(f"La tarea {task_id} no existe en Redis ni en Celery ni en tareas creadas.")
        
##
def get_task_details(task_id):
    """
    Recuperar los detalles de una tarea específica desde Redis.
    Maneja tareas almacenadas como JSON o como hash.
    """
    task_key = f"task:{task_id}"
    task_key_c = f"celery-task-meta-{task_id}"
    task_details = None
    task_type = None

    # Intentar obtener la tarea como JSON
    task_data = redis_client.get(task_key)
    if task_data:
        try:
            # Si se puede decodificar como JSON, asignar los detalles
            task_details = json.loads(task_data)
            task_type = "JSON"
        except json.JSONDecodeError:
            pass  # Continuar si no es JSON válido
    else:
        task_data = redis_client.hgetall(task_key_c)
        # Si no es JSON, intentar obtenerla como hash
        if task_data is None:
            if task_data:
                task_details = task_data
                task_type = "Hash"
                return {
                        "task_id": task_id,
                        "status": task_data.get("status", None),
                        "result": task_data.get("result", None),
                        "traceback": task_data.get("traceback", None),
                        "children": task_data.get("children", None),
                        "date_done": task_data.get("date_done", None),
                        "key": task_data.get("key", None),
                        "type": task_type,
                        "parent_id": task_data.get("parent_id", None),
                        "group_id": task_data.get("group_id", None),
                        "args": task_data.get("args", None),
                        "kwargs": task_data.get("kwargs", None),
                        "details": task_details,
                        "message": f"Tarea {task_id} encontrada como {task_type}.",
                        "exists": True,
                    }
            else:
                return {
                        "task_id": task_id,
                        "type": None,
                        "details": None,
                        "message": f"Tarea {task_id} no encontrada en Redis.",
                        "exists": False,
                    }
                
    return {
            "task_id": task_id,
            "type": task_type,
            "details": task_details,
            "message": f"Tarea {task_id} encontrada como {task_type}.",
            "exists": True,
        }
    # Retornar los datos encontrados o un mensaje si no existe
    # if task_details:
    #     return {
    #         "task_id": task_id,
    #         "type": task_type,
    #         "details": task_details,
    #         "message": f"Tarea {task_id} encontrada como {task_type}.",
    #         "exists": True,
    #     }
    # else:
    #     return {
    #         "task_id": task_id,
    #         "type": None,
    #         "details": None,
    #         "message": f"Tarea {task_id} no encontrada en Redis.",
    #         "exists": False,
    #     }

## Backups

def backup_tasks(backup_dir="C:\\Backups"):
    """
    Realiza un backup de todas las tareas almacenadas en Redis.
    Guarda las tareas en un archivo JSON en una carpeta local.
    """
    # Verificar si la carpeta de backups existe, si no, crearla
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        st.write(f"Carpeta creada: {backup_dir}")

    patterns = ["task:*", "celery-task-meta-*"]  # Patrones de las claves de tareas
    task_keys = set()  # Usar un conjunto para evitar duplicados

    # Combinar claves de todos los patrones
    for pattern in patterns:
        task_keys.update(redis_client.scan_iter(pattern))

    
    #task_keys = redis_client.scan_iter("task:*")
    tasks = []

    # Extraer todas las tareas
    for key in task_keys:
        task_data = redis_client.get(key)
        if task_data:
            try:
                task = json.loads(task_data)
                tasks.append({"key": key, "data": task, "type": "JSON"})
            except json.JSONDecodeError:
                # Si no es JSON, intentar como hash
                task_data = redis_client.hgetall(key)
                if task_data:
                    tasks.append({"key": key, "data": task_data, "type": "Hash"})

    # Generar el nombre del archivo con la fecha actual
    filename = f"backup_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    full_path = os.path.join(backup_dir, filename)

    # Guardar los datos en un archivo JSON
    with open(full_path, "w") as file:
        json.dump(tasks, file, indent=4)

    st.write(f"Backup completado: {full_path}")
    return full_path


## Restaurar Backup
def restore_tasks():
    # Título de la página
    st.title("Restaurar Tareas en Redis")

    # Subir el archivo JSON
    uploaded_file = st.file_uploader("Selecciona un archivo de backup (.json)", type=["json"])

    if uploaded_file:
        try:
            # Leer y cargar los datos del archivo JSON
            tasks = json.load(uploaded_file)

            # Mostrar un resumen del archivo cargado
            st.success(f"Archivo '{uploaded_file.name}' cargado exitosamente.")
            st.write(f"Número de tareas en el archivo: **{len(tasks)}**")

            # Botón para restaurar las tareas
            if st.button("Restaurar Tareas"):
                for task in tasks:
                    key = task["key"]
                    data = task["data"]
                    task_type = task["type"]

                    # Restaurar en Redis según el tipo
                    if task_type == "JSON":
                        redis_client.set(key, json.dumps(data))
                    elif task_type == "Hash":
                        redis_client.hset(key, mapping=data)

                    st.write(f"Tarea restaurada: `{key}` ({task_type})")

                st.success("Todas las tareas han sido restauradas en Redis.")

        except json.JSONDecodeError as e:
            st.error(f"Error al leer el archivo JSON: {e}")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")
    else:
        st.info("Por favor, sube un archivo de backup en formato JSON.")




# Configuración inicial de la página
st.set_page_config(
    page_title="Monitor Redis",
    page_icon="🔄",
    layout="wide"
)

# Mostrar el título inicial
st.sidebar.markdown('<p style="font-size:18px; color:gray;">Verificando conexión ☑</p>', unsafe_allow_html=True)

try:
    # Intentar conectar a Redis
    #redis_client = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)
    # Obtener información del keyspace
    redis_client = redis.StrictRedis(host="192.168.151.58", port=6379, password="montecristo", decode_responses=True)
    redis_client.ping()
    # Si la conexión es exitosa
    st.sidebar.markdown('<p style="font-size:18px; color:black;">Redis Verificado ✅</p>', unsafe_allow_html=True)
    
    info = redis_client.info("keyspace")
    databases = [key for key in info.keys() if key.startswith("db")]
    selected_db = st.selectbox("Selecciona una base de datos:", databases)
    numeros = int(''.join([c for c in selected_db if c.isdigit()]))
    st.write(f"Base de datos seleccionada: {selected_db}")
    
    redis_client = redis.StrictRedis(host="192.168.151.58", port=6379, password="montecristo", db=numeros, decode_responses=True)
    redis_client.ping()
    st.sidebar.markdown('<p style="font-size:18px; color:black;">Base de datos ✅</p>', unsafe_allow_html=True)
    info = redis_client.info()
    clients = redis_client.client_list()
    
    
except redis.ConnectionError as e:
    # Si la conexión falla
    st.sidebar.markdown('<p style="font-size:18px; color:black;">Sin conexión a Redis ❌</p>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<p style="font-size:18px; color:black;">Detalles del error: {e}</p>', unsafe_allow_html=True)
    


# Menú lateral
st.sidebar.title("Menu")

menu_options = ["Lista de Tareas", "Consulta", "Configuración", "Estadistica", "Backup", "Restauración"]
menu_selection = st.sidebar.radio("Selecciona una opción", menu_options)
st.sidebar.title("Info Server")
st.sidebar.write(info)
st.sidebar.title("Conexiones")
st.sidebar.write(clients)
#st.write(f"Bases de datos activas: {databases}")
# Renderizar contenido basado en el menú seleccionado
if menu_selection == "Lista de Tareas":
    st.header("Tareas en Redis")
    # Intervalo de actualización
    update_interval = st.sidebar.slider("Intervalo de actualización (segundos)", 1, 30, 5)

    # Contenedor principal
    placeholder = st.empty()

    # Bucle para actualización automática
    while True:
        # Cargar las tareas en un DataFrame
        tasks_df = load_tasks_to_dataframe(redis_client)
        tasks_df = prepare_dataframe_for_streamlit(tasks_df)
        if tasks_df.empty:
            st.warning("No hay tareas disponibles.")
            st.stop()
        
        #tasks_df["Accion"] = ""
        tasks_df = tasks_df.style.applymap(highlight_status, subset=["status"])
        # Actualizar la interfaz
        with placeholder.container():
            st.subheader("Estado Actual de las Tareas")
            if tasks_df:
                #st.data_editor(tasks_df, num_rows="dynamic", key="Nro")
                st.dataframe(tasks_df, width=1400, height=600)
            else:
                st.info("No hay tareas disponibles en Redis.")
    time.sleep(update_interval)
        
        
elif menu_selection == "Backup":
    confirmation = st.text_input("Confirma el Backup", help="Se confirma con S o s el Backup")
    if confirmation.lower() == "s":
        st.error(f"Backup...")
        backup_tasks()
    else:
        st.write("Operación cancelada.")
                
                
    
    
    
 
elif menu_selection == "Consulta":
    st.header("Visualización")
    with st.expander("Consulta de Tarea por Task_id:", expanded=True):
        with st.form("Consulta"):
            id_tasks = st.text_input("Task_id Tarea", help="El Task_id de la tarea en Redis")
            
            submit_button = st.form_submit_button(label="Consultar")
            if submit_button:
                #task_key = f"tasks:{id_tasks}"
                respuesta = get_task_details(id_tasks)
                st.write(respuesta)
                if id_tasks and respuesta['details'].get('type') =="Json":
                    #task_key = f"tasks:{id_tasks}"
                    st.write("Json")
                    st.write(respuesta)
                    # st.markdown(f"Detalles de la tarea: <span style='color:blue; font-size:20px; font-weight:bold;'>{id_tasks}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Nombre de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('name','sin nombre')}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Args de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('args')}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Kwargs de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('kwars')}</span>", unsafe_allow_html=True)
                    # if respuesta["details"].get('status') == ['FAILED', 'FAILURE']:
                    #     st.markdown(f"Status de la tarea: <span style='color:red; font-size:18px; font-weight:bold;'>{respuesta['details'].get('status')}</span>", unsafe_allow_html=True)
                    # else:
                    #     st.markdown(f"Status de la tarea: <span style='color:green; font-size:18px; font-weight:bold;'>{respuesta['details'].get('status')}</span>", unsafe_allow_html=True)    
                    # st.markdown(f"Resultado de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('result','No hay resultado')}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Error de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('error','No hay error')}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Worker de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('worker')}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Fecha creación de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['details'].get('created_at')}</span>", unsafe_allow_html=True)
                else:
                    st.write("Hash")
                    st.write(respuesta)
                    # st.markdown(f"Detalles de la tarea: <span style='color:blue; font-size:20px; font-weight:bold;'>{id_tasks}</span>", unsafe_allow_html=True)
                    # st.markdown(f"Nombre de la tarea: <span style='color:blue; font-size:18px; font-weight:bold;'>{respuesta['children']}</span>", unsafe_allow_html=True)
                       
                    #st.markdown(f"Resumen: <span style='color:green; font-size:12px; font-weight:bold;'>{json.dumps(respuesta, indent=4)}</span>", unsafe_allow_html=True)
                    #for key, value in respuesta["details"].items():
                    #    st.write(f"{key}: {value}")
                    #st.write(redis_client.hget(task_key, "status"))
            #status =  redis_client.hget(task_key, "status")       
            #st.write(redis_client.hget(task_key, "status"))
            action = st.selectbox("Acción:", ["Ninguna", "Reintentar", "Cancelar"])
            button = st.form_submit_button("Ejecutar Acción")
            if button:
                if action == "Reintentar":
                    task_data = redis_client.get(f"task_id:{task_id}")
                    if task_data:
                        task = json.loads(task_data)
                        task["status"] = "PENDING"
                        redis_client.set(f"task:{task_id}", json.dumps(task))
                        redis_client.rpush("task_queue", json.dumps(task))
                        st.success(f"Tarea {task_id} reenviada a la cola.")
                elif action == "Cancelar":
                    task_data = redis_client.get(f"task_id:{task_id}")
                    if task_data:
                        task = json.loads(task_data)
                        task["status"] = "CANCELLED"
                        redis_client.set(f"task:{task_id}", json.dumps(task))
                        st.success(f"Tarea {task_id} cancelada.")
                else:
                    st.warning("Por favor, selecciona una acción válida.")
elif menu_selection == "Configuración":
    st.header("Configuración")
    st.write("Agrega opciones para personalizar la aplicación.")
elif menu_selection == "Acerca de":
    st.header("Acerca de")
    st.write("Información sobre la aplicación y su propósito.")


