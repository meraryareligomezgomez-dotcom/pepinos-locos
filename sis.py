from flask import Flask, render_template_string, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

# Configuración de Correo (Opcional, para las pruebas de envío)
EMAIL_REMITENTE = "tu_correo@gmail.com"
PASSWORD_REMITENTE = "tu_contraseña_de_aplicacion"

# Catálogo de Pepinos Locos
PRODUCTOS = [
    {
        "id": 1,
        "nombre": "Pepino Loco Clásico",
        "precio": 2.50,
        "descripcion": "Pepino entero preparado con cacahuates japoneses, chamoy, limón y Tajín.",
        "imagen": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": 2,
        "nombre": "Pepino Loco con Gomitas",
        "precio": 3.25,
        "descripcion": "Añade gomitas ácidas, ositos de goma, serpientes de tamarindo y chamoy dulce.",
        "imagen": "https://images.unsplash.com/photo-1582058091505-f87a2e55a40f?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": 3,
        "nombre": "Barquillos de Pepino",
        "precio": 2.75,
        "descripcion": "Mitades abiertas cargadas con Skwinkles, Valentina y cacahuates crujientes.",
        "imagen": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": 4,
        "nombre": "Mega Charola Extreme",
        "precio": 6.50,
        "descripcion": "Charola familiar con Takis Fuego, Doritos, gomitas, salsas y tajín abundante.",
        "imagen": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"
    }
]

HISTORIAL_VENTAS = []

