import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'
import './overrides.css'
import './visual-refresh.css'
import './workspace-ui.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>,
)
