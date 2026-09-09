import { useState } from 'react'
import Cliente from './components/Cliente.jsx'
import Picking from './components/Picking.jsx'

const VISTAS = [
  { id: 'cliente', label: 'Tienda' },
  { id: 'picking', label: 'Picking' },
]

export default function App() {
  const [vista, setVista] = useState('cliente')

  return (
    <div className="app">
      <header className="site-header">
        <div className="brand">
          <h1>Mercado Viva</h1>
          <span>Inventario omnicanal</span>
        </div>
        <nav className="nav">
          {VISTAS.map((item) => (
            <button
              key={item.id}
              className={vista === item.id ? 'active' : ''}
              onClick={() => setVista(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main">
        <div hidden={vista !== 'cliente'}>
          <Cliente />
        </div>
        <div hidden={vista !== 'picking'}>
          <Picking />
        </div>
      </main>
    </div>
  )
}
