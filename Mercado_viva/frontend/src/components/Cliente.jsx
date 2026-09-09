import { useEffect, useState } from 'react'
import { confirmarPedido, obtenerProductos, verificarLote } from '../api.js'
import ModalSustitutos from './ModalSustitutos.jsx'

const UMBRAL = 2

export default function Cliente() {
  const [catalogo, setCatalogo] = useState([])
  const [carrito, setCarrito] = useState([])
  const [cantidades, setCantidades] = useState({})
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [confirmacion, setConfirmacion] = useState(null)
  const [agotado, setAgotado] = useState(null)

  async function cargarCatalogo() {
    try {
      const data = await obtenerProductos()
      setCatalogo(data)
      setCantidades((prev) => {
        const next = { ...prev }
        data.forEach((p) => {
          if (!next[p.id]) next[p.id] = 1
        })
        return next
      })
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    cargarCatalogo()
  }, [])

  function disponibleEnLinea(producto) {
    return producto.stock_fisico > UMBRAL
  }

  function agregar(producto) {
    const cantidad = Number(cantidades[producto.id] || 1)
    setConfirmacion(null)
    setCarrito((prev) => {
      const idx = prev.findIndex((item) => item.id === producto.id)
      if (idx >= 0) {
        const copia = [...prev]
        copia[idx] = { ...copia[idx], cantidad: copia[idx].cantidad + cantidad }
        return copia
      }
      return [...prev, { ...producto, cantidad }]
    })
  }

  function quitar(id) {
    setCarrito((prev) => prev.filter((item) => item.id !== id))
  }

  async function checkout(items = carrito) {
    if (items.length === 0) return
    setCargando(true)
    setError('')
    setConfirmacion(null)

    try {
      const resultado = await verificarLote(items)

      if (!resultado.aprobado) {
        setAgotado(resultado)
        return
      }

      const orden = await confirmarPedido(items)
      setCarrito([])
      setConfirmacion(orden)
      await cargarCatalogo()
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  function aceptarSustituto(idOriginal, sustituto) {
    const original = carrito.find((item) => item.id === idOriginal)
    const resto = carrito.filter((item) => item.id !== idOriginal && item.id !== sustituto.id)
    const existente = carrito.find((item) => item.id === sustituto.id)
    const cantidad = (existente?.cantidad || 0) + (original?.cantidad || 1)
    const actualizado = [...resto, { ...original, ...sustituto, cantidad }]

    setAgotado(null)
    setCarrito(actualizado)
    checkout(actualizado)
  }

  return (
    <div className="grid">
      <section className="panel">
        <h2>Catálogo</h2>
        <p className="hint">La venta en línea se habilita solo si el stock físico supera el umbral de seguridad (2 unidades).</p>
        {error && <p className="status err">{error}</p>}
        <div className="product-list">
          {catalogo.map((producto) => {
            const enLinea = disponibleEnLinea(producto)
            return (
              <article className="product" key={producto.id}>
                <div>
                  <h3>
                    {producto.nombre}
                    <span className={`badge ${enLinea ? 'ok' : 'off'}`}>
                      {enLinea ? 'En línea' : 'Agotado en línea'}
                    </span>
                  </h3>
                  <p className="meta">
                    {producto.pasillo} · {producto.stock_fisico} un. físicas
                  </p>
                </div>
                <div className="actions">
                  <input
                    className="qty"
                    type="number"
                    min="1"
                    value={cantidades[producto.id] || 1}
                    onChange={(e) =>
                      setCantidades((prev) => ({ ...prev, [producto.id]: Number(e.target.value) }))
                    }
                    disabled={!enLinea}
                  />
                  <button className="btn" disabled={!enLinea} onClick={() => agregar(producto)}>
                    Agregar
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      </section>

      <aside className="panel">
        <h2>Carrito</h2>
        <p className="hint">Al confirmar, se verifica la disponibilidad antes del pago.</p>
        {carrito.length === 0 ? (
          <p className="empty">No hay productos seleccionados.</p>
        ) : (
          <div className="cart-list">
            {carrito.map((item) => (
              <div className="cart-item" key={item.id}>
                <div>
                  <strong>{item.nombre}</strong>
                  <p className="meta">{item.cantidad} un.</p>
                </div>
                <button className="btn danger" onClick={() => quitar(item.id)}>
                  Quitar
                </button>
              </div>
            ))}
          </div>
        )}
        {confirmacion && (
          <div className="success-box" style={{ marginTop: 16 }}>
            <strong>Pedido {confirmacion.orden_id} confirmado</strong>
            <p>Stock reservado. El operario ya puede iniciar el picking.</p>
          </div>
        )}
        <button className="btn wide" disabled={carrito.length === 0 || cargando} onClick={() => checkout()}>
          {cargando ? 'Verificando…' : 'Confirmar pedido'}
        </button>
      </aside>

      {agotado && (
        <ModalSustitutos
          resultado={agotado}
          onCerrar={() => setAgotado(null)}
          onAceptar={aceptarSustituto}
        />
      )}
    </div>
  )
}