# Plantilla HTML integrada dentro del mismo archivo Python
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pepinos Locos - Sistema POS & Facturación</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-amber-50 text-slate-800 font-sans">

    <header class="bg-lime-600 text-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <h1 class="text-2xl font-black tracking-wider flex items-center gap-2">
                🥒 PEPINOS LOCOS <span class="text-xs bg-red-600 px-2 py-1 rounded-full text-white">POS v2.0</span>
            </h1>
            <button onclick="toggleModal('modal-metricas')" class="bg-lime-800 hover:bg-lime-900 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                <i class="fa-solid fa-chart-line"></i> Métricas Módulo
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section class="lg:col-span-2 space-y-4">
            <h2 class="text-xl font-bold text-lime-900 border-b-2 border-lime-500 pb-1 flex items-center gap-2">
                <i class="fa-solid fa-store"></i> Menú de Especialidades
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {% for prod in productos %}
                <div class="bg-white rounded-xl shadow-md overflow-hidden border border-lime-200 flex flex-col justify-between hover:shadow-lg transition">
                    <img src="{{ prod.imagen }}" alt="{{ prod.nombre }}" class="h-40 w-full object-cover">
                    <div class="p-4 flex-1 flex flex-col justify-between">
                        <div>
                            <div class="flex justify-between items-start">
                                <h3 class="font-bold text-lg text-slate-800">{{ prod.nombre }}</h3>
                                <span class="bg-red-100 text-red-700 font-bold px-2 py-0.5 rounded text-sm">${{ "%.2f"|format(prod.precio) }}</span>
                            </div>
                            <p class="text-gray-600 text-xs mt-1">{{ prod.descripcion }}</p>
                        </div>
                        <button onclick="agregarAlCarrito({{ prod.id }}, '{{ prod.nombre }}', {{ prod.precio }})" 
                                class="mt-3 w-full bg-lime-500 hover:bg-lime-600 text-white font-bold py-2 rounded-lg transition flex items-center justify-center gap-2">
                            <i class="fa-solid fa-cart-plus"></i> Agregar al Carrito
                        </button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>

        <section class="bg-white rounded-xl shadow-lg border border-lime-200 p-5 flex flex-col justify-between h-fit">
            <div>
                <h2 class="text-xl font-bold text-lime-900 border-b-2 border-lime-500 pb-2 mb-4 flex items-center justify-between">
                    <span><i class="fa-solid fa-basket-shopping"></i> Carrito</span>
                    <button onclick="vaciarCarrito()" class="text-xs text-red-500 hover:underline">Vaciar</button>
                </h2>
                <div id="lista-carrito" class="space-y-3 max-h-60 overflow-y-auto pr-1 mb-4">
                    <p class="text-gray-400 text-center text-sm py-8">Tu carrito está vacío 🥒</p>
                </div>
                <div class="space-y-2 border-t pt-3 border-gray-200">
                    <h3 class="font-bold text-xs text-gray-500 uppercase tracking-wider">Datos de Facturación</h3>
                    <input type="text" id="cli-nombre" placeholder="Nombre completo" class="w-full text-sm p-2 border rounded bg-gray-50 focus:outline-none focus:ring-1 focus:ring-lime-500">
                    <input type="text" id="cli-nit" placeholder="NIT / Documento" class="w-full text-sm p-2 border rounded bg-gray-50 focus:outline-none focus:ring-1 focus:ring-lime-500">
                    <input type="email" id="cli-correo" placeholder="Correo electrónico (para envío DTE)" class="w-full text-sm p-2 border rounded bg-gray-50 focus:outline-none focus:ring-1 focus:ring-lime-500">
                    <input type="number" id="monto-pago" step="0.01" placeholder="Monto pagado ($)" class="w-full text-sm p-2 border rounded bg-gray-50 focus:outline-none focus:ring-1 focus:ring-lime-500">
                </div>
            </div>
            <div class="mt-4 border-t border-gray-200 pt-3 space-y-1.5 text-sm">
                <div class="flex justify-between text-gray-600"><span>Subtotal:</span><span id="txt-subtotal">$0.00</span></div>
                <div class="flex justify-between text-gray-600"><span>IVA (13%):</span><span id="txt-iva">$0.00</span></div>
                <div class="flex justify-between text-base font-black text-lime-900 pt-1 border-t"><span>TOTAL:</span><span id="txt-total">$0.00</span></div>
                <button onclick="procesarPago()" class="w-full mt-3 bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-xl shadow transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-receipt"></i> Facturar y Enviar Ticket
                </button>
            </div>
        </section>
    </main>

    <div id="modal-factura" class="fixed inset-0 bg-black/60 hidden flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative font-mono text-sm">
            <h3 class="text-center font-bold text-lg mb-2">🥒 PEPINOS LOCOS S.A. DE C.V.</h3>
            <p class="text-center text-xs text-gray-500 mb-4" id="fact-id">COMPROBANTE DTE</p>
            <div class="border-t border-b border-dashed py-2 my-2 space-y-1 text-xs" id="fact-detalles"></div>
            <div class="space-y-1 text-right text-xs my-2 font-bold" id="fact-totales"></div>
            <p id="fact-correo-status" class="text-xs text-center my-3 font-sans font-semibold"></p>
            <button onclick="toggleModal('modal-factura')" class="w-full bg-slate-800 text-white py-2 rounded-lg font-sans font-bold">Cerrar</button>
        </div>
    </div>

    <div id="modal-metricas" class="fixed inset-0 bg-black/60 hidden flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative font-sans">
            <h3 class="font-bold text-xl text-lime-900 mb-4 flex items-center gap-2"><i class="fa-solid fa-chart-pie"></i> Consola de Evaluación</h3>
            <div class="grid grid-cols-3 gap-3 text-center mb-6">
                <div class="bg-lime-50 p-3 rounded-xl border border-lime-200">
                    <span class="block text-2xl font-black text-lime-800" id="m-ventas">0</span>
                    <span class="text-xs text-gray-500">Ventas</span>
                </div>
                <div class="bg-amber-50 p-3 rounded-xl border border-amber-200">
                    <span class="block text-2xl font-black text-amber-800" id="m-ingresos">$0.00</span>
                    <span class="text-xs text-gray-500">Ingresos</span>
                </div>
                <div class="bg-red-50 p-3 rounded-xl border border-red-200">
                    <span class="block text-xs font-black text-red-800 truncate" id="m-estrella">-</span>
                    <span class="text-xs text-gray-500">Más Vendido</span>
                </div>
            </div>
            <button onclick="toggleModal('modal-metricas')" class="w-full bg-lime-600 text-white py-2 rounded-lg font-bold">Aceptar</button>
        </div>
    </div>

    <script>
        let carrito = [];

        function agregarAlCarrito(id, nombre, precio) {
            const item = carrito.find(x => x.id === id);
            if (item) { item.cantidad++; } 
            else { carrito.push({ id, nombre, precio, cantidad: 1 }); }
            actualizarCarritoUI();
        }

        function cambiarCantidad(id, delta) {
            const item = carrito.find(x => x.id === id);
            if (!item) return;
            item.cantidad += delta;
            if (item.cantidad <= 0) { carrito = carrito.filter(x => x.id !== id); }
            actualizarCarritoUI();
        }

        function vaciarCarrito() {
            carrito = [];
            actualizarCarritoUI();
        }

        function actualizarCarritoUI() {
            const cont = document.getElementById('lista-carrito');
            if (carrito.length === 0) {
                cont.innerHTML = `<p class="text-gray-400 text-center text-sm py-8">Tu carrito está vacío 🥒</p>`;
            } else {
                cont.innerHTML = carrito.map(item => `
                    <div class="flex justify-between items-center bg-gray-50 p-2 rounded border border-gray-100 text-sm">
                        <div class="flex-1 pr-2">
                            <span class="font-bold text-gray-800 block">${item.nombre}</span>
                            <span class="text-xs text-gray-500">$${item.precio.toFixed(2)} c/u</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="cambiarCantidad(${item.id}, -1)" class="w-6 h-6 bg-gray-200 text-gray-700 font-bold rounded hover:bg-gray-300">-</button>
                            <span class="font-bold text-sm w-4 text-center">${item.cantidad}</span>
                            <button onclick="cambiarCantidad(${item.id}, 1)" class="w-6 h-6 bg-lime-500 text-white font-bold rounded hover:bg-lime-600">+</button>
                        </div>
                    </div>
                `).join('');
            }
            const subtotal = carrito.reduce((acc, i) => acc + (i.precio * i.cantidad), 0);
            const iva = subtotal * 0.13;
            const total = subtotal + iva;
            document.getElementById('txt-subtotal').innerText = `$${subtotal.toFixed(2)}`;
            document.getElementById('txt-iva').innerText = `$${iva.toFixed(2)}`;
            document.getElementById('txt-total').innerText = `$${total.toFixed(2)}`;
        }

        async function procesarPago() {
            if (carrito.length === 0) { alert('Agrega al menos un producto al carrito'); return; }
            const cliente = {
                nombre: document.getElementById('cli-nombre').value,
                nit: document.getElementById('cli-nit').value,
                correo: document.getElementById('cli-correo').value
            };
            const montoPago = parseFloat(document.getElementById('monto-pago').value) || 0;

            const res = await fetch('/api/procesar_venta', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cliente, carrito, monto_pago: montoPago })
            });
            const data = await res.json();

            if (data.success) {
                const f = data.factura;
                document.getElementById('fact-id').innerText = `${f.id} - ${f.fecha}`;
                document.getElementById('fact-detalles').innerHTML = f.items.map(i => `
                    <div class="flex justify-between">
                        <span>${i.nombre} x${i.cantidad}</span>
                        <span>$${(i.precio * i.cantidad).toFixed(2)}</span>
                    </div>
                `).join('');
                document.getElementById('fact-totales').innerHTML = `
                    <p>Subtotal: $${f.subtotal.toFixed(2)}</p>
                    <p>IVA (13%): $${f.iva.toFixed(2)}</p>
                    <p class="text-sm font-black">TOTAL: $${f.total.toFixed(2)}</p>
                    <p class="text-xs font-normal">Recibido: $${f.monto_pago.toFixed(2)} | Cambio: $${f.cambio.toFixed(2)}</p>
                `;
                const correoStatus = document.getElementById('fact-correo-status');
                if (data.correo_enviado) {
                    correoStatus.className = "text-xs text-center my-3 font-sans font-semibold text-green-600";
                    correoStatus.innerText = "✉️ Factura enviada exitosamente por correo.";
                } else {
                    correoStatus.className = "text-xs text-center my-3 font-sans font-semibold text-amber-600";
                    correoStatus.innerText = "⚠️ Factura registrada (Configura tus credenciales SMTP para enviar correos).";
                }
                toggleModal('modal-factura');
                vaciarCarrito();
                actualizarMetricas();
            }
        }

    async function actualizarMetricas() {
        const res = await fetch('/api/metricas');
        const data = await res.json();
        document.getElementById('m-ventas').innerText = data.total_ventas;
        document.getElementById('m-ingresos').innerText = `$${data.ingresos_totales.toFixed(2)}`;
        document.getElementById('m-estrella').innerText = data.producto_estrella;
    }

    function toggleModal(id) {
        document.getElementById(id).classList.toggle('hidden');
    }
    actualizarMetricas();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, productos=PRODUCTOS)

