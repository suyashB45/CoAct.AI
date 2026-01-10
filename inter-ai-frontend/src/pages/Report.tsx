"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Loader2, Download, AlertCircle, TrendingUp, Brain, Target, User, Bot, History, CheckCircle, HelpCircle } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "@/lib/api"



interface TranscriptMessage {
    role: "user" | "assistant"
    content: string
    audio_url?: string | null
}

// --- NEW INTERFACES FOR MODES ---

interface SkillScore {
    dimension: string
    score: number
    interpretation: string
}

interface AssessmentObservation {
    moment: string
    analysis: string
}

interface ManagerRecs {
    immediate_action: string
    next_simulation: string
}

interface Readiness {
    label: string
    score: number
}

interface Insight {
    pattern: string
    description: string
}

interface SkillFocus {
    skill: string
    description: string
}

interface ReportData {
    meta: {
        summary: string
        emotional_trajectory?: string
    }
    mode?: "coaching" | "evaluation" | "learning" // 'learning' mapped to 'coaching' generally, but explicit here

    // --- ASSESSMENT MODE FIELDS ---
    skill_dimension_scores?: SkillScore[]
    tactical_observations?: {
        success?: AssessmentObservation
        risk?: AssessmentObservation
    }
    manager_recommendations?: ManagerRecs
    readiness_indicator?: Readiness
    effectiveness_insights?: { moment: string, reframe: string, why?: string }[]

    // --- LEARNING MODE FIELDS ---
    key_insights?: Insight[]
    reflective_questions?: string[]
    skill_focus_areas?: SkillFocus[]
    suggested_approaches?: { moment: string, alternative: string, benefit?: string }[]
    practice_plan?: string[]
    learning_outcome?: string

    // --- SHARED / LEGACY FIELDS ---
    observed_strengths?: { title: string, observation: string }[]
    growth_opportunities?: { title: string, observation: string, suggestion?: string }[]

    transcript?: TranscriptMessage[]
    scenario?: string
    pace_data?: number[]
    sentiment_arc?: number[]
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

                // Fetch from backend
                const response = await fetch(getApiUrl(`/api/session/${sessionId}/report_data`))
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

    const isAssessment = data.mode === "evaluation"

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-purple-500/30">
            <Navigation />

            {/* Background */}
            <div className="fixed inset-0 pointer-events-none -z-10">
                <div className={`absolute top-[-20%] left-1/4 w-[800px] h-[800px] rounded-full blur-[120px] ${isAssessment ? 'bg-indigo-900/10' : 'bg-emerald-900/10'}`} />
            </div>

            <main className="container mx-auto px-6 py-32 space-y-12">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">
                            {isAssessment ? "Performance Assessment" : "Skill Development Reflection"}
                        </h1>
                        <p className="text-slate-400 text-sm mt-1">
                            {isAssessment ? "Evaluation & Scoring Report" : "Coaching & Growth Journey"}
                        </p>
                    </div>

                    <button onClick={handleDownload} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-colors border border-white/10">
                        <Download className="w-4 h-4" /> Export PDF
                    </button>
                </div>

