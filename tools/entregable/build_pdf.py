"""Genera el PDF entregable desde la documentación del repositorio (HTML + Edge headless)."""
import csv
import html
import io
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import markdown
import pymupdf

REPO = Path(sys.argv[1]).resolve()
SALIDA = Path(sys.argv[2]).resolve()
TRABAJO = Path(sys.argv[3]).resolve()
TRABAJO.mkdir(parents=True, exist_ok=True)
URL = "https://github.com/IsaVonxz-type/bi-envasado-vinilos"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CAPT = REPO / "docs" / "capturas"
DB_USER, DB_NAME = sys.argv[4], sys.argv[5]

CAPITULOS = [  # (clave, titulo)
    ("resumen", "Resumen ejecutivo"),
    ("rubrica", "Cumplimiento de los requerimientos"),
    ("analisis", "Análisis de negocio y diagnóstico de la fuente"),
    ("kpi", "Catálogo de indicadores"),
    ("modelo", "Modelo dimensional"),
    ("diccionario", "Diccionario de datos y linaje"),
    ("etl", "Proceso ETL y calidad de datos"),
    ("sql", "Base de datos y consultas de negocio"),
    ("powerbi", "Tablero analítico en Power BI"),
    ("grafana", "Monitoreo casi en tiempo real en Grafana"),
    ("arquitectura", "Arquitectura, comparación de capas y evolución"),
    ("seguridad", "Datos personales y seguridad de acceso"),
    ("docker", "Despliegue con Docker (bonificación)"),
    ("hallazgos", "Hallazgos y recomendaciones"),
    ("equipo", "Repositorio y trabajo en equipo"),
]

MERMAIDS: list[tuple[str, str]] = []
import uuid


# ------------------------------------------------------------------ utilidades
def leer(ruta: str) -> str:
    return (REPO / ruta).read_text(encoding="utf-8")


def enlace_repo(base: str, destino: str) -> str:
    if destino.startswith(("http://", "https://", "#", "mailto:")):
        return destino
    ruta = (Path(base) / destino.split("#")[0]).as_posix()
    partes = []
    for p in ruta.split("/"):
        if p == "..":
            if partes:
                partes.pop()
        elif p not in ("", "."):
            partes.append(p)
    limpio = "/".join(partes)
    tipo = "tree" if destino.endswith("/") or "." not in partes[-1] else "blob"
    return f"{URL}/{tipo}/main/{limpio}"


def svg_estrella(facts, tops, bottoms, edges, etiquetas=None, ancho_fact=196):
    """Esquema en estrella: hechos al centro, dimensiones arriba y abajo. edges: (dim, fact, activa)."""
    etiquetas = etiquetas or {}
    W, H = 980, 470
    yf, hf = 205, 66
    yt, yb, hd, wd = 28, 376, 48, 184

    def centros(n, ancho_caja):
        hueco = (W - n * ancho_caja) / (n + 1)
        return [hueco + ancho_caja / 2 + i * (ancho_caja + hueco) for i in range(n)]

    cf = dict(zip([f[0] for f in facts], centros(len(facts), ancho_fact)))
    ct = dict(zip(tops, centros(len(tops), wd)))
    cb = dict(zip(bottoms, centros(len(bottoms), wd)))
    cd = {**ct, **cb}
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" font-family="Segoe UI, Arial, sans-serif">']
    for nombre, _ in facts:
        for lado, grupo in (("top", ct), ("bot", cb)):
            lista = sorted([(cd[d], d, act) for d, f, act in edges if f == nombre and d in grupo])
            n = len(lista)
            izq = cf[nombre] - ancho_fact / 2 + 22
            paso = (ancho_fact - 44) / (n - 1) if n > 1 else 0
            for i, (cx, d, act) in enumerate(lista):
                xf = izq + i * paso if n > 1 else cf[nombre]
                y1 = yt + hd if lado == "top" else yb
                y2 = yf if lado == "top" else yf + hf
                dash = "" if act else ' stroke-dasharray="6 4"'
                p.append(f'<line x1="{cx:.1f}" y1="{y1}" x2="{xf:.1f}" y2="{y2}" stroke="#7B8AA0" stroke-width="1.4"{dash}/>')
                p.append(f'<circle cx="{xf:.1f}" cy="{y2}" r="3.4" fill="#7B8AA0"/>')
    for d, cx in cd.items():
        y = yt if d in ct else yb
        et = etiquetas.get(d, "")
        p.append(f'<rect x="{cx - wd / 2:.1f}" y="{y}" width="{wd}" height="{hd}" rx="7" fill="#E8EEF6" stroke="#1F3A5F" stroke-width="1.5"/>')
        p.append(f'<text x="{cx:.1f}" y="{y + (21 if et else 29)}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#1B2A41">{html.escape(d)}</text>')
        if et:
            p.append(f'<text x="{cx:.1f}" y="{y + 37}" text-anchor="middle" font-size="10" fill="#2F5D8C">{html.escape(et)}</text>')
    for nombre, grano in facts:
        cx = cf[nombre]
        p.append(f'<rect x="{cx - ancho_fact / 2:.1f}" y="{yf}" width="{ancho_fact}" height="{hf}" rx="8" fill="#00A99D" stroke="#007F76" stroke-width="1.5"/>')
        p.append(f'<text x="{cx:.1f}" y="{yf + 27}" text-anchor="middle" font-size="13" font-weight="700" fill="#fff">{html.escape(nombre)}</text>')
        p.append(f'<text x="{cx:.1f}" y="{yf + 47}" text-anchor="middle" font-size="10" fill="#E6FBF8">{html.escape(grano)}</text>')
    p.append(f'<text x="{W / 2}" y="{H - 16}" text-anchor="middle" font-size="10.5" fill="#5B6B82">Cada línea une una dimensión (uno) con un hecho (muchos). Una línea punteada es una relación inactiva.</text>')
    p.append("</svg>")
    return "".join(p)


