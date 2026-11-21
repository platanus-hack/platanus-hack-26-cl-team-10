"""La conexión compartida aguanta hilos a la vez (endpoints + WebSocket del edge).

Correr:  python3 -m unittest discover tests
"""

import threading
import unittest

from app import db


class ConexionCompartida(unittest.TestCase):
    def test_muchos_hilos_leyendo_y_escribiendo_no_rompen_la_conexion(self):
        cx = db.conectar(":memory:")
        errores = []

        def trabajar(i):
            try:
                for j in range(300):
                    db.escribir_sensor(cx, f"s{i}", str(j))
                    db.estado_sensores(cx)
            except Exception as e:  # noqa: BLE001 - la prueba quiere ver cualquier falla
                errores.append(e)

        hilos = [threading.Thread(target=trabajar, args=(i,)) for i in range(8)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        self.assertEqual(errores, [])
        self.assertEqual(db.estado_sensores(cx)["s0"], "299")

    def test_fetchone_avanza_como_un_cursor(self):
        cx = db.conectar(":memory:")
        db.escribir_sensor(cx, "a", "1")
        db.escribir_sensor(cx, "b", "2")
        r = cx.execute("SELECT id FROM sensores ORDER BY id")
        self.assertEqual([r.fetchone()["id"], r.fetchone()["id"], r.fetchone()], ["a", "b", None])


if __name__ == "__main__":
    unittest.main()