@app.route('/api/procesar_venta', methods=['POST'])
def procesar_venta():
    datos = request.json
    cliente = datos.get('cliente', {})
    carrito = datos.get('carrito', [])
    monto_pago = float(datos.get('monto_pago', 0))

    if not carrito:
        return jsonify({"success": False, "message": "El carrito está vacío."}), 400

    subtotal = sum(item['precio'] * item['cantidad'] for item in carrito)
    iva = subtotal * 0.13
    total = subtotal + iva
    cambio = max(0, monto_pago - total)

    id_factura = f"DTE-{int(datetime.now().timestamp())}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    factura = {
        "id": id_factura,
        "fecha": fecha,
        "cliente": cliente,
        "items": carrito,
        "subtotal": round(subtotal, 2),
        "iva": round(iva, 2),
        "total": round(total, 2),
        "monto_pago": round(monto_pago, 2),
        "cambio": round(cambio, 2)
    }

    HISTORIAL_VENTAS.append(factura)

    correo_enviado = False
    if cliente.get('correo'):
        correo_enviado = enviar_factura_correo(cliente['correo'], factura)

    return jsonify({
        "success": True,
        "factura": factura,
        "correo_enviado": correo_enviado
    })

@app.route('/api/metricas', methods=['GET'])
def get_metricas():
    total_ventas = len(HISTORIAL_VENTAS)
    ingresos_totales = sum(f['total'] for f in HISTORIAL_VENTAS)
    
    conteo_items = {}
    for f in HISTORIAL_VENTAS:
        for item in f['items']:
            nombre = item['nombre']
            conteo_items[nombre] = conteo_items.get(nombre, 0) + item['cantidad']

    producto_estrella = max(conteo_items, key=conteo_items.get) if conteo_items else "Sin ventas"

    return jsonify({
        "total_ventas": total_ventas,
        "ingresos_totales": round(ingresos_totales, 2),
        "producto_estrella": producto_estrella
    })

