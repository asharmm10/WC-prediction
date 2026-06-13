'use client'

import { useEffect } from 'react'

export default function Home() {
  useEffect(() => {
    // Redirect to the Django application running on port 8000
    // through the Caddy gateway with XTransformPort parameter
    window.location.href = '/?XTransformPort=8000'
  }, [])

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      gap: '1rem',
      background: '#0a0e17',
      color: '#d4af37',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <div style={{ fontSize: '3rem' }}>⚽</div>
      <div style={{ fontSize: '1.2rem', fontWeight: 600 }}>
        Loading World Cup 2026...
      </div>
    </div>
  )
}
