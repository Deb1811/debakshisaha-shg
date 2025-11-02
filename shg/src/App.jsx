import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'
import Landing from './components/landing/Landing'
import Chatbot from './components/chatbot/Chatbot'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/chatbot" element={<Chatbot />} />
      </Routes>
    </Router>
  )
}

export default App
