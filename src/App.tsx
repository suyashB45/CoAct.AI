import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AnimatePresence, motion } from 'framer-motion'
import Home from './pages/Home'
import Practice from './pages/Practice'
import Conversation from './pages/Conversation'
import Report from './pages/Report'
import SessionHistory from './pages/SessionHistory'

function AppContent() {
    const location = useLocation()

    return (
        <AnimatePresence mode="wait">
            <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="w-full"
            >
                <Routes location={location} key={location.pathname}>
                    <Route path="/" element={<Home />} />
                    <Route path="/practice" element={<Practice />} />
                    <Route path="/history" element={<SessionHistory />} />
                    <Route path="/conversation/:sessionId" element={<Conversation />} />
                    <Route path="/report/:sessionId" element={<Report />} />
                </Routes>
            </motion.div>
        </AnimatePresence>
    )
}

function App() {
    return (
        <BrowserRouter>
            <Toaster position="top-center" theme="dark" richColors />
            <AppContent />
        </BrowserRouter>
    )
}

export default App
