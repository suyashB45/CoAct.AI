"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Loader2, Download, AlertCircle, TrendingUp, Target, User, Bot, History, Zap } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "@/lib/api"

// --- INTERFACES FOR UNIFIED REPORT STRUCTURE (Matching PDF) ---

// --- UNIVERSAL MODULAR STRUCTURE INTERFACES ---

interface PulseMetric {
    metric: string
    score: string | number // Can be 1-10 or "Beginner"/"Expert" level
    insight: string
}

interface NarrativeLayer {
    sentiment_curve?: string
    critical_pivots?: {
        green_light?: { turn?: string, event: string, quote?: string }
        red_light?: { turn?: string, event: string, quote?: string }
    }
    think_aloud?: {
        context: string
        thought: string
    }
}

interface BlueprintLayer {
    micro_correction?: string
    shadow_impact?: string
    homework_exercises?: string[]
}

interface ReportData {
    meta: {
        scenario_id: string
        outcome_status: string // Success, Partial, Failure
        overall_grade: string // A-F or 1-100
        summary: string
        scenario_type?: string
    }
    scenario_type?: string // legacy fallback

    // The 3 Universal Layers
    layer_1_pulse?: PulseMetric[]
    layer_2_narrative?: NarrativeLayer
    layer_3_blueprint?: BlueprintLayer

    // Legacy / Optional fields
    transcript?: { role: "user" | "assistant", content: string }[]
}