def svg_arquitectura() -> str:
    """Arquitectura completa: fuente, contenedores Docker y herramientas del anfitrión."""
    def caja(x, y, w, h, t1, t2="", relleno="#E8EEF6", borde="#1F3A5F", color="#1B2A41"):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{relleno}" stroke="{borde}" stroke-width="1.6"/>'
        s += f'<text x="{x + w / 2}" y="{y + (h / 2 - 3 if t2 else h / 2 + 5)}" text-anchor="middle" font-size="13.5" font-weight="700" fill="{color}">{html.escape(t1)}</text>'
        if t2:
            s += f'<text x="{x + w / 2}" y="{y + h / 2 + 15}" text-anchor="middle" font-size="10.5" fill="{color}" opacity=".85">{html.escape(t2)}</text>'
        return s

    def flecha(x1, y1, x2, y2, etiqueta="", dx=0, dy=-6):
        s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#5B6B82" stroke-width="1.7" marker-end="url(#pta)"/>'
        if etiqueta:
            s += f'<text x="{(x1 + x2) / 2 + dx}" y="{(y1 + y2) / 2 + dy}" text-anchor="middle" font-size="10.5" fill="#33445F" font-style="italic">{html.escape(etiqueta)}</text>'
        return s

    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 540" width="100%" font-family="Segoe UI, Arial, sans-serif">',
         '<defs><marker id="pta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#5B6B82"/></marker></defs>']
    # grupos
    p.append('<rect x="238" y="20" width="528" height="500" rx="14" fill="#F8FAFD" stroke="#2F5D8C" stroke-width="1.6" stroke-dasharray="7 5"/>')
    p.append('<text x="254" y="44" font-size="12.5" font-weight="700" fill="#2F5D8C">docker compose up -d</text>')
    p.append('<rect x="796" y="20" width="190" height="500" rx="14" fill="#F8FAFD" stroke="#7B8AA0" stroke-width="1.4" stroke-dasharray="7 5"/>')
    p.append('<text x="812" y="44" font-size="12.5" font-weight="700" fill="#5B6B82">Equipo anfitrión</text>')
    p.append('<text x="20" y="150" font-size="12.5" font-weight="700" fill="#5B6B82">Fuente</text>')
    # fuente
    p.append(caja(20, 165, 178, 92, "Excel con macros", "Base De Datos + catálogos"))
    # etl
    p.append(caja(262, 165, 160, 92, "ETL en Python", "limpia · seudonimiza · cuadra", "#E6F7F5", "#007F76"))
    # postgres
    p.append('<rect x="470" y="70" width="276" height="226" rx="12" fill="#fff" stroke="#1F3A5F" stroke-width="1.8"/>')
    p.append('<text x="608" y="94" text-anchor="middle" font-size="13.5" font-weight="700" fill="#1F3A5F">PostgreSQL 17</text>')
    for i, (n, d) in enumerate((("dw", "modelo dimensional"), ("audit", "calidad y cuadre"), ("ops", "lecturas hora a hora"))):
        y = 108 + i * 62
        p.append(caja(488, y, 240, 50, n, d, "#E8EEF6"))
    # simulador y grafana
    p.append(caja(262, 372, 190, 92, "Simulador", "lecturas + receptor de alertas", "#E6F7F5", "#007F76"))
    p.append(caja(526, 372, 210, 92, "Grafana", "tablero + reglas de alerta", "#E6F7F5", "#007F76"))
    # anfitrión
    p.append(caja(812, 112, 158, 92, "Power BI Desktop", "proyecto PBIP"))
    p.append(caja(812, 270, 158, 76, "DBeaver", "administración"))
    # flechas
    p.append(flecha(198, 211, 262, 211, "lee"))
    p.append(flecha(422, 211, 470, 211, "carga", 0, -7))
    p.append(flecha(500, 296, 400, 372, "calibración", -34, -2))
    p.append(flecha(440, 372, 560, 296, "lecturas", 24, 0))
    p.append(flecha(660, 296, 640, 372, "bi_lector", 34, 0))
    p.append(flecha(526, 424, 452, 424, "alertas (webhook)", 0, -8))
    p.append(flecha(746, 158, 812, 158, "bi_lector", 0, -8))
    p.append(flecha(746, 250, 812, 308, "", 0, 0))
    p.append("</svg>")
    return "".join(p)


