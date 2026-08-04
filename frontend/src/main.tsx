import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './context/AuthContext.tsx'
import { StepUpAuthProvider } from './context/StepUpAuthContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <StepUpAuthProvider>
        <App />
      </StepUpAuthProvider>
    </AuthProvider>
  </StrictMode>,
)
