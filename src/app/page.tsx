'use client'

import { useEffect } from 'react'

export default function Home() {
  useEffect(() => {
    // Check if we're already behind the Caddy gateway with XTransformPort
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.has('XTransformPort')) {
      // We're already behind the gateway but Next.js caught the request
      // This shouldn't happen if Caddy is configured correctly
      // Just show a message and link to the correct URL
      return
    }

    // Redirect to the Caddy gateway which will proxy to Django
    // The Caddy gateway on port 81 handles XTransformPort routing
    const currentPort = window.location.port
    const currentHost = window.location.hostname

    if (currentPort === '3000') {
      // Accessing via Next.js dev server - redirect to Caddy gateway on port 81
      window.location.href = `http://${currentHost}:81/?XTransformPort=8000`
    } else if (currentPort === '81' || currentPort === '') {
      // Already on Caddy gateway - add the XTransformPort parameter
      window.location.href = '/?XTransformPort=8000'
    } else {
      // Fallback - try adding XTransformPort to current URL
      window.location.href = '/?XTransformPort=8000'
    }
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
      <div style={{ fontSize: '0.9rem', opacity: 0.7, marginTop: '1rem' }}>
        <a href="http://localhost:81/?XTransformPort=8000"
           style={{ color: '#d4af37', textDecoration: 'underline' }}>
          Click here if not redirected
        </a>
      </div>
    </div>
  )
}