def svg_modelo(codigo: str) -> str:
    if "OEE_Base" in codigo:  # modelo semántico de Power BI
        facts = [("OEE_Base", "producción y paro por turno"), ("Produccion", "una línea de producción"),
                 ("Paros", "un código de paro con minutos"), ("NoOperacion", "máquina, día y motivo")]
        tops = ["Referencia", "Turno", "Fecha"]
        bottoms = ["Persona", "CausaParo", "Maquina", "MotivoNoOperacion"]
        e = []
        for d in ("Referencia", "Turno", "Fecha", "Maquina"):
            e += [(d, "OEE_Base", True), (d, "Produccion", True), (d, "Paros", True)]
        e += [("Fecha", "NoOperacion", True), ("Maquina", "NoOperacion", True), ("MotivoNoOperacion", "NoOperacion", True),
              ("Persona", "Produccion", True), ("Persona", "Paros", True), ("CausaParo", "Paros", True)]
        return svg_estrella(facts, tops, bottoms, e, {"Fecha": "tabla de fechas", "CausaParo": "jerarquía de paros"}, 176)
    facts = [("fact_produccion", "una línea de producción"), ("fact_paro", "un código de paro con minutos"),
             ("fact_no_operacion", "máquina, día y motivo")]
    tops = ["dim_estandar_produccion", "dim_referencia", "dim_turno", "dim_fecha"]
    bottoms = ["dim_persona", "dim_causa_paro", "dim_maquina", "dim_motivo_no_operacion"]
    e = [("dim_estandar_produccion", "fact_produccion", True)]
    for d in ("dim_referencia", "dim_turno", "dim_fecha", "dim_persona", "dim_maquina"):
        e += [(d, "fact_produccion", True), (d, "fact_paro", True)]
    e += [("dim_causa_paro", "fact_paro", True), ("dim_fecha", "fact_no_operacion", True),
          ("dim_maquina", "fact_no_operacion", True), ("dim_motivo_no_operacion", "fact_no_operacion", True)]
    return svg_estrella(facts, tops, bottoms, e,
                        {"dim_estandar_produccion": "SCD tipo 2", "dim_turno": "construida por el equipo",
                         "dim_causa_paro": "construida por el equipo", "dim_motivo_no_operacion": "construida por el equipo"})


def md_a_html(texto: str, carpeta_doc: str) -> str:
    def mermaid(m):
        codigo = m.group(1)
        if codigo.lstrip().startswith("erDiagram"):
            MERMAIDS.append(("svg", svg_modelo(codigo)))
        elif "subgraph Docker" in codigo:
            MERMAIDS.append(("svg", svg_arquitectura()))
        else:
            if "subgraph" not in codigo:  # los flujos horizontales salen minúsculos en una página vertical
                codigo = codigo.replace("flowchart LR", "flowchart TB")
            MERMAIDS.append(("mm", codigo))
        return f"\n\n@@MERMAID{len(MERMAIDS) - 1}@@\n\n"

    texto = re.sub(r"(?m)^   (?=[-*] )", "    ", texto)  # sublistas con 3 espacios: python-markdown exige 4
    texto = re.sub(r"```mermaid\n(.*?)```", mermaid, texto, flags=re.S)
    texto = re.sub(r"\]\(([^)]+)\)", lambda m: "](" + enlace_repo(carpeta_doc, m.group(1)) + ")", texto)
    out = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    out = re.sub(r"<td>(-?[0-9][0-9.,]*[ ]?%?)</td>", lambda m: '<td class="n">' + m.group(1) + "</td>", out)
    for i, (tipo, codigo) in enumerate(MERMAIDS):
        cuerpo_d = codigo if tipo == "svg" else f'<pre class="mermaid">{html.escape(codigo)}</pre>'
        out = out.replace(f"<p>@@MERMAID{i}@@</p>", f'<div class="diagrama">{cuerpo_d}</div>')
    return out


def quitar_h1(cuerpo: str) -> str:
    return re.sub(r"^\s*<h1>.*?</h1>", "", cuerpo, count=1, flags=re.S)


def cortar_desde(texto: str, marca: str) -> str:
    i = texto.find(marca)
    return texto[:i] if i >= 0 else texto


def psql_csv(consulta: str) -> list[list[str]]:
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-U", DB_USER, "-d", DB_NAME, "--csv"],
        input=consulta, capture_output=True, text=True, encoding="utf-8", cwd=REPO, check=True)
    return list(csv.reader(io.StringIO(r.stdout)))


