import { useEffect, useState } from 'react'
import { obtenerPedidos } from '../api.js'

export default function Picking() {
  const [pedidos, setPedidos] = useState([])
  const [error, setError] = useState('')

  async function cargar() {
    try {
      const data = await obtenerPedidos()
      setPedidos(data)
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    cargar()
    const id = setInterval(cargar, 3000)
    return () => clearInterval(id)
  }, [])

  return (
    <section className="panel">
      <h2>Órdenes de recolección</h2>
      <p className="hint">Solo aparecen pedidos con inventario pre-verificado y reservado.</p>
      {error && <p className="status err">{error}</p>}
      {pedidos.length === 0 ? (
        <p className="empty">No hay órdenes pendientes.</p>
      ) : (
        <div className="order-list">
          {pedidos.map((pedido) => (
            <article className="order" key={pedido.orden_id}>
              <div className="order-head">
                <h3>{pedido.orden_id}</h3>
                <span className="badge ok">{pedido.estado}</span>
              </div>
              <ul>
                {pedido.items.map((item) => (
                  <li key={`${pedido.orden_id}-${item.id}`}>
                    {item.cantidad} × {item.nombre} — {item.pasillo}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
