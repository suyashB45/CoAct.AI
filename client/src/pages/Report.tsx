"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Loader2, Download, AlertCircle, TrendingUp, Brain, MessageSquare, Zap, BookOpen, Target, Trophy, Clock, User, Bot, History, Sparkles, Lightbulb, CheckCircle, ChevronUp, ChevronDown } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import Navigation from "../components/landing/Navigation"

// Helper to map signals to scores
// Helper to map signals to colors
const getSignalColor = (signal: string) => {
    switch (signal) {
        case "Starting Out": return "bg-red-400"
        case "Developing": return "bg-amber-400"
        case "Consistent": return "bg-emerald-400"
        case "Fluent": return "bg-blue-400"
        default: return "bg-slate-400"
    }
}

// Linear Progress Bar Component
const ProgressBar = ({ value, colorClass = "bg-blue-500", height = "h-2" }: { value: number, colorClass?: string, height?: string }) => {
    return (
        <div className="w-full bg-slate-200/20 rounded-full overflow-hidden">
            <motion.div
                initial={{ width: 0 }}
                whileInView={{ width: `${value}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={`${height} ${colorClass} rounded-full`}
                style={{ width: `${value}%` }}
            />
        </div>
    )
}


// Premium Line Chart Component with Glow
const SessionLineChart = ({ data, color = "#60a5fa", label, height = 60 }: { data: number[], color?: string, label?: string, height?: number }) => {
    if (!data || data.length < 2) return null
    const max = Math.max(...data, 1)
    const points = data.map((val, i) => {
        const x = (i / (data.length - 1)) * 100
        const y = 100 - ((val / max) * 100)
        return `${x},${y}`
    }).join(" ")

    return (
        <div className="w-full">
            <div className="flex justify-between text-xs text-slate-500 uppercase tracking-widest font-bold mb-2 pl-1">
                <span>Start</span>
                <span>{label}</span>
                <span>End</span>
            </div>
            <div className="relative w-full" style={{ height: `${height}px` }}>
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
                    <defs>
                        <linearGradient id={`grad-${label}`} x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
                            <stop offset="100%" stopColor={color} stopOpacity="0" />
                        </linearGradient>
                        <filter id={`glow-${label}`} x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    {/* Area Fill */}
                    <polygon points={`0,100 ${points} 100,100`} fill={`url(#grad-${label})`} />

                    {/* Glow Line */}
                    <polyline
                        points={points}
                        fill="none"
                        stroke={color}
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        vectorEffect="non-scaling-stroke"
                        style={{ filter: `drop-shadow(0 0 4px ${color})` }}
                    />

                    {/* Data Points */}
                    {data.map((val, i) => {
                        const x = (i / (data.length - 1)) * 100
                        const y = 100 - ((val / max) * 100)
                        return (
                            <circle
                                key={i}
                                cx={x}
                                cy={y}
                                r="3"
                                fill="white"
                                stroke={color}
                                strokeWidth="2"
                                vectorEffect="non-scaling-stroke"
                                style={{ filter: `drop-shadow(0 0 2px ${color})` }}
                            />
                        )
                    })}
                </svg>
            </div>
        </div>
    )
}

interface SkillSnapshot {
    name: string
    signal: "Starting Out" | "Developing" | "Consistent" | "Fluent"
    text: string
}

interface TranscriptMessage {
    role: "user" | "assistant"
    content: string
}

interface CoachingOpportunity {
    you_said: string
    try_this: string
    why: string
}

interface ReportData {
    meta: {
        fit_label: string
        fit_score?: number
        summary: string
    }
    sidebar_data?: {
        top_traits?: string[]
        improvements?: string[]
    }
    skill_snapshot?: SkillSnapshot[]
    coach_rewrite_card?: {
        title: string
        context: string
        original_user_response: string
        pro_rewrite: string
        why_it_works: string
    }
    learning_plan?: {
        priority_focus: string
        recommended_drill: string
        suggested_reading: string
    }
    // Coaching-focused fields
    observed_strengths?: string[]
    coaching_opportunities?: CoachingOpportunity[]
    practice_prompts?: string[]
    transcript?: TranscriptMessage[]
    scenario?: string
    // Coaching sections
    turning_point?: {
        occurred: boolean
        moment: string | null
        before_state: string
        after_state: string
        analysis: string
    }
    vocabulary_coaching?: {
        lean_in_phrases: string[]
        lean_away_phrases: string[]
        coaching_tip: string
    }
    reflection_guide?: string[]
    pace_data?: number[]  // Words per Turn
    sentiment_arc?: number[] // 1-10 Sentiment
    behavioral_cards?: {
        trait: string
        score: number
        text: string
    }[]
}


export default function Report() {
    const params = useParams()
    const navigate = useNavigate()
    const sessionId = params.sessionId as string
    const [data, setData] = useState<ReportData | null>(null)
    const [loading, setLoading] = useState(true)
    const [showTranscript, setShowTranscript] = useState(false)
    const [showContext, setShowContext] = useState(true)

    useEffect(() => {
        const fetchReport = async () => {
            try {
                if (!sessionId) return

                // Fetch from backend
                const response = await fetch(`http://localhost:8000/api/session/${sessionId}/report_data`)
                if (!response.ok) {
                    throw new Error("Failed to fetch report data")
                }

                const data: ReportData = await response.json()
                setData(data)
                setLoading(false)
            } catch (err) {
                console.error("Error generating report:", err)
                setLoading(false)
            }
        }

        fetchReport()
    }, [sessionId])

    const handleDownload = async () => {
        try {
            // Fetch the PDF from backend
            const response = await fetch(`http://localhost:8000/api/report/${sessionId}`)

            if (!response.ok) {
                throw new Error("Failed to generate PDF")
            }

            // Get the PDF blob and trigger download
            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `CoActAI_Report_${sessionId}.pdf`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            window.URL.revokeObjectURL(url)
        } catch (error) {
            console.error("Error downloading PDF:", error)
            alert("PDF export failed. Please ensure the backend is running.")
        }
    }

    const getSignalBg = (signal: string) => {
        switch (signal) {
            case 'Fluent': return "bg-emerald-500/20 border-emerald-500/30"
            case 'Consistent': return "bg-emerald-500/20 border-emerald-500/30"
            case 'Developing': return "bg-amber-500/20 border-amber-500/30"
            case 'Starting Out': return "bg-rose-500/20 border-rose-500/30"
            default: return "bg-amber-500/20 border-amber-500/30"
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 gap-6 font-sans">
                <div className="relative">
                    <div className="absolute inset-0 rounded-full bg-blue-500/30 animate-ping" />
                    <Loader2 className="h-16 w-16 animate-spin text-blue-400 relative z-10" />
                </div>
                <div className="text-center">
                    <p className="text-white font-bold text-2xl mb-2">Preparing Your Insights</p>
                    <p className="text-slate-400 animate-pulse">Crafting your personalized coaching reflection...</p>
                </div>
            </div>
        )
    }

    if (!data || !data.meta) {
        return (
            <div className="min-h-screen bg-slate-950 p-12 flex flex-col items-center justify-center font-sans">
                <div className="w-24 h-24 bg-amber-500/10 rounded-full flex items-center justify-center mb-8 border border-amber-500/20">
                    <AlertCircle className="h-12 w-12 text-amber-500" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-3">Report Unavailable</h2>
                <p className="text-slate-400 mb-8 text-center max-w-md text-lg">We couldn't load the analysis data. This might be because the session was too short or there was a processing error.</p>
                <div className="flex gap-4">
                    <button onClick={() => navigate("/")} className="btn-ultra-modern px-8 py-3">
                        Go Home
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-purple-500/30">
            <Navigation />

            {/* Background */}
            <div className="fixed inset-0 pointer-events-none -z-10">
                <div className="absolute top-[-20%] left-1/4 w-[800px] h-[800px] bg-blue-900/10 rounded-full blur-[120px]" />
            </div>

            <main className="container mx-auto px-6 py-32 space-y-12">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-white">Coaching Practice Reflection</h1>
                    <button onClick={handleDownload} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-colors border border-white/10">
                        <Download className="w-4 h-4" /> Export PDF
                    </button>
                </div>

                {/* Hero Score Section */}
                <div className="grid lg:grid-cols-12 gap-8">
                    {/* Main Score Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="lg:col-span-8 relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-blue-900/40 via-slate-900/80 to-slate-950 border border-white/10 p-10 md:p-14 shadow-2xl group"
                    >
                        {/* Animated gradient orb */}
                        <div className="absolute top-0 right-0 p-16 opacity-20 pointer-events-none group-hover:opacity-30 transition-opacity duration-700">
                            <div className="w-64 h-64 bg-blue-500 rounded-full blur-[100px] morph-blob" />
                        </div>
                        <div className="absolute -bottom-20 -left-20 w-48 h-48 bg-purple-500/20 rounded-full blur-[80px] morph-blob" style={{ animationDelay: '-4s' }} />

                        <div className="relative z-10">
                            <div className="flex items-center gap-3 mb-6">
                                <span className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider border shadow-lg animate-count-up ${getSignalBg(data.meta.fit_label)}`}>
                                    {data.meta.fit_label}
                                </span>
                                <span className="text-slate-400 text-sm font-medium flex items-center gap-1">
                                    <Clock className="w-4 h-4" /> Just now
                                </span>
                            </div>

                            {/* Qualitative Alignment Label */}
                            <h2 className="text-5xl md:text-7xl font-black text-white mb-8 leading-tight tracking-tight">
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400">
                                    {data.meta.fit_label || 'Developing'}
                                </span>
                            </h2>

                            <p className="text-xl md:text-2xl text-slate-300 leading-relaxed max-w-3xl font-light">
                                {data.meta.summary}
                            </p>
                        </div>
                    </motion.div>

                    {/* Skill Development Side Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="lg:col-span-4 card-ultra-glass p-10 flex flex-col justify-between relative overflow-hidden group"
                    >
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/20 rounded-full blur-[60px] group-hover:bg-purple-500/30 transition-colors duration-500" />
                        <div>
                            <h3 className="text-slate-400 text-sm font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-purple-400" /> Skill Development
                            </h3>
                            <div className="text-4xl font-black text-white mb-8">Growth Focus</div>
                        </div>

                        <div className="space-y-4">
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Key Strength</div>
                                <div className="text-white font-semibold text-lg">{data.sidebar_data?.top_traits?.[0] || "Your strengths are emerging!"}</div>
                            </div>
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Practice Area</div>
                                <div className="text-white font-semibold text-lg">{data.sidebar_data?.improvements?.[0] || "Continued growth"}</div>
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* Session Context Section */}
                {data.scenario && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass overflow-hidden"
                    >
                        <div
                            className="p-8 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                            onClick={() => setShowContext(!showContext)}
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center text-blue-400 shadow-lg shadow-blue-500/10">
                                    <Target className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">Session Context</h3>
                                    <p className="text-sm text-slate-400">The scenario being practiced</p>
                                </div>
                            </div>
                            <Button variant="ghost" className="text-slate-400">
                                {showContext ? "Hide" : "Show"}
                            </Button>
                        </div>

                        <AnimatePresence>
                            {showContext && (
                                <motion.div
                                    initial={{ height: 0 }}
                                    animate={{ height: "auto" }}
                                    exit={{ height: 0 }}
                                    className="bg-black/20"
                                >
                                    <div className="p-8 pt-0">
                                        <div className="h-px w-full bg-white/5 mb-6" />
                                        <div className="p-8 rounded-2xl bg-white/5 border border-white/10 text-slate-300 leading-relaxed italic text-lg shadow-inner">
                                            "{data.scenario}"
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                )}

                {/* Session Overview (Transcript) */}
                {data.transcript && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass overflow-hidden"
                    >
                        <div
                            className="p-8 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                            onClick={() => setShowTranscript(!showTranscript)}
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-lg shadow-indigo-500/10">
                                    <History className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">Session Overview</h3>
                                    <p className="text-sm text-slate-400">View full conversation transcript</p>
                                </div>
                            </div>
                            <Button variant="ghost" className="text-slate-400">
                                {showTranscript ? "Hide" : "Show"}
                            </Button>
                        </div>

                        <AnimatePresence>
                            {showTranscript && (
                                <motion.div
                                    initial={{ height: 0 }}
                                    animate={{ height: "auto" }}
                                    exit={{ height: 0 }}
                                    className="bg-black/20"
                                >
                                    <div className="p-8 pt-0 space-y-6 max-h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                                        <div className="h-px w-full bg-white/5 mb-6" />
                                        {data.transcript.map((msg, idx) => (
                                            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                {msg.role === 'assistant' && (
                                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shrink-0 mt-1">
                                                        <Bot className="w-5 h-5 text-white" />
                                                    </div>
                                                )}

                                                <div className={`p-6 rounded-3xl max-w-[80%] text-base leading-relaxed shadow-lg ${msg.role === 'user'
                                                    ? 'bg-blue-600 border border-blue-500 text-white rounded-tr-none'
                                                    : 'bg-white/10 border border-white/5 text-slate-200 rounded-tl-none backdrop-blur-md'
                                                    }`}>
                                                    {msg.content}
                                                </div>

                                                {msg.role === 'user' && (
                                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shrink-0 mt-1">
                                                        <User className="w-5 h-5 text-white" />
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                )}

                {/* Skill Reflection */}
                {data.skill_snapshot && data.skill_snapshot.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center text-blue-400 shadow-lg shadow-blue-500/10">
                                <Brain className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white">Skill Reflection</h3>
                                <p className="text-slate-400 text-sm">Celebrating your communication journey</p>
                            </div>
                        </div>

                        <div className="grid lg:grid-cols-3 gap-8">
                            <div className="lg:col-span-2 space-y-8">
                                {/* Fit Score Header */}
                                {data.meta.fit_score !== undefined && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        className="p-6 rounded-3xl bg-white/5 border border-white/10"
                                    >
                                        <div className="flex justify-between items-end mb-4">
                                            <div>
                                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-1">Overall Performance</h3>
                                                <div className="flex items-baseline gap-2">
                                                    <span className="text-4xl font-black text-white">{data.meta.fit_score.toFixed(1)}</span>
                                                    <span className="text-lg text-slate-400">/ 10</span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <span className={`px-4 py-1.5 rounded-full text-sm font-bold bg-white/10 text-white border border-white/20`}>
                                                    {data.meta.fit_label}
                                                </span>
                                            </div>
                                        </div>
                                        <ProgressBar value={data.meta.fit_score * 10} height="h-6" colorClass="bg-gradient-to-r from-emerald-400 to-blue-500" />
                                        <div className="flex justify-between mt-2 text-xs text-slate-500 font-medium">
                                            <span>Starting Out</span>
                                            <span>Developing</span>
                                            <span>Consistent</span>
                                            <span>Fluent</span>
                                        </div>
                                    </motion.div>
                                )}

                                {/* Skills Grid */}
                                <div className="grid md:grid-cols-2 gap-6">
                                    {data.skill_snapshot.map((skill, i) => {
                                        let percentage = 25
                                        if (skill.signal === "Developing") percentage = 50
                                        if (skill.signal === "Consistent") percentage = 75
                                        if (skill.signal === "Fluent") percentage = 100

                                        return (
                                            <motion.div
                                                key={i}
                                                initial={{ opacity: 0, x: 20 }}
                                                whileInView={{ opacity: 1, x: 0 }}
                                                viewport={{ once: true }}
                                                transition={{ delay: i * 0.1 }}
                                                className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                                            >
                                                <div className="flex justify-between items-start mb-4">
                                                    <div>
                                                        <h4 className="font-bold text-white text-lg mb-1">{skill.name}</h4>
                                                        <span className={`text-xs font-bold uppercase tracking-wider text-slate-400`}>
                                                            {skill.signal}
                                                        </span>
                                                    </div>
                                                    <div className="w-12 text-right font-mono text-white/50 text-sm">
                                                        {percentage}%
                                                    </div>
                                                </div>

                                                <div className="mb-4">
                                                    <ProgressBar value={percentage} colorClass={getSignalColor(skill.signal)} />
                                                </div>

                                                <p className="text-sm text-slate-400 leading-relaxed">{skill.text}</p>
                                            </motion.div>
                                        )
                                    })}
                                </div>
                            </div>

                            {/* Sidebar: Traits & Improvements */}
                            <div className="space-y-6">
                                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                                    <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2 uppercase tracking-wider">
                                        <Target className="w-4 h-4 text-emerald-400" /> Top Traits
                                    </h4>
                                    <div className="space-y-3">
                                        {(data.sidebar_data?.top_traits ?? []).map((t, i) => (
                                            <div key={i} className="flex items-center gap-3 text-slate-300">
                                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                                <span>{t}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                                    <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2 uppercase tracking-wider">
                                        <TrendingUp className="w-4 h-4 text-amber-400" /> Areas of Improvement
                                    </h4>
                                    <div className="space-y-3">
                                        {(data.sidebar_data?.improvements ?? ["Focus on clarity", "Practice pacing"]).map((t, i) => (
                                            <div key={i} className="flex items-center gap-3 text-slate-300">
                                                <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                                                <span>{t}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Behavioral Analysis */}
                        {data.behavioral_cards && data.behavioral_cards.length > 0 && (
                            <div className="mt-10 pt-8 border-t border-white/10">
                                <h4 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                                    <Brain className="w-5 h-5 text-purple-400" /> Behavioral Analysis
                                </h4>
                                <div className="grid md:grid-cols-3 gap-6">
                                    {data.behavioral_cards.map((card, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, y: 10 }}
                                            whileInView={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                            className="p-6 rounded-2xl bg-white/5 border border-white/10"
                                        >
                                            <div className="flex justify-between items-start mb-3">
                                                <h5 className="font-bold text-white">{card.trait}</h5>
                                                <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-xs font-bold border border-purple-500/30">
                                                    {card.score}
                                                </div>
                                            </div>
                                            <p className="text-sm text-slate-400 leading-relaxed">{card.text}</p>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.section>
                )}

                {/* Instant Fix Card (Coach Rewrite) */}
                {data.coach_rewrite_card && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-[2.5rem] bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-500/30 p-1 relative overflow-hidden group shadow-2xl"
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:animate-[shimmer_2s_infinite] pointer-events-none" />

                        <div className="bg-slate-950/90 backdrop-blur-xl rounded-[2.4rem] p-10 md:p-14 relative z-10">
                            <div className="flex items-center gap-4 mb-10">
                                <div className="p-4 bg-yellow-500/20 text-yellow-400 rounded-2xl shadow-lg shadow-yellow-500/10">
                                    <Zap className="w-8 h-8 fill-current" />
                                </div>
                                <div>
                                    <h3 className="text-3xl font-bold text-white">Coaching Insight</h3>
                                    <p className="text-slate-400 text-lg">A moment with wonderful growth potential</p>
                                </div>
                            </div>

                            <div className="grid md:grid-cols-2 gap-10 md:gap-16">
                                <div className="space-y-4 relative">
                                    <div className="absolute -left-6 top-0 bottom-0 w-1.5 bg-rose-500/30 rounded-full" />
                                    <h4 className="text-sm font-bold text-rose-400 uppercase tracking-widest pl-2">You Said</h4>
                                    <p className="text-xl text-slate-300 italic pl-2 leading-relaxed font-light">
                                        "{data.coach_rewrite_card.original_user_response}"
                                    </p>
                                </div>
                                <div className="space-y-5 relative">
                                    <div className="absolute -left-6 top-0 bottom-0 w-1.5 bg-emerald-500/30 rounded-full" />
                                    <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-widest pl-2">Coach Suggests</h4>
                                    <p className="text-xl text-emerald-100 font-medium pl-2 leading-relaxed">
                                        "{data.coach_rewrite_card.pro_rewrite}"
                                    </p>
                                    <div className="pl-2 pt-4">
                                        <p className="text-sm text-slate-400 bg-white/5 p-5 rounded-2xl border border-white/5 leading-relaxed">
                                            <span className="text-slate-200 font-bold block mb-2 text-base">Why this works:</span>
                                            {data.coach_rewrite_card.why_it_works}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}


                {/* Observed Strengths & Coaching Opportunities */}
                {(data.observed_strengths || data.coaching_opportunities) && (
                    <div className="grid lg:grid-cols-2 gap-8">
                        {/* Observed Strengths */}
                        {data.observed_strengths && data.observed_strengths.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                className="card-ultra-glass p-10"
                            >
                                <div className="flex items-center gap-4 mb-8">
                                    <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/10">
                                        <CheckCircle className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-2xl font-bold text-white">Your Shining Moments</h3>
                                </div>
                                <ul className="space-y-4">
                                    {data.observed_strengths.map((strength, i) => (
                                        <li key={i} className="flex items-start gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                            <CheckCircle className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0" />
                                            <span className="text-slate-300">{strength}</span>
                                        </li>
                                    ))}
                                </ul>
                            </motion.section>
                        )}

                        {/* Session Flow & Trends */}
                        {(data.pace_data || data.sentiment_arc) && (
                            <motion.section
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                className="grid md:grid-cols-2 gap-6"
                            >
                                {data.sentiment_arc && (
                                    <div className="card-ultra-glass p-8">
                                        <div className="flex items-center gap-3 mb-6">
                                            <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-400">
                                                <TrendingUp className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-bold text-white">Emotional Flow</h3>
                                                <p className="text-xs text-slate-400">Sentiment trajectory</p>
                                            </div>
                                        </div>
                                        <SessionLineChart data={data.sentiment_arc} color="#10b981" label="Sentiment" />
                                    </div>
                                )}

                                {data.pace_data && (
                                    <div className="card-ultra-glass p-8">
                                        <div className="flex items-center gap-3 mb-6">
                                            <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                                                <Clock className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-bold text-white">Communication Volume</h3>
                                                <p className="text-xs text-slate-400">Words per turn</p>
                                            </div>
                                        </div>
                                        <SessionLineChart data={data.pace_data} color="#60a5fa" label="Volume" />
                                    </div>
                                )}
                            </motion.section>
                        )}

                        {/* Coaching Opportunities */}
                        {data.coaching_opportunities && data.coaching_opportunities.length > 0 && (
                            <motion.section
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                className="card-ultra-glass p-10"
                            >
                                <div className="flex items-center gap-4 mb-8">
                                    <div className="w-12 h-12 rounded-2xl bg-amber-500/20 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/10">
                                        <Lightbulb className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-2xl font-bold text-white">Growth Opportunities</h3>
                                </div>
                                <div className="space-y-6">
                                    {data.coaching_opportunities.map((opp, i) => (
                                        <div key={i} className="p-5 rounded-xl bg-white/5 border border-white/10">
                                            <div className="mb-4 p-4 rounded-lg bg-rose-500/5 border border-rose-500/10">
                                                <span className="text-rose-400 font-semibold text-sm uppercase tracking-widest flex items-center gap-2">
                                                    <User className="w-4 h-4" /> Your Words:
                                                </span>
                                                <p className="text-slate-300 italic mt-2 text-lg">"{opp.you_said}"</p>
                                            </div>
                                            <div className="mb-4 p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                                                <span className="text-emerald-400 font-semibold text-sm uppercase tracking-widest flex items-center gap-2">
                                                    <Sparkles className="w-4 h-4" /> A Lovely Alternative:
                                                </span>
                                                <p className="text-emerald-100 font-medium mt-2 text-lg">"{opp.try_this}"</p>
                                            </div>
                                            <div className="p-4 bg-slate-950/50 rounded-lg border border-white/5">
                                                <span className="text-blue-400 font-semibold text-sm flex items-center gap-2">
                                                    <Lightbulb className="w-4 h-4" /> Why This Works:
                                                </span>
                                                <p className="text-slate-400 mt-2">{opp.why}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}
                    </div>
                )}

                {/* Practice Prompts */}
                {data.practice_prompts && data.practice_prompts.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-12 h-12 rounded-2xl bg-purple-500/20 flex items-center justify-center text-purple-400 shadow-lg shadow-purple-500/10">
                                <Target className="w-6 h-6" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">Practice Prompts</h3>
                        </div>
                        <div className="grid md:grid-cols-3 gap-4">
                            {data.practice_prompts.map((prompt, i) => (
                                <div key={i} className="p-5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-slate-300">
                                    {prompt}
                                </div>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* Turning Point Analysis */}
                {data.turning_point && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <div className="flex items-center gap-4 mb-8">
                            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg ${data.turning_point.occurred ? 'bg-emerald-500/20 text-emerald-400 shadow-emerald-500/10' : 'bg-amber-500/20 text-amber-400 shadow-amber-500/10'}`}>
                                <Zap className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white">The Turning Point</h3>
                                <p className="text-slate-400 text-sm">{data.turning_point.occurred ? 'A beautiful breakthrough moment!' : 'Your next breakthrough is waiting - keep practicing!'}</p>
                            </div>
                        </div>

                        {data.turning_point.occurred && data.turning_point.moment && (
                            <div className="mb-8 p-6 rounded-xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 border border-emerald-500/20">
                                <p className="text-xl text-emerald-100 font-medium italic">"{data.turning_point.moment}"</p>
                            </div>
                        )}

                        <div className="grid md:grid-cols-2 gap-6 mb-6">
                            <div className="p-5 rounded-xl bg-rose-500/10 border border-rose-500/20">
                                <h4 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-2">Before</h4>
                                <p className="text-slate-300">{data.turning_point.before_state}</p>
                            </div>
                            <div className="p-5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">After</h4>
                                <p className="text-slate-300">{data.turning_point.after_state}</p>
                            </div>
                        </div>

                        <div className="p-5 rounded-xl bg-white/5 border border-white/10">
                            <h4 className="text-sm font-bold text-slate-300 uppercase tracking-widest mb-2">Analysis</h4>
                            <p className="text-slate-400">{data.turning_point.analysis}</p>
                        </div>
                    </motion.section>
                )}

                {/* Vocabulary Coaching */}
                {data.vocabulary_coaching && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-12 h-12 rounded-2xl bg-violet-500/20 flex items-center justify-center text-violet-400 shadow-lg shadow-violet-500/10">
                                <MessageSquare className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white">Vocabulary Coaching</h3>
                                <p className="text-slate-400 text-sm">Words that shape your conversation quality</p>
                            </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-6 mb-8">
                            <div className="p-6 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <ChevronUp className="w-4 h-4" /> Lean In Phrases
                                </h4>
                                <ul className="space-y-2">
                                    {(data.vocabulary_coaching.lean_in_phrases ?? []).map((phrase, i) => (
                                        <li key={i} className="text-emerald-100 text-sm p-2 rounded bg-emerald-500/10">"{phrase}"</li>
                                    ))}
                                </ul>
                            </div>
                            <div className="p-6 rounded-xl bg-rose-500/10 border border-rose-500/20">
                                <h4 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <ChevronDown className="w-4 h-4" /> Lean Away Phrases
                                </h4>
                                <ul className="space-y-2">
                                    {(data.vocabulary_coaching.lean_away_phrases ?? []).map((phrase, i) => (
                                        <li key={i} className="text-rose-100 text-sm p-2 rounded bg-rose-500/10">"{phrase}"</li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        <div className="p-5 rounded-xl bg-gradient-to-r from-violet-500/10 to-blue-500/10 border border-violet-500/20">
                            <h4 className="text-sm font-bold text-violet-300 uppercase tracking-widest mb-2">Coaching Tip</h4>
                            <p className="text-slate-300">{data.vocabulary_coaching.coaching_tip}</p>
                        </div>
                    </motion.section>
                )}

                {/* Reflection Guide */}
                {data.reflection_guide && data.reflection_guide.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/10">
                                <Brain className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white">Reflection Guide</h3>
                                <p className="text-slate-400 text-sm">Inspiring questions for your journey</p>
                            </div>
                        </div>

                        <div className="space-y-4">
                            {data.reflection_guide.map((question, i) => (
                                <div key={i} className="p-6 rounded-xl bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 flex items-start gap-4">
                                    <span className="w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-lg font-bold shrink-0">{i + 1}</span>
                                    <p className="text-slate-200 text-lg leading-relaxed">{question}</p>
                                </div>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* Learning Plan */}
                <section className="grid md:grid-cols-3 gap-8">
                    <div className="md:col-span-1 bg-gradient-to-br from-blue-600 to-blue-700 rounded-[2.5rem] p-10 text-white shadow-xl shadow-blue-900/30 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
                            <BookOpen className="w-32 h-32" />
                        </div>
                        <BookOpen className="w-10 h-10 mb-6 text-blue-200" />
                        <h3 className="text-xl font-bold mb-3">Primary Focus</h3>
                        <p className="text-blue-100 leading-relaxed text-lg opacity-90 font-medium">
                            {data.learning_plan?.priority_focus ?? 'Focus on clarity'}
                        </p>
                    </div>

                    <div className="md:col-span-1 card-ultra-glass p-10 group hover:border-amber-500/30 transition-colors">
                        <Trophy className="w-10 h-10 mb-6 text-amber-500 group-hover:scale-110 transition-transform duration-300" />
                        <h3 className="text-xl font-bold text-white mb-3">Recommended Drill</h3>
                        <p className="text-slate-400 leading-relaxed">
                            {data.learning_plan?.recommended_drill ?? 'Practice active listening'}
                        </p>
                    </div>

                    <div className="md:col-span-1 card-ultra-glass p-10 group hover:border-purple-500/30 transition-colors">
                        <Sparkles className="w-10 h-10 mb-6 text-purple-400 group-hover:scale-110 transition-transform duration-300" />
                        <h3 className="text-xl font-bold text-white mb-3">Expert Reading</h3>
                        <p className="text-slate-400 leading-relaxed italic">
                            "{data.learning_plan?.suggested_reading ?? 'Crucial Conversations'}"
                        </p>
                    </div>
                </section>

                {/* Footer */}
                <div className="text-center pt-16 pb-8 border-t border-white/5 text-slate-600 text-sm">
                    <p>Generated by CoAct.AI Performance Engine</p>
                </div>
            </main>
        </div>
    )
}