def tabla_html(filas: list[list[str]], max_filas: int = 20) -> str:
    cab, cuerpo = filas[0], filas[1:max_filas + 1]
    def es_num(v):
        return bool(re.fullmatch(r"-?[\d.,]+", v or ""))
    th = "".join(f"<th>{html.escape(c)}</th>" for c in cab)
    trs = ""
    for f in cuerpo:
        trs += "<tr>" + "".join(f'<td class="{"n" if es_num(c) else ""}">{html.escape(c)}</td>' for c in f) + "</tr>"
    return f"<table class='res'><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def figura(archivo: str, leyenda: str, ancho: str = "100%") -> str:
    ruta = CAPT / archivo
    if not ruta.exists():
        print("AVISO: falta la captura", archivo)
        return f'<p class="falta">[Falta la captura {html.escape(archivo)}]</p>'
    return (f'<figure style="width:{ancho}"><img src="{ruta.as_uri()}" alt="{html.escape(leyenda)}">'
            f"<figcaption>{html.escape(leyenda)}</figcaption></figure>")


# ------------------------------------------------------------------ capítulos
def cap_resumen() -> str:
    return f"""
<p class="lead">Se construyó una solución de inteligencia de negocios de extremo a extremo para las cuatro líneas de envasado de vinilos y témperas:
los registros históricos del Excel con macros pasan por un proceso ETL con validación de calidad, se cargan en un modelo dimensional en PostgreSQL
y se consumen en dos capas complementarias, un tablero analítico en <b>Power BI</b> para la dirección y un tablero operativo en <b>Grafana</b>,
con alertas, para supervisión y mantenimiento. Todo se despliega con un solo comando de Docker.</p>
<div class="tarjetas">
  <div class="tarjeta"><span class="v">26</span><span class="e">reglas de limpieza documentadas, con su efecto en filas</span></div>
  <div class="tarjeta"><span class="v">0,00</span><span class="e">diferencia en el cuadre de pacas, horas y minutos contra la fuente</span></div>
  <div class="tarjeta"><span class="v">81,6 %</span><span class="e">OEE de 2024 de Vinilos_3, frente a 55,9 % de Vinilos_1</span></div>
  <div class="tarjeta"><span class="v">72 %</span><span class="e">del paro no programado lo explican tres causas operativas</span></div>
  <div class="tarjeta"><span class="v">38,8 %</span><span class="e">utilización de capacidad; el 71 % de las horas sin operar son paros por ventas</span></div>
  <div class="tarjeta"><span class="v">~40 s</span><span class="e">para levantar base, ETL, simulador y Grafana con <code>docker compose up -d</code></span></div>
</div>
<h2>El mensaje en tres frases</h2>
<ol>
<li><b>Las líneas no pierden tiempo por averías, sino por la forma de operar:</b> ajuste operativo, limpieza por derrame y alistamiento explican el 72 % del paro no programado, y pesan cada año más.</li>
<li><b>La brecha entre líneas es grande:</b> Vinilos_3 y Vinilos_4 rinden un OEE de casi 80 % y Vinilos_1 y Vinilos_2, de 56 % a 61 %.</li>
<li><b>Invertir en más capacidad no se justifica con estos datos:</b> la planta opera cerca del 39 % del tiempo y la mayor parte de las horas sin operar se debe a paros por ventas.</li>
</ol>
<p>Un hallazgo sobre el dato cambió una cifra importante: el registro de horas no trabajadas casi desaparece desde julio de 2024, lo que inflaba la utilización a 48,4 %.
Medida solo en los meses con registro completo es de 38,8 %. El capítulo 14 desarrolla los hallazgos y las recomendaciones.</p>
<p><b>Repositorio:</b> <a href="{URL}">{URL}</a></p>
"""


def cap_rubrica() -> str:
    filas = [
        ("Usuarios (stakeholders) y preguntas de negocio", "3", "docs/01_analisis_negocio.md"),
        ("Diagnóstico de la fuente, calidad del dato y limitaciones del esquema actual", "3", "docs/01_analisis_negocio.md"),
        ("Catálogo de indicadores y propuestas nuevas con justificación", "4", "docs/02_catalogo_kpi.md"),
        ("Modelo en estrella, grano, dimensiones, jerarquías, matriz de bus y SCD", "5", "docs/03_modelo_dimensional.md"),
        ("Diccionario de datos: columnas, tipos, llaves, reglas y linaje", "6", "docs/10_diccionario_de_datos.md"),
        ("ETL justificado, reglas de limpieza con conteos y cuadre de cifras", "7", "etl/, docs/04_etl.md"),
        ("DDL, restricciones, índices y consultas con ventanas y comparativos", "5, 8", "sql/ddl/, sql/queries/"),
        ("Power BI: conexión a la base, modelo semántico, inteligencia de tiempo, navegación, segmentaciones, drill-down y Pareto", "9", "powerbi/"),
        ("Grafana: series de tiempo, estado por máquina, variables, alertas y datos simulados en vivo", "10", "grafana/, simulator/"),
        ("Arquitectura, comparación Power BI y Grafana, y evolución con PLC o SCADA", "11", "docs/08_arquitectura_y_evolucion.md"),
        ("Datos personales y seguridad de acceso a los tableros", "12", "docs/09_seguridad_y_datos_personales.md"),
        ("Repositorio: README, scripts, ETL, tablero exportado, proyecto de Power BI, sin secretos, historial de ambos integrantes", "13, 15", "README.md, .gitignore, historial"),
        ("Bonificación: Docker con un comando, volúmenes, variables de entorno y provisioning de Grafana", "13", "docker-compose.yml, .env.example"),
        ("Historia con hallazgos y recomendaciones", "14", "docs/11_hallazgos_y_recomendaciones.md"),
    ]
    trs = "".join(f"<tr><td>{html.escape(a)}</td><td class='c'>{b}</td><td><code>{html.escape(c)}</code></td></tr>" for a, b, c in filas)
    return f"""<p>Mapa entre lo que pide el enunciado y dónde se cumple, en este documento y en el repositorio.</p>
<table><thead><tr><th>Requerimiento</th><th>Capítulo</th><th>En el repositorio</th></tr></thead><tbody>{trs}</tbody></table>"""