                {/* Hero Summary Section */}
                <div className="grid lg:grid-cols-12 gap-8">
                    {/* Main Summary Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="lg:col-span-8 relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-slate-900/80 to-slate-950 border border-white/10 p-10 md:p-14 shadow-2xl"
                    >
                        <div className="absolute top-0 right-0 p-32 opacity-10 bg-blue-500 rounded-full blur-[100px]" />

                        <div className="relative z-10">
                            <h2 className="text-4xl font-black text-white mb-6 leading-tight">
                                <span className={`text-transparent bg-clip-text bg-gradient-to-r ${isAssessment ? 'from-blue-400 to-rose-400' : 'from-emerald-400 to-teal-400'}`}>
                                    {isAssessment ? "Performance Summary" : "Reflection Summary"}
                                </span>
                            </h2>
                            <p className="text-xl text-slate-300 leading-relaxed font-light">
                                {data.meta.summary}
                            </p>
                        </div>
                    </motion.div>

                    {/* Side Stat Card */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="lg:col-span-4 card-ultra-glass p-10 flex flex-col justify-center items-center text-center relative overflow-hidden"
                    >
                        {isAssessment ? (
                            <>
                                <div className="absolute inset-0 bg-rose-500/5" />
                                <div className="relative z-10">
                                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">Overall Readiness</h3>
                                    <div className={`text-5xl font-black mb-2 ${(data.readiness_indicator?.score || 0) >= 7 ? 'text-emerald-400' :
                                        (data.readiness_indicator?.score || 0) >= 5 ? 'text-amber-400' : 'text-rose-400'
                                        }`}>
                                        {data.readiness_indicator?.label || "N/A"}
                                    </div>
                                    <div className="text-2xl font-bold text-white mb-2">{data.readiness_indicator?.score}/10</div>
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="absolute inset-0 bg-emerald-500/5" />
                                <div className="relative z-10">
                                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">Focus Area</h3>
                                    <div className="text-3xl font-bold text-white mb-4">
                                        {data.skill_focus_areas?.[0]?.skill || "General Growth"}
                                    </div>
                                    <p className="text-sm text-slate-400">
                                        "{data.learning_outcome?.substring(0, 60)}..."
                                    </p>
                                </div>
                            </>
                        )}
                    </motion.div>
                </div>

                {/* 1️⃣ ASSESSMENT MODE SPECIFIC CONTENT */}
                {isAssessment && data.skill_dimension_scores && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                            <Target className="w-6 h-6 text-rose-400" /> Skill Dimension Scores
                        </h3>

                        {/* Chart Visualization */}
                        <div className="mb-10 h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={data.skill_dimension_scores}
                                    layout="vertical"
                                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal={false} />
                                    <XAxis type="number" domain={[0, 10]} hide />
                                    <YAxis
                                        dataKey="dimension"
                                        type="category"
                                        width={150}
                                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
                                        {data.skill_dimension_scores.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={
                                                entry.score >= 8 ? '#4ade80' :
                                                    entry.score >= 5 ? '#fbbf24' :
                                                        '#f43f5e'
                                            } />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="grid gap-6">
                            {data.skill_dimension_scores.map((item, i) => (
                                <div key={i} className="grid md:grid-cols-12 gap-6 items-center p-6 bg-white/5 rounded-2xl border border-white/5">
                                    <div className="md:col-span-4">
                                        <h4 className="font-bold text-white text-lg">{item.dimension}</h4>
                                    </div>
                                    <div className="md:col-span-2 text-center">
                                        <div className={`text-2xl font-black ${item.score >= 8 ? 'text-emerald-400' : item.score >= 5 ? 'text-amber-400' : 'text-rose-400'
                                            }`}>
                                            {item.score}/10
                                        </div>
                                    </div>
                                    <div className="md:col-span-6">
                                        <p className="text-slate-400 text-sm">{item.interpretation}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* 2️⃣ LEARNING MODE SPECIFIC CONTENT */}
                {!isAssessment && data.key_insights && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="grid md:grid-cols-2 gap-8"
                    >
                        <div className="card-ultra-glass p-10">
                            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                                <Brain className="w-5 h-5 text-purple-400" /> Key Insights
                            </h3>
                            <div className="space-y-6">
                                {data.key_insights.map((insight, i) => (
                                    <div key={i} className="pl-4 border-l-2 border-purple-500/50">
                                        <h4 className="text-purple-300 font-bold mb-1">{insight.pattern}</h4>
                                        <p className="text-slate-400 text-sm">{insight.description}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="card-ultra-glass p-10">
                            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                                <HelpCircle className="w-5 h-5 text-blue-400" /> Reflective Questions
                            </h3>
                            <ul className="space-y-4">
                                {data.reflective_questions?.map((q, i) => (
                                    <li key={i} className="flex gap-3 text-slate-300 italic">
                                        <span className="text-blue-500 font-bold">?</span>
                                        {q}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </motion.section>
                )}

                {/* SHARED SECTIONS (Strengths & Opportunities) */}
                {(data.observed_strengths || data.growth_opportunities) && (
                    <div className="grid lg:grid-cols-2 gap-8">
                        {data.observed_strengths && (
                            <motion.section
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                className="card-ultra-glass p-10"
                            >
                                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" /> Strengths Identified
                                </h3>
                                <div className="space-y-6">
                                    {data.observed_strengths.map((str, i) => (
                                        <div key={i}>
                                            <h4 className="text-emerald-200 font-bold mb-1">{str.title}</h4>
                                            <p className="text-slate-400">{str.observation}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}

                        {data.growth_opportunities && (
                            <motion.section
                                initial={{ opacity: 0, x: 20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                className="card-ultra-glass p-10"
                            >
                                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                                    <TrendingUp className="w-5 h-5 text-amber-400" />
                                    {isAssessment ? "Improvement Areas" : "Growth Opportunities"}
                                </h3>
                                <div className="space-y-6">
                                    {data.growth_opportunities.map((opp, i) => (
                                        <div key={i}>
                                            <h4 className="text-amber-200 font-bold mb-1">{opp.title}</h4>
                                            <p className="text-slate-400 mb-2">{opp.observation}</p>
                                            {opp.suggestion && (
                                                <p className="text-sm text-amber-400/80 bg-amber-950/30 p-3 rounded-lg border border-amber-500/10">
                                                    Try: {opp.suggestion}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )}
                    </div>
                )}


                {/* Assessment Recommendations */}
                {isAssessment && data.manager_recommendations && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10 border-t-4 border-blue-500"
                    >
                        <h3 className="text-2xl font-bold text-white mb-6">Manager Recommendations</h3>
                        <div className="grid md:grid-cols-2 gap-8">
                            <div>
                                <h4 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-2">Immediate Action</h4>
                                <p className="text-xl text-white font-medium">{data.manager_recommendations.immediate_action}</p>
                            </div>
                            <div>
                                <h4 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-2">Next Simulation</h4>
                                <p className="text-xl text-white font-medium">{data.manager_recommendations.next_simulation}</p>
                            </div>
                        </div>
                    </motion.section>
                )}

                {/* Learning Outcome */}
                {!isAssessment && data.learning_outcome && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10 bg-emerald-900/10 border-emerald-500/20"
                    >
                        <h3 className="text-xl font-bold text-emerald-400 mb-4">Learning Outcome</h3>
                        <p className="text-xl text-emerald-100 italic leading-relaxed">
                            "{data.learning_outcome}"
                        </p>
                    </motion.section>
                )}

                {/* Transcript Viewer */}
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
                                    <h3 className="text-xl font-bold text-white">Session Transcript</h3>
                                    <p className="text-sm text-slate-400">View full conversation history</p>
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
            </main>
        </div>
    )
}