def enviar_factura_correo(destino, factura):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = destino
        msg['Subject'] = f"🥒 Factura Electrónica #{factura['id']} - Pepinos Locos"

        cuerpo = f"""
=====================================================
            🥒 PEPINOS LOCOS S.A. DE C.V. 🥒
                 FACTURA DE VENTA
=====================================================
No. Factura: {factura['id']}
Fecha: {factura['fecha']}
DATOS DEL CLIENTE:
Nombre: {factura['cliente'].get('nombre', 'Cliente General')}
NIT/DUI: {factura['cliente'].get('nit', 'N/A')}
Correo: {destino}
-----------------------------------------------------
DETALLE DEL PEDIDO:
-----------------------------------------------------
"""
        for item in factura['items']:
            cuerpo += f"- {item['nombre']} x{item['cantidad']} -> ${item['precio'] * item['cantidad']:.2f}\n"

        cuerpo += f"""-----------------------------------------------------
Subtotal: ${factura['subtotal']:.2f}
IVA (13%): ${factura['iva']:.2f}
TOTAL A PAGAR: ${factura['total']:.2f}
Pagado con: ${factura['monto_pago']:.2f}
Cambio: ${factura['cambio']:.2f}
=====================================================
      ¡Gracias por tu compra en Pepinos Locos! 🔥
"""
        msg.attach(MIMEText(cuerpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, PASSWORD_REMITENTE)
        server.sendmail(EMAIL_REMITENTE, destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error en correo:", e)
        return False

if __name__ == '__main__':
    print("🚀 Servidor corriendo en http://127.0.0.1:5000")
    app.run(debug=True, port=5000)