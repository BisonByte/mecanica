import http.server
import socketserver
import urllib.parse
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HOST = ""  # Listen on all interfaces
PORT = 8000

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>Simulador de Viga Móvil</title>
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:40px;max-width:600px;}
textarea{width:100%;height:60px;}
img{max-width:100%;height:auto;}
</style>
</head>
<body>
<h1>Simulador de Viga (versión móvil)</h1>
<form method='POST'>
<label>Longitud de la viga (m): <input type='number' step='0.1' name='L' value='{L}' required></label><br><br>
<label>Cargas puntuales (pos,mag) una por línea:</label><br>
<textarea name='cargas_puntuales'>{cp}</textarea><br>
<label>Cargas distribuidas (inicio,fin,mag) una por línea:</label><br>
<textarea name='cargas_distribuidas'>{cd}</textarea><br>
<label>Par torsor (N*m): <input type='number' step='0.1' name='par' value='{par}'></label><br><br>
<label>Usar apoyo C: <input type='checkbox' name='use_c' {use_c}></label>
<label>Posición C (m): <input type='number' step='0.1' name='pos_c' value='{pos_c}'></label><br><br>
<button type='submit'>Calcular</button>
</form>
{resultado}
{imagen}
</body>
</html>
"""


def parse_cargas(text):
    cargas = []
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        try:
            partes = [float(x) for x in line.replace(',', ' ').split()]
            if len(partes) == 2:
                cargas.append((partes[0], partes[1]))
        except ValueError:
            pass
    return cargas


def parse_cargas_distribuidas(text):
    cargas = []
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        try:
            partes = [float(x) for x in line.replace(',', ' ').split()]
            if len(partes) == 3:
                cargas.append((partes[0], partes[1], partes[2]))
        except ValueError:
            pass
    return cargas


def calcular_reacciones(L, cargas_puntuales, cargas_distribuidas, par_torsor, use_c, pos_c):
    suma_fuerzas_y = 0
    suma_momentos_a = 0

    for pos, mag in cargas_puntuales:
        suma_fuerzas_y += mag
        suma_momentos_a += mag * pos

    for inicio, fin, mag in cargas_distribuidas:
        F = mag * (fin - inicio)
        centroide = inicio + (fin - inicio) / 2
        suma_fuerzas_y += F
        suma_momentos_a += F * centroide

    if not use_c:
        RB = (suma_momentos_a + par_torsor) / L
        RA = suma_fuerzas_y - RB
        RC = 0
    else:
        c = pos_c
        RB = ((suma_momentos_a + par_torsor) - c * suma_fuerzas_y / 2) / (L - c)
        RA = RC = (suma_fuerzas_y - RB) / 2
    return RA, RB, RC


def dibujar_viga(L, cargas_puntuales, cargas_distribuidas):
    fig, ax = plt.subplots(figsize=(6,3))
    ax.plot([0, L], [0,0], 'k-', lw=4)
    for pos, mag in cargas_puntuales:
        ax.arrow(pos, 0.5, 0, -0.4, head_width=0.1, head_length=0.1, fc='r', ec='r')
        ax.text(pos, 0.55, f"{mag}N", ha='center', fontsize=8)
    for i, f, mag in cargas_distribuidas:
        F = mag * (f-i)
        ax.arrow((i+f)/2, 0.8, 0, -0.6, head_width=0.1, head_length=0.1, fc='orange', ec='orange')
        ax.text((i+f)/2, 0.85, f"{F:.1f}N", ha='center', fontsize=8)
    ax.set_xlim(-L*0.05, L*1.05)
    ax.set_ylim(-0.2,1)
    ax.axis('off')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    return buf.getvalue()


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_form()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        params = urllib.parse.parse_qs(data.decode())
        L = float(params.get('L', ['0'])[0])
        cp_text = params.get('cargas_puntuales', [''])[0]
        cd_text = params.get('cargas_distribuidas', [''])[0]
        par = float(params.get('par', ['0'])[0])
        use_c = 'use_c' in params
        pos_c = float(params.get('pos_c', ['0'])[0]) if use_c else 0
        cargas_puntuales = parse_cargas(cp_text)
        cargas_distribuidas = parse_cargas_distribuidas(cd_text)
        RA, RB, RC = calcular_reacciones(L, cargas_puntuales, cargas_distribuidas, par, use_c, pos_c)
        img_data = dibujar_viga(L, cargas_puntuales, cargas_distribuidas)
        img_b64 = io.BytesIO()
        img_b64.write(img_data)
        img_b64.seek(0)
        import base64
        b64 = base64.b64encode(img_b64.read()).decode()
        resultado = f"<h2>Resultados</h2><p>RA = {RA:.2f} N<br>RB = {RB:.2f} N" + (f"<br>RC = {RC:.2f} N" if use_c else "") + "</p>"
        imagen = f"<img src='data:image/png;base64,{b64}'/>"
        self.send_form(L=L, cp=cp_text, cd=cd_text, par=par, use_c='checked' if use_c else '', pos_c=pos_c, resultado=resultado, imagen=imagen)

    def send_form(self, **kwargs):
        defaults = {'L':10, 'cp':'', 'cd':'', 'par':0, 'use_c':'', 'pos_c':'', 'resultado':'', 'imagen':''}
        defaults.update(kwargs)
        html = HTML_FORM.format(**defaults)
        encoded = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type','text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run_server():
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"Sirviendo en http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
