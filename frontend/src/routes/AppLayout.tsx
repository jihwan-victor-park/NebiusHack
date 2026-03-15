import React from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import '@vaadin/react-components/button'
import '@vaadin/react-components/horizontal-layout'
import '@vaadin/react-components/vertical-layout'

export const AppLayout: React.FC = () => {
  const loc = useLocation()
  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', gap: 16, padding: '10px 16px', borderBottom: '1px solid #eee'}}>
        <div style={{fontWeight: 600}}>Timecard Demo</div>
        <Link to="/">Home</Link>
        <Link to="/pto-entry">PTO Entry</Link>
        <div style={{marginLeft: 'auto', color: '#777', fontSize: 12}}>{loc.pathname}</div>
      </div>
      <Outlet />
    </div>
  )
}