def cap_doc(ruta: str, quitar_desde: str | None = None, extra: str = "") -> str:
    t = leer(ruta)
    if quitar_desde:
        t = cortar_desde(t, quitar_desde)
    return quitar_h1(md_a_html(t, str(Path(ruta).parent.as_posix()))) + extra


def cap_etl() -> str:
    reporte = leer("docs/generated/reporte_etl.md")
    reporte = re.sub(r"^# .*\n", "", reporte, count=1)
    reporte = reporte.replace("## ", "### ")
    return cap_doc("docs/04_etl.md") + "<h2>Resultado de la última ejecución</h2>" + md_a_html(reporte, "docs/generated")


def cap_sql() -> str:
    consultas = []
    for f in sorted((REPO / "sql" / "queries").glob("*.sql")):
        if f.name.startswith("30_"):
            continue
        lineas = f.read_text(encoding="utf-8").splitlines()
        titulo = lineas[0].lstrip("- ").strip()
        def campo(nombre):
            for l in lineas[:10]:
                if l.startswith(f"-- {nombre}:"):
                    return l.split(":", 1)[1].strip()
            return ""
        consultas.append((f.name, titulo, campo("Pregunta"), campo("Usuario"), campo("Técnica")))
    trs = "".join(
        f"<tr><td><code>{html.escape(n)}</code></td><td>{html.escape(p)}</td><td>{html.escape(u)}</td><td>{html.escape(t)}</td></tr>"
        for n, _, p, u, t in consultas)

    esquema = leer("sql/ddl/01_schema.sql")
    bloque_paro = re.search(r"CREATE TABLE dw\.fact_paro \(.*?\);", esquema, flags=re.S).group(0)
    indices = "\n".join(re.findall(r"CREATE INDEX .*?;", esquema))

    ejemplos = ""
    for archivo, titulo in (("01_oee_anual_por_maquina.sql", "OEE anual por máquina"),
                            ("02_comparativo_mismos_meses.sql", "Comparativo de 2025 contra 2024 con los mismos meses"),
                            ("04_pareto_paros_no_programados.sql", "Pareto de paros no programados")):
        sql = leer(f"sql/queries/{archivo}")
        filas = psql_csv(sql)
        ejemplos += (f"<h3>{html.escape(titulo)}</h3><pre class='sql'><code>{html.escape(sql.strip())}</code></pre>"
                     f"<p class='res-t'>Resultado sobre los datos cargados:</p>{tabla_html(filas, 16)}")
    return f"""
<h2>Despliegue y herramienta</h2>
<p>La base es <b>PostgreSQL 17</b>, administrada desde <b>DBeaver</b>. El DDL está en <code>sql/ddl/</code> (<code>01_schema.sql</code> crea tablas, restricciones e índices;
<code>02_views.sql</code>, las vistas de indicadores; <code>03_permisos.sql</code>, el acceso de solo lectura) y el esquema de monitoreo, en <code>sql/ops/</code>.
El ETL lo aplica en cada ejecución, de modo que el modelo se reconstruye desde cero.</p>
<h2>Restricciones e índices</h2>
<p>Cada hecho tiene llaves foráneas a sus dimensiones, <code>CHECK</code> que impiden medidas negativas y códigos fuera de 1 a 18, y <code>UNIQUE</code> que evitan cargar una línea dos veces.
La justificación de cada índice según el tipo de consulta está en el capítulo 5. A modo de ejemplo, la tabla de hechos de paros y los índices del modelo:</p>
<pre class='sql'><code>{html.escape(bloque_paro)}</code></pre>
<pre class='sql'><code>{html.escape(indices)}</code></pre>
<h2>Consultas de negocio</h2>
<p>Quince consultas en <code>sql/queries/</code> responden preguntas de cada usuario. Todas incluyen agregaciones, y la mayoría usan funciones de ventana (<code>RANK</code>, <code>ROW_NUMBER</code>,
<code>LAG</code>, <code>SUM() OVER</code>, <code>FIRST_VALUE</code>, <code>NTILE</code>, <code>PERCENT_RANK</code>) y comparativos entre periodos.</p>
<table><thead><tr><th>Archivo</th><th>Pregunta</th><th>Usuario</th><th>Técnica</th></tr></thead><tbody>{trs}</tbody></table>
<h2>Ejemplos con resultados</h2>
{ejemplos}
"""


