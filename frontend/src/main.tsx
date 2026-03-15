import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppLayout } from './routes/AppLayout'
import { PTOEntryView } from './views/pto/PTOEntryView'
import './styles.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { path: '/', element: <div style={{padding: '1rem'}}>Home. Go to PTO Entry.</div> },
      { path: '/pto-entry', element: <PTOEntryView /> }
    ]
  }
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
