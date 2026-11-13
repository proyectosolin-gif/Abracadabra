from datetime import datetime
import urllib.parse
import pyodbc
import streamlit as st
from sqlalchemy import create_engine, text

# Configuración de la página
st.set_page_config(
    page_title="Registro de Fichas - Alumnos", page_icon="📝", layout="centered"
)


def obtener_conexion():
    drivers_instalados = pyodbc.drivers()
    driver_elegido = "SQL Server"
    for d in [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server",
    ]:
        if d in drivers_instalados:
            driver_elegido = d
            break

    try:
        server = st.secrets["db_credentials"]["SERVER"]
        database = st.secrets["db_credentials"]["DATABASE"]
        username = st.secrets["db_credentials"]["UID"]
        password = st.secrets["db_credentials"]["PWD"]
    except Exception:
        server = "CBTis139.mssql.somee.com"
        database = "CBTis139"
        username = "TovarLara_SQLLogin_1"
        password = "1hmetvyyiv"

    connection_string = (
        f"DRIVER={{{driver_elegido}}};SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password};TrustServerCertificate=yes;"
    )
    params = urllib.parse.quote_plus(connection_string)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


# Inicializar variables de sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "acceso_alumno" not in st.session_state:
    st.session_state.acceso_alumno = ""
if "fichas_guardadas" not in st.session_state:
    st.session_state.fichas_guardadas = 0

# --- PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🧠 Proyecto Abracadabra  CBTis 139")
    st.subheader("Acceso de Alumnos")

    with st.form("form_login"):
        codigo_ingresado = st.text_input(
            "Ingresa tu código de acceso (ej. 001):", max_chars=10
        ).strip()
        submit_btn = st.form_submit_button("Ingresar")

        if submit_btn:
            if not codigo_ingresado:
                st.warning("Por favor, introduce tu código de acceso.")
            else:
                try:
                    engine = obtener_conexion()
                    with engine.connect() as connection:
                        query = text(
                            "SELECT * FROM alumno WHERE acceso = :acceso"
                        )
                        result = connection.execute(
                            query, {"acceso": codigo_ingresado}
                        ).fetchone()

                        if result:
                            st.session_state.autenticado = True
                            st.session_state.acceso_alumno = codigo_ingresado
                            # Contar cuántas fichas ya tiene en la BD
                            count_query = text(
                                "SELECT COUNT(*) FROM Abracadaba WHERE idalumno = :idalumno"
                            )
                            total_previas = connection.execute(
                                count_query, {"idalumno": codigo_ingresado}
                            ).scalar()
                            st.session_state.fichas_guardadas = (
                                total_previas if total_previas else 0
                            )

                            st.success(
                                "¡Acceso autorizado! Cargando módulo..."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Código de acceso no encontrado. Verifica tus datos."
                            )
                except Exception as e:
                    st.error(f"Error al conectar con la base de datos: {e}")

# --- MÓDULO PRINCIPAL: REGISTRO DE FICHAS ---
else:
    # Barra lateral limpia para cerrar sesión
    st.sidebar.markdown(f"**Alumno:** `{st.session_state.acceso_alumno}`")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.acceso_alumno = ""
        st.session_state.fichas_guardadas = 0
        st.rerun()

    st.title("📝 Registro de Ficha Emocional")
    st.write("Captura tus fichas una por una.")

    # Cargar las emociones incluyendo la descripción desde la base de datos
    try:
        engine = obtener_conexion()
        with engine.connect() as connection:
            emisiones_query = text(
                "SELECT idemocion, Emocion, descripcion FROM Emocion ORDER BY idemocion"
            )
            resultado_emociones = connection.execute(emisiones_query).fetchall()

            dict_emociones = {
                row.idemocion: {
                    "nombre": row.Emocion,
                    "descripcion": (
                        row.descripcion
                        if row.descripcion
                        else "Sin descripción disponible."
                    ),
                }
                for row in resultado_emociones
            }

            opciones_select = {
                f"{row.idemocion} - {row.Emocion}": row.idemocion
                for row in resultado_emociones
            }
    except Exception as e:
        st.error(f"Error al cargar el catálogo de emociones: {e}")
        opciones_select = {}
        dict_emociones = {}

    if opciones_select:
        # 1. El selector de emoción está FUERA del formulario para que responda de inmediato
        emocion_seleccionada_texto = st.selectbox(
            "Selecciona la emoción (Clave - Nombre):",
            options=list(opciones_select.keys()),
        )
        idemocion_elegida = opciones_select[emocion_seleccionada_texto]

        # 2. La descripción cambia al instante en cuanto mueven el selector
        desc_actual = dict_emociones[idemocion_elegida]["descripcion"]
        st.info(f"💡 **¿Qué significa esta emoción?:** {desc_actual}")
    else:
        idemocion_elegida = ""
        st.warning("No se pudieron cargar las emociones de la base de datos.")

    # Usamos una clave dinámica basada en el contador para limpiar el formulario al recargar
    form_key = f"form_ficha_{st.session_state.fichas_guardadas}"

    with st.form(key=form_key):
        fecha_ficha = st.date_input(
            "Fecha correspondiente a la ficha", value=datetime.today()
        )

        motivo = st.text_area(
            "Motivo",
            placeholder="Describe brevemente el motivo...",
            max_chars=500,
        )

        # Contador en el extremo opuesto al botón de guardar
        col_contador, col_boton = st.columns([2, 1])

        with col_contador:
            st.markdown(
                f"📊 **Fichas guardadas:** `{st.session_state.fichas_guardadas} / 30`"
            )

        with col_boton:
            guardar_btn = st.form_submit_button(
                "Guardar esta Ficha", use_container_width=True
            )

        if guardar_btn:
            if not motivo.strip():
                st.warning("Por favor, describe el motivo antes de guardar.")
            elif not idemocion_elegida:
                st.warning("Por favor, selecciona una emoción válida.")
            else:
                try:
                    with engine.connect() as connection:
                        insert_query = text(
                            """
                            INSERT INTO Abracadaba (idalumno, fecha, idemocion, motivo)
                            VALUES (:idalumno, :fecha, :idemocion, :motivo)
                        """
                        )
                        connection.execute(
                            insert_query,
                            {
                                "idalumno": st.session_state.acceso_alumno,
                                "fecha": fecha_ficha,
                                "idemocion": idemocion_elegida,
                                "motivo": motivo,
                            },
                        )
                        connection.commit()

                        # Incrementamos el contador localmente
                        st.session_state.fichas_guardadas += 1
                        st.success("¡Ficha guardada con éxito!")
                        st.rerun()

                except Exception as e:
                    st.error(
                        f"Error al guardar la ficha en la base de datos: {e}"
                    )

    # Mensaje de apoyo si llegan a la meta sugerida
    if st.session_state.fichas_guardadas >= 20:
        st.balloons()
        st.success(
            "🎉 ¡Excelente trabajo! Ya has completado un bloque importante de fichas."
        )