def cap_powerbi() -> str:
    figs = (
        "<h2>Capturas del tablero</h2>"
        + figura("pbi_01_resumen.png", "Resumen ejecutivo: tarjetas de OEE, disponibilidad y rendimiento, OEE por mes frente al mismo mes del año anterior (inteligencia de tiempo), OEE por máquina y media móvil de 3 meses.")
        + figura("pbi_02_paros.png", "Causas de paro: Pareto con porcentaje acumulado, profundización por la jerarquía área → código → sistema → subcódigo, y matriz expandible.")
        + figura("pbi_03_confiabilidad.png", "Confiabilidad: fallas, MTBF y MTTR por año y máquina.")
        + figura("pbi_04_capacidad.png", "Capacidad: utilización por año y máquina en los meses con registro completo, y horas no trabajadas por motivo.")
        + figura("pbi_05_calidad.png", "Calidad del dato: cobertura del rendimiento por año y por mes, y pacas reportadas frente a válidas."))
    return cap_doc("docs/07_power_bi.md") + figs


def cap_grafana() -> str:
    figs = (
        "<h2>Capturas del tablero y de las alertas</h2>"
        + figura("gf_01_normal.jpg", "Tablero en operación normal: estado de cada línea, disponibilidad y OEE móviles de 4 horas, causas de paro y producción.")
        + figura("gf_02_falla.jpg", "Con una falla provocada en Vinilos_2: la disponibilidad móvil cae por debajo del umbral de 40 %, el estado de la línea pasa a rojo y las reglas de alerta se disparan.")
        + figura("gf_03_alertas.jpg", "Reglas de alerta cargadas por provisioning, con su estado por máquina."))
    return cap_doc("docs/06_monitoreo_grafana.md") + figs


def cap_docker() -> str:
    compose = leer("docker-compose.yml")
    env = leer(".env.example")
    return f"""
<p>La solución completa se levanta con <b>un solo comando</b> y de forma reproducible desde cero:</p>
<pre class='sql'><code>docker compose up -d</code></pre>
<table><thead><tr><th>Servicio</th><th>Qué hace</th><th>Acceso</th></tr></thead><tbody>
<tr><td><code>db</code></td><td>PostgreSQL 17 con volumen persistente; crea el usuario de solo lectura <code>bi_lector</code> la primera vez</td><td><code>localhost:5432</code> (configurable)</td></tr>
<tr><td><code>etl</code></td><td>Crea los esquemas, limpia, seudonimiza, cuadra y carga; luego termina</td><td><code>docker compose logs etl</code></td></tr>
<tr><td><code>simulator</code></td><td>Genera una hora de producción cada 15 s y recibe las alertas por webhook</td><td>solo red interna</td></tr>
<tr><td><code>grafana</code></td><td>Tablero, fuente de datos y alertas cargados por provisioning</td><td><code>http://localhost:3000</code></td></tr>
</tbody></table>
<h2>Cumplimiento de la bonificación</h2>
<ul>
<li><b>Un solo comando, desde cero.</b> Probado con <code>docker compose down -v</code> seguido de <code>up -d</code>: la solución queda operativa en menos de un minuto.</li>
<li><b>Persistencia con volúmenes.</b> <code>pgdata</code> guarda la base y <code>grafana-data</code>, el estado de Grafana. El esquema <code>ops</code> (lecturas del monitoreo) sobrevive al ETL, que recrea solo <code>dw</code> y <code>audit</code>.</li>
<li><b>Credenciales por variables de entorno.</b> El <code>.env</code> está excluido del repositorio y el <code>.env.example</code> está versionado con valores <code>cambiar_esto</code>; los servicios se niegan a iniciar si siguen así.</li>
<li><b>Provisioning de Grafana.</b> La fuente de datos, el tablero y las reglas de alerta se cargan al iniciar el contenedor, sin configuración manual, desde <code>grafana/provisioning/</code> y <code>grafana/dashboards/</code>.</li>
<li><b>Orden de arranque garantizado.</b> Los <i>healthchecks</i> y <code>depends_on</code> hacen que el ETL espere a la base, el simulador al ETL y Grafana al simulador.</li>
<li><b>Power BI y DBeaver en el anfitrión</b>, conectados a los servicios contenerizados.</li>
</ul>
<h2>docker-compose.yml</h2>
<pre class='sql'><code>{html.escape(compose)}</code></pre>
<h2>.env.example</h2>
<pre class='sql'><code>{html.escape(env)}</code></pre>
"""


