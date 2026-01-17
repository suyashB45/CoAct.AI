"use client"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Clock, User, Bot, CheckCircle2, PlayCircle, Calendar, Trophy } from "lucide-react"
import { motion } from "framer-motion"

import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "../lib/api"

interface SessionItem {
    id: string
    created_at: string
    role: string
    ai_role: string
    scenario: string
    completed: boolean
    fit_score: number
}

export default function SessionHistory() {
    const navigate = useNavigate()
    const [sessions, setSessions] = useState<SessionItem[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<'all' | 'completed' | 'ongoing'>('all')

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                // Fetch from backend
                const res = await fetch(getApiUrl('/api/sessions'))
                if (!res.ok) throw new Error('Failed to fetch sessions')

                const data = await res.json()

                // Map backend format to frontend interface if needed
                // Backend returns: SessionModel.to_dict()
                // Frontend SessionItem expects: id, created_at, role, ai_role...
                // They match mostly. We just need to ensure correct mapping.

                const mappedSessions = data.map((s: any) => ({
                    id: s.id,
                    created_at: s.created_at,
                    role: s.role,
                    ai_role: s.ai_role,
                    scenario: s.scenario,
                    completed: s.completed,
                    fit_score: s.fit_score // Ensure backend sends this
                }))

                setSessions(mappedSessions)
            } catch (err) {
                console.error("Failed to load sessions from API", err)
            } finally {
                setLoading(false)
            }
        }

        fetchSessions()
    }, [])

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date)
    }

    const filteredSessions = sessions.filter(s => {
        if (filter === 'completed') return s.completed
        if (filter === 'ongoing') return !s.completed
        return true
    })

    return (
        <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-purple-500/30">
            <Navigation />

            {/* Background */}
            <div className="fixed inset-0 pointer-events-none -z-10">
                <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] left-[-10%] w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[120px]" />
            </div>

            <main className="container mx-auto px-6 pt-32 pb-12">
                {/* Controls */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-12">
                    <div>
                        <h2 className="text-4xl font-bold text-white mb-2">Training Log</h2>
                        <p className="text-slate-400 text-lg">Track your progress and review past scenarios.</p>
                    </div>

                    <div className="flex bg-slate-900/50 backdrop-blur-md p-1.5 rounded-xl border border-white/10 shadow-lg">
                        {(['all', 'completed', 'ongoing'] as const).map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={`px-5 py-2 rounded-lg text-sm font-bold capitalize transition-all duration-300 btn-press ${filter === f
                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-900/30'
                                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                </div>

                {loading ? (
                    <div className="flex flex-col items-center justify-center py-32 text-slate-500">
                        <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-4" />
                        <p className="font-medium animate-pulse">Loading history...</p>
                    </div>
                ) : filteredSessions.length === 0 ? (
                    <div className="text-center py-24 card-ultra-glass border-dashed group">
                        <div className="w-20 h-20 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-6 text-slate-500 border border-white/5 group-hover:bg-slate-700/50 transition-colors animate-breathe">
                            <Clock className="w-10 h-10" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">No Sessions Found</h3>
                        <p className="text-slate-400 mb-8 max-w-md mx-auto">You haven't started any training sessions yet. Launch a new scenario to get started.</p>
                        <button onClick={() => navigate("/practice")} className="btn-ultra-modern btn-press px-8 py-3">
                            Start New Session
                        </button>
                    </div>
                ) : (
                    <div className="grid gap-6">
                        {filteredSessions.map((session, idx) => (
                            <motion.div
                                key={session.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                whileHover={{ y: -4, scale: 1.01 }}
                                className="group relative card-ultra-glass p-6 md:p-8 flex flex-col md:flex-row gap-8 md:items-center justify-between hover:border-blue-500/30 transition-all duration-300"
                            >
                                {/* Subtle hover glow */}
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-purple-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-3xl pointer-events-none" />
                                <div className="flex-1 space-y-4">
                                    <div className="flex items-center gap-3 text-xs font-bold tracking-wider text-slate-500 uppercase">
                                        <div className="flex items-center gap-1.5 bg-white/5 px-2 py-1 rounded-md">
                                            <Calendar className="w-3.5 h-3.5" />
                                            {formatDate(session.created_at)}
                                        </div>
                                        {session.completed ? (
                                            <span className="text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md flex items-center gap-1.5 border border-emerald-500/20">
                                                <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                                            </span>
                                        ) : (
                                            <span className="text-amber-400 bg-amber-500/10 px-2 py-1 rounded-md flex items-center gap-1.5 border border-amber-500/20">
                                                <PlayCircle className="w-3.5 h-3.5" /> In Progress
                                            </span>
                                        )}
                                    </div>

                                    <div>
                                        <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                                            {session.scenario}
                                        </h3>
                                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                                            <div className="flex items-center gap-1.5">
                                                <User className="w-4 h-4 text-blue-400" />
                                                <span className="text-slate-300">You: {session.role}</span>
                                            </div>
                                            <div className="w-1 h-1 bg-slate-700 rounded-full hidden md:block" />
                                            <div className="flex items-center gap-1.5">
                                                <Bot className="w-4 h-4 text-purple-400" />
                                                <span className="text-slate-300">AI: {session.ai_role}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-6 justify-between md:justify-end border-t md:border-t-0 border-white/5 pt-4 md:pt-0">
                                    {session.completed && session.fit_score > 0 && (
                                        <div className="text-right">
                                            <div className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Score</div>
                                            <div className={`text-3xl font-black ${session.fit_score >= 7 ? 'text-emerald-400' : session.fit_score >= 5 ? 'text-amber-400' : 'text-rose-400'}`}>
                                                {session.fit_score.toFixed(1)}<span className="text-sm text-slate-600 font-semibold ml-0.5">/10</span>
                                            </div>
                                        </div>
                                    )}

                                    <button
                                        onClick={() => session.completed ? navigate(`/report/${session.id}`) : navigate(`/conversation/${session.id}`)}
                                        className={`min-w-[140px] px-6 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all btn-press ${session.completed
                                            ? 'bg-slate-800 hover:bg-slate-700 text-white border border-white/10 hover:border-white/20'
                                            : 'btn-ultra-modern'
                                            }`}
                                    >
                                        {session.completed ? (
                                            <>
                                                <Trophy className="w-4 h-4" /> View Report
                                            </>
                                        ) : (
                                            <>
                                                <PlayCircle className="w-4 h-4" /> Resume
                                            </>
                                        )}
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    )
}
