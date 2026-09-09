export default function ModalSustitutos({ resultado, onCerrar, onAceptar }) {
  const sustitutos = resultado.sustitutos_disponibles || []

  return (
    <div className="overlay" onClick={onCerrar}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Producto no disponible para domicilio</h3>
        <p className="hint">{resultado.mensaje}</p>
        {sustitutos.length === 0 ? (
          <p className="empty">No hay alternativas equivalentes en este momento.</p>
        ) : (
          sustitutos.map((alt) => (
            <div className="substitute" key={alt.id}>
              <div>
                <strong>{alt.nombre}</strong>
                <p className="meta">Stock físico: {alt.stock_fisico} un.</p>
              </div>
              <button className="btn ghost" onClick={() => onAceptar(resultado.producto_rechazado_id, alt)}>
                Aceptar sustituto
              </button>
            </div>
          ))
        )}
        <button className="btn danger wide" onClick={onCerrar}>
          Cancelar
        </button>
      </div>
    </div>
  )
}