def cap_equipo() -> str:
    r = subprocess.run(["git", "log", "--reverse", "--format=%h|%an|%ad|%s", "--date=short"], cwd=REPO,
                       capture_output=True, text=True, encoding="utf-8", check=True)
    commits = [l.split("|", 3) for l in r.stdout.strip().splitlines()]
    conteo: dict[str, int] = {}
    for _, autor, _, _ in commits:
        conteo[autor] = conteo.get(autor, 0) + 1
    nombres = {"Isa": "Isaac Madera Jiménez", "Daniela": "Daniela Montoya Quintero"}
    areas = {"Isa": "Análisis de negocio, catálogo de indicadores, modelo dimensional, ETL en Python con pruebas, despliegue con Docker",
             "Daniela": "Simulador y webhook, consultas SQL de negocio, tablero y alertas de Grafana, proyecto de Power BI, seguridad y documentación del Bloque 2"}
    resumen = "".join(f"<tr><td>{nombres.get(a, a)}</td><td class='c'>{n}</td><td>{areas.get(a, '')}</td></tr>" for a, n in conteo.items())
    trs = "".join(f"<tr><td><code>{h}</code></td><td>{nombres.get(a, a).split()[0]}</td><td>{f}</td><td>{html.escape(m)}</td></tr>" for h, a, f, m in commits)
    estructura = md_a_html(re.search(r"## Estructura\n(.*?)\n## ", leer("README.md"), flags=re.S).group(1), ".")
    return f"""
<p><b>Repositorio:</b> <a href="{URL}">{URL}</a></p>
<p>El repositorio contiene los scripts SQL, el código del ETL con sus pruebas, el simulador, el tablero de Grafana exportado y su provisioning, el proyecto de Power BI en formato PBIP,
la documentación y un <code>README.md</code> que explica el proyecto, su arquitectura y cómo reproducirlo desde cero. Ni el <code>.env</code> ni el Excel fuente se versionan, y el <code>.gitignore</code> excluye los archivos con datos personales.</p>
<h2>Estructura</h2>{estructura}
<h2>Aportes de cada integrante</h2>
<table><thead><tr><th>Integrante</th><th>Commits</th><th>Áreas principales</th></tr></thead><tbody>{resumen}</tbody></table>
<h2>Historial de commits</h2>
<table class='commits'><thead><tr><th>Commit</th><th>Autor</th><th>Fecha</th><th>Mensaje</th></tr></thead><tbody>{trs}</tbody></table>
"""


CUERPO = {
    "resumen": cap_resumen,
    "rubrica": cap_rubrica,
    "analisis": lambda: cap_doc("docs/01_analisis_negocio.md"),
    "kpi": lambda: cap_doc("docs/02_catalogo_kpi.md"),
    "modelo": lambda: cap_doc("docs/03_modelo_dimensional.md"),
    "diccionario": lambda: cap_doc("docs/10_diccionario_de_datos.md"),
    "etl": cap_etl,
    "sql": cap_sql,
    "powerbi": cap_powerbi,
    "grafana": cap_grafana,
    "arquitectura": lambda: cap_doc("docs/08_arquitectura_y_evolucion.md"),
    "seguridad": lambda: cap_doc("docs/09_seguridad_y_datos_personales.md"),
    "docker": cap_docker,
    "hallazgos": lambda: cap_doc("docs/11_hallazgos_y_recomendaciones.md", quitar_desde="## Guion de la sustentación"),
    "equipo": cap_equipo,
}

_css = (Path(__file__).with_name("pdf.css")).read_text(encoding="utf-8")
_i0 = _css.index("/* ---------- portada ---------- */")
_i1 = _css.index("/* ---------- índice ---------- */")
CSS_PORTADA = ("@page { size: Letter; margin: 0; } html, body { margin: 0; } :root { --azul:#1F3A5F; }"
               " html { font-family: 'Segoe UI', Calibri, Arial, sans-serif; } body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } "
               + _css[_i0:_i1])
CSS = _css[:_i0].replace("@page :first { margin: 0; }", "") + _css[_i1:]


def construir_html(paginas_toc: dict[str, int] | None) -> str:
    MERMAIDS.clear()
    capitulos = ""
    for n, (clave, titulo) in enumerate(CAPITULOS, start=1):
        cuerpo = CUERPO[clave]()
        sec = 0
        def numerar(m):
            nonlocal sec
            sec += 1
            return f"<h2><span class='num'>{n}.{sec}</span> {m.group(1)}</h2>"
        cuerpo = re.sub(r"<h2>(.*?)</h2>", numerar, cuerpo, flags=re.S)
        capitulos += f"<section class='cap' id='c{n}'><h1><span class='num'>{n}</span>{html.escape(titulo)}</h1>{cuerpo}</section>"
    toc = "".join(
        f"<li><span class='t'><b>{n}</b> &nbsp; {html.escape(t)}</span><span class='p'>{(paginas_toc or {}).get(c, '')}</span></li>"
        for n, (c, t) in enumerate(CAPITULOS, start=1))
    hoy = "Noviembre de 2026"
    portada = f"""
<section class='portada'>
  <div class='banda'></div>
  <div class='contenido'>
    <div class='kicker'>Proyecto final · Inteligencia de Negocios</div>
    <h1>Solución de inteligencia de negocios para las líneas de envasado de vinilos y témperas</h1>
    <p class='sub'>Modelo dimensional, ETL reproducible, tablero analítico en Power BI y monitoreo casi en tiempo real con alertas en Grafana</p>
    <div class='integrantes'>
      <div class='etq'>Integrantes</div>
      <div class='nombre'>Isaac Madera Jiménez</div>
      <div class='nombre'>Daniela Montoya Quintero</div>
    </div>
    <div class='repo'>
      <div class='etq'>Repositorio en GitHub</div>
      <a href='{URL}'>{URL}</a>
    </div>
    <div class='pie'>{hoy} · Semestre 2026-2</div>
  </div>
</section>"""
    indice = f"<section class='indice'><h1 class='sin'>Contenido</h1><ol>{toc}</ol></section>"
    mermaid_js = """
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'base', securityLevel:'loose',
 themeVariables:{primaryColor:'#E8EEF6', primaryBorderColor:'#1F3A5F', primaryTextColor:'#1B2A41', lineColor:'#5B6B82', fontFamily:'Segoe UI, Arial', fontSize:'13px'},
 flowchart:{useMaxWidth:true, htmlLabels:true, curve:'basis'}, er:{useMaxWidth:true}, sequence:{useMaxWidth:true}});</script>"""
    cuerpo_html = f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Solución de BI - Envasado de vinilos</title><style>{CSS}</style>{mermaid_js}</head><body>{indice}{capitulos}</body></html>"
    portada_html = f"<!doctype html><html lang='es'><head><meta charset='utf-8'><style>{CSS_PORTADA}</style></head><body>{portada}</body></html>"
    return cuerpo_html, portada_html


