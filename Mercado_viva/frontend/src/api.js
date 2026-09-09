const API = '/api/v1'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })

  if (!response.ok) {
    let detalle = `Error ${response.status}`
    try {
      const body = await response.json()
      detalle = body.detail || body.mensaje || detalle
    } catch {
      /* ignore */
    }
    throw new Error(detalle)
  }

  return response.json()
}

export function obtenerProductos() {
  return request('/productos')
}

export function verificarLote(items) {
  return request('/inventario/verificar-lote', {
    method: 'POST',
    body: JSON.stringify({ items: items.map(({ id, cantidad }) => ({ id, cantidad })) }),
  })
}

export function confirmarPedido(items) {
  return request('/pedidos/confirmar', {
    method: 'POST',
    body: JSON.stringify({ items: items.map(({ id, cantidad }) => ({ id, cantidad })) }),
  })
}

export function obtenerPedidos() {
  return request('/pedidos')
}
