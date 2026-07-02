import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

load_dotenv()

app = Flask(__name__)
app.secret_key = "clave_secreta_para_mensajes"


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "flask_crud"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        cursor_factory=RealDictCursor,
    )


def email_valido(email):
    if not email:
        return True
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)


@app.route("/")
def index():
    orden = request.args.get("orden", "id")

    columnas_permitidas = {
        "id": "id",
        "apellido": "apellido",
        "carrera": "carrera",
        "fecha": "fecha_registro"
    }

    columna = columnas_permitidas.get(orden, "id")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM estudiantes ORDER BY {columna} ASC")
            estudiantes = cur.fetchall()

    return render_template("index.html", estudiantes=estudiantes)


@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        dni = request.form.get("dni", "").strip()
        apellido = request.form.get("apellido", "").strip()
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        carrera = request.form.get("carrera", "").strip()
        telefono = request.form.get("telefono", "").strip()
        edad = request.form.get("edad", "").strip()

        if not dni or not apellido or not nombre or not carrera:
            flash("DNI, apellido, nombre y carrera son obligatorios.", "error")
            return redirect(url_for("agregar"))

        if not email_valido(email):
            flash("El email ingresado no es válido.", "error")
            return redirect(url_for("agregar"))

        if edad and not edad.isdigit():
            flash("La edad debe ser un número.", "error")
            return redirect(url_for("agregar"))

        edad = int(edad) if edad else None

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO estudiantes
                        (dni, apellido, nombre, email, carrera, telefono, edad)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (dni, apellido, nombre, email, carrera, telefono, edad),
                    )
                conn.commit()

            flash("Estudiante agregado correctamente.", "success")
            return redirect(url_for("index"))

        except psycopg2.errors.UniqueViolation:
            flash("Ya existe un estudiante con ese DNI.", "error")
            return redirect(url_for("agregar"))

        except Exception as e:
            flash(f"Error al agregar estudiante: {e}", "error")
            return redirect(url_for("agregar"))

    return render_template("agregar.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if request.method == "POST":
        dni = request.form.get("dni", "").strip()
        apellido = request.form.get("apellido", "").strip()
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        carrera = request.form.get("carrera", "").strip()
        telefono = request.form.get("telefono", "").strip()
        edad = request.form.get("edad", "").strip()

        if not dni or not apellido or not nombre or not carrera:
            flash("DNI, apellido, nombre y carrera son obligatorios.", "error")
            return redirect(url_for("editar", id=id))

        if not email_valido(email):
            flash("El email ingresado no es válido.", "error")
            return redirect(url_for("editar", id=id))

        if edad and not edad.isdigit():
            flash("La edad debe ser un número.", "error")
            return redirect(url_for("editar", id=id))

        edad = int(edad) if edad else None

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE estudiantes
                        SET dni=%s, apellido=%s, nombre=%s, email=%s,
                            carrera=%s, telefono=%s, edad=%s
                        WHERE id=%s
                        """,
                        (dni, apellido, nombre, email, carrera, telefono, edad, id),
                    )
                conn.commit()

            flash("Estudiante actualizado correctamente.", "success")
            return redirect(url_for("index"))

        except Exception as e:
            flash(f"Error al actualizar estudiante: {e}", "error")
            return redirect(url_for("editar", id=id))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM estudiantes WHERE id = %s", (id,))
            estudiante = cur.fetchone()

    if not estudiante:
        flash("No se encontró el estudiante solicitado.", "error")
        return redirect(url_for("index"))

    return render_template("editar.html", estudiante=estudiante)


@app.route("/eliminar/<int:id>")
def eliminar(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM estudiantes WHERE id = %s", (id,))
        conn.commit()

    flash("Estudiante eliminado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/buscar", methods=["POST"])
def buscar():
    texto = request.form.get("buscar", "").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM estudiantes
                WHERE dni ILIKE %s
                   OR apellido ILIKE %s
                   OR carrera ILIKE %s
                ORDER BY apellido ASC
                """,
                (f"%{texto}%", f"%{texto}%", f"%{texto}%"),
            )
            estudiantes = cur.fetchall()

    return render_template("index.html", estudiantes=estudiantes, busqueda=texto)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)