def _limpiar_edge() -> None:
    """Cierra los procesos de Edge que lanzó este script (los reconoce por su carpeta de perfil)."""
    patron = str(TRABAJO).replace("\\", "\\\\")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object {{ $_.CommandLine -like '*perfil_edge_*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"],
                   capture_output=True)


def imprimir(html_texto: str, destino: Path) -> None:
    f = TRABAJO / (destino.stem + ".html")
    f.write_text(html_texto, encoding="utf-8")
    if destino.exists():
        destino.unlink()
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
           f"--user-data-dir={TRABAJO / ('perfil_edge_' + uuid.uuid4().hex[:8])}", "--no-first-run", "--disable-extensions",
           "--virtual-time-budget=40000", f"--print-to-pdf={destino}", f.as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    import time
    for _ in range(120):
        if destino.exists() and destino.stat().st_size > 10000:
            time.sleep(1.0)
            _limpiar_edge()
            return
        time.sleep(1.0)
    raise RuntimeError("Edge no generó el PDF: " + str(destino))


def paginas_de_capitulos(pdf: Path) -> dict[str, int]:
    doc = pymupdf.open(pdf)
    res: dict[str, int] = {}
    for n, (clave, titulo) in enumerate(CAPITULOS, start=1):
        for i in range(1, len(doc)):  # después del índice (página 0 del cuerpo)
            texto = doc[i].get_text()
            if re.search(rf"^\s*{n}\s*\n?\s*{re.escape(titulo)}", texto, flags=re.M):
                res[clave] = i + 2  # +1 por la portada, +1 por contar desde 1
                break
    doc.close()
    return res


def sellar(pdf_portada: Path, pdf_in: Path, pdf_out: Path, paginas: dict[str, int]) -> None:
    doc = pymupdf.open(pdf_portada)
    doc.insert_pdf(pymupdf.open(pdf_in))
    total = len(doc)
    gris = (0.42, 0.47, 0.55)
    for i, pagina in enumerate(doc):
        if i == 0:
            continue
        w, h = pagina.rect.width, pagina.rect.height
        pagina.insert_text((38, h - 24), "Solución de BI · Envasado de vinilos y témperas", fontsize=7.5, fontname="helv", color=gris)
        pagina.insert_text((w - 38 - 72, h - 24), f"Página {i + 1} de {total}", fontsize=7.5, fontname="helv", color=gris)
    toc = [[1, titulo, paginas[c]] for c, titulo in CAPITULOS if c in paginas]
    if paginas:
        doc.set_toc(toc)
    doc.set_metadata({"title": "Solución de BI para las líneas de envasado de vinilos y témperas",
                      "author": "Isaac Madera Jiménez, Daniela Montoya Quintero", "subject": "Proyecto final de Inteligencia de Negocios",
                      "keywords": "BI, OEE, Power BI, Grafana, PostgreSQL, ETL"})
    doc.save(pdf_out, deflate=True, garbage=3)
    doc.close()


if __name__ == "__main__":
    borrador, portada_pdf = TRABAJO / "cuerpo.pdf", TRABAJO / "portada.pdf"
    cuerpo_html, portada_html = construir_html(None)
    imprimir(portada_html, portada_pdf)
    imprimir(cuerpo_html, borrador)
    pg = paginas_de_capitulos(borrador)
    print("Páginas por capítulo:", pg)
    imprimir(construir_html(pg)[0], borrador)
    pg2 = paginas_de_capitulos(borrador)
    if pg2 != pg:
        print("El índice cambió de paginación; se recalcula:", pg2)
        imprimir(construir_html(pg2)[0], borrador)
        pg = pg2
    sellar(portada_pdf, borrador, SALIDA, pg)
    print("PDF escrito:", SALIDA, "páginas:", len(pymupdf.open(SALIDA)))