export default function Report() {
    const params = useParams()
    const navigate = useNavigate()
    const sessionId = params.sessionId as string
    const [data, setData] = useState<ReportData | null>(null)
    const [loading, setLoading] = useState(true)
    const [showTranscript, setShowTranscript] = useState(false)

    useEffect(() => {
        const fetchReport = async () => {
            try {
                if (!sessionId) return
                const response = await fetch(getApiUrl(`/api/session/${sessionId}/report_data`))
                if (!response.ok) throw new Error("Failed to fetch report data")
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
            const response = await fetch(getApiUrl(`/api/report/${sessionId}`))
            if (!response.ok) throw new Error("Failed to generate PDF")
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

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 gap-6 font-sans">
                <Loader2 className="h-16 w-16 animate-spin text-blue-400" />
                <p className="text-slate-400 animate-pulse">Generating Universal Report...</p>
            </div>
        )
    }

    if (!data || !data.meta) {
        return (
            <div className="min-h-screen bg-slate-950 p-12 flex flex-col items-center justify-center font-sans">
                <AlertCircle className="h-12 w-12 text-amber-500 mb-4" />
                <h2 className="text-3xl font-bold text-white mb-3">Report Unavailable</h2>
                <button onClick={() => navigate("/")} className="px-8 py-3 bg-slate-800 rounded-lg text-white hover:bg-slate-700">Go Home</button>
            </div>
        )
    }

    const pulse = data.layer_1_pulse || []
    const narrative = data.layer_2_narrative || {}
    const blueprint = data.layer_3_blueprint || {}

    // Helper for status color
    const getStatusColor = (status: string) => {
        const s = status?.toLowerCase() || ''
        if (s.includes('success') || s.includes('closed') || s.includes('motivated')) return 'text-emerald-400 border-emerald-500/50 bg-emerald-500/10'
        if (s.includes('failure') || s.includes('unresolved')) return 'text-rose-400 border-rose-500/50 bg-rose-500/10'
        return 'text-amber-400 border-amber-500/50 bg-amber-500/10' // Partial
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-purple-500/30">
            <Navigation />
            <main className="container mx-auto px-4 sm:px-6 py-24 sm:py-32 space-y-8">

                {/* HEADER & SUMMARY */}
                <div className="flex flex-col md:flex-row gap-6 justify-between items-start">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold text-white tracking-tight">{(data.meta?.scenario_id || "REPORT").toUpperCase()}</h1>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${getStatusColor(data.meta?.outcome_status)}`}>
                                {data.meta?.outcome_status || "Unknown"}
                            </span>
                        </div>
                        <p className="text-slate-400 max-w-2xl text-lg">{data.meta?.summary || "No summary available."}</p>
                    </div>
                    <div className="text-right flex flex-col items-end gap-2">
                        <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                            {data.meta?.scenario_type === "reflection" ? "N/A" : (data.meta?.overall_grade || "N/A")}
                        </div>
                        <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                            {(() => {
                                const st = (data.meta?.scenario_type || data.scenario_type || "").toLowerCase();
                                if (st.includes("coaching")) return "Coaching Efficacy";
                                if (st.includes("negotiation")) return "Negotiation Power";
                                if (st.includes("reflection")) return "Learning Insights";
                                return "Goal Attainment";
                            })()}
                        </div>
                        <button onClick={handleDownload} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors mt-2">
                            <Download className="w-4 h-4" /> Export PDF
                        </button>
                    </div>
                </div>

                {/* LAYER 1: THE PULSE (Metrics) - HIDE IF EMPTY (S3) */}
                {pulse.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        className="rounded-2xl bg-slate-900 border border-white/10 overflow-hidden"
                    >
                        <div className="bg-slate-800/50 px-6 py-4 border-b border-white/5 flex items-center gap-3">
                            <div className="p-2 bg-blue-500/20 rounded-lg"><TrendingUp className="w-5 h-5 text-blue-400" /></div>
                            <h2 className="text-lg font-bold text-white tracking-wide">LAYER 1: THE PULSE</h2>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-white/5">
                            {pulse.map((metric, i) => (
                                <div key={i} className="p-6 hover:bg-white/5 transition-colors group">
                                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">{metric.metric}</h3>
                                    <div className="flex items-baseline gap-2 mb-3">
                                        <span className={`text-3xl font-bold ${String(metric.score).includes('Expert') || Number(metric.score) >= 8 ? 'text-emerald-400' :
                                            Number(metric.score) <= 4 ? 'text-rose-400' : 'text-amber-400'
                                            }`}>
                                            {metric.score}
                                        </span>
                                        {typeof metric.score === 'number' && <span className="text-sm text-slate-600 font-medium">/ 10</span>}
                                    </div>
                                    <p className="text-sm text-slate-300 leading-relaxed opacity-80 group-hover:opacity-100">{metric.insight}</p>
                                </div>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* LAYER 2: THE NARRATIVE (Insights) */}
                <motion.section
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                    className="rounded-2xl bg-slate-900 border border-white/10 overflow-hidden"
                >
                    <div className="bg-slate-800/50 px-6 py-4 border-b border-white/5 flex items-center gap-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg"><User className="w-5 h-5 text-purple-400" /></div>
                        <h2 className="text-lg font-bold text-white tracking-wide">
                            {data.meta?.scenario_type === 'reflection' ? "LAYER 2: REFLECTIVE INSIGHTS" : "LAYER 2: THE NARRATIVE"}
                        </h2>
                    </div>
                    <div className="p-6 space-y-8">
                        {/* Sentiment Curve - Rename for S3? Keep unique. */}
                        <div className="relative pl-4 border-l-2 border-slate-800">
                            <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-2">
                                {data.meta?.scenario_type === 'reflection' ? "REFLECTION TIMELINE" : "AI SENTIMENT CURVE"}
                            </h3>
                            <p className="text-lg text-slate-200">{narrative.sentiment_curve || "Not available"}</p>
                        </div>

                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Critical Pivots / Key Moments */}
                            <div className="space-y-4">
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                                    {data.meta?.scenario_type === 'reflection' ? "KEY LEARNING MOMENTS" : "CRITICAL PIVOTS"}
                                </h3>
                                {narrative.critical_pivots?.green_light && (
                                    <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                            <span className="text-emerald-400 font-bold text-sm uppercase">
                                                {data.meta?.scenario_type === 'reflection' ? "POSITIVE PATTERN" : "GREEN LIGHT MOMENT"}
                                            </span>
                                        </div>
                                        <p className="text-slate-300 text-sm mb-2">{narrative.critical_pivots.green_light.event}</p>
                                        {narrative.critical_pivots.green_light.quote && (
                                            <p className="text-xs text-slate-500 italic">"{narrative.critical_pivots.green_light.quote}"</p>
                                        )}
                                    </div>
                                )}
                                {narrative.critical_pivots?.red_light && (
                                    <div className="bg-rose-950/20 border border-rose-500/20 rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <div className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]" />
                                            <span className="text-rose-400 font-bold text-sm uppercase">
                                                {data.meta?.scenario_type === 'reflection' ? "MISSED OPPORTUNITY" : "RED LIGHT MOMENT"}
                                            </span>
                                        </div>
                                        <p className="text-slate-300 text-sm mb-2">{narrative.critical_pivots.red_light.event}</p>
                                        {narrative.critical_pivots.red_light.quote && (
                                            <p className="text-xs text-slate-500 italic">"{narrative.critical_pivots.red_light.quote}"</p>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Think Aloud Reveal / Coach's Observation */}
                            <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-5 relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4 opacity-10"><Bot className="w-24 h-24 text-indigo-500" /></div>
                                <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <Zap className="w-4 h-4" />
                                    {data.meta?.scenario_type === 'reflection' ? "COACH'S OBSERVATION" : "THE \"THINK-ALOUD\" REVEAL"}
                                </h3>
                                <div className="relative z-10 space-y-4">
                                    <div>
                                        <span className="text-xs text-slate-500 uppercase block mb-1">When you said...</span>
                                        <p className="text-sm text-slate-300 italic">"{narrative.think_aloud?.context || '...'}"</p>
                                    </div>
                                    <div>
                                        <span className="text-xs text-slate-500 uppercase block mb-1">
                                            {data.meta?.scenario_type === 'reflection' ? "I observed..." : "I was actually thinking..."}
                                        </span>
                                        <p className="text-base text-white font-medium">"{narrative.think_aloud?.thought || '...'}"</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.section>

                {/* LAYER 3: THE BLUEPRINT (Development) */}
                <motion.section
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="rounded-2xl bg-slate-900 border border-white/10 overflow-hidden"
                >
                    <div className="bg-slate-800/50 px-6 py-4 border-b border-white/5 flex items-center gap-3">
                        <div className="p-2 bg-amber-500/20 rounded-lg"><Target className="w-5 h-5 text-amber-400" /></div>
                        <h2 className="text-lg font-bold text-white tracking-wide">
                            {data.meta?.scenario_type === 'reflection' ? "LAYER 3: PERSONAL LEARNING PLAN" : "LAYER 3: THE BLUEPRINT"}
                        </h2>
                    </div>
                    <div className="p-6 grid md:grid-cols-3 gap-6">
                        {/* Micro Correction / Key Insights (S3) */}
                        <div className="bg-slate-800/50 rounded-xl p-5 border border-white/5">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                                {data.meta?.scenario_type === 'reflection' ? "CRITICAL INSIGHTS" : "MICRO-CORRECTION"}
                            </h3>
                            <p className="text-slate-300 text-sm leading-relaxed">{blueprint.micro_correction || "No specific correction."}</p>
                        </div>

                        {/* Shadow Impact / Skill Focus (S3) */}
                        <div className="bg-slate-800/50 rounded-xl p-5 border border-white/5">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                                {data.meta?.scenario_type === 'reflection' ? "SKILL FOCUS AREA" : "THE SHADOW IMPACT"}
                            </h3>
                            <p className="text-slate-300 text-sm leading-relaxed">{blueprint.shadow_impact || "No long-term impact analysis."}</p>
                        </div>

                        {/* Actionable Homework / Practice Suggestions (S3) */}
                        <div className="bg-slate-800/50 rounded-xl p-5 border border-white/5">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
                                {data.meta?.scenario_type === 'reflection' ? "PRACTICE SUGGESTIONS" : "ACTIONABLE HOMEWORK"}
                            </h3>
                            <ul className="space-y-3">
                                {blueprint.homework_exercises?.map((ex, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                        <span className="text-amber-400 mt-0.5">▪</span>
                                        {ex}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </motion.section>


                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 10: SESSION TRANSCRIPT
                ══════════════════════════════════════════════════════════════════ */}
                {data.transcript && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-2xl bg-slate-900/80 border border-white/10 overflow-hidden"
                    >
                        <div
                            className="px-5 py-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                            onClick={() => setShowTranscript(!showTranscript)}
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                                    <History className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-base font-bold text-white">Session Transcript</h3>
                                    <p className="text-xs text-slate-400">View full conversation history</p>
                                </div>
                            </div>
                            <Button variant="ghost" size="sm" className="text-slate-400">
                                {showTranscript ? "Hide" : "Show"}
                            </Button>
                        </div>

                        <AnimatePresence>
                            {showTranscript && (
                                <motion.div
                                    initial={{ height: 0 }}
                                    animate={{ height: "auto" }}
                                    exit={{ height: 0 }}
                                    className="bg-black/30"
                                >
                                    <div className="p-5 pt-0 space-y-4 max-h-[500px] overflow-y-auto scrollbar-hide">
                                        <div className="h-px w-full bg-white/5 mb-4" />
                                        {data.transcript.map((msg, idx) => (
                                            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                {msg.role === 'assistant' && (
                                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shrink-0 mt-1">
                                                        <Bot className="w-4 h-4 text-white" />
                                                    </div>
                                                )}
                                                <div className={`p-4 rounded-2xl max-w-[85%] text-sm leading-relaxed ${msg.role === 'user'
                                                    ? 'bg-blue-600 border border-blue-500 text-white rounded-tr-none'
                                                    : 'bg-white/10 border border-white/5 text-slate-200 rounded-tl-none'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                                {msg.role === 'user' && (
                                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shrink-0 mt-1">
                                                        <User className="w-4 h-4 text-white" />
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
            </main>
        </div>
    )
}
