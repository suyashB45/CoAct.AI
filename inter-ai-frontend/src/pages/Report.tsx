"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Download, AlertCircle, Target, History, Zap, Award, BookOpen, Briefcase, MessageSquare, ChevronRight, Check, X, ArrowRight } from "lucide-react"
import { motion, Variants } from "framer-motion"
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'

import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "@/lib/api"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"

// --- TYPES & INTERFACES (UNCHANGED) ---

interface BaseMeta {
    scenario_id: string
    outcome_status: string
    overall_grade: string
    summary: string
    scenario_type?: string
}

interface GenericReportData {
    meta: BaseMeta
    type?: string
    transcript?: { role: "user" | "assistant", content: string }[]
    user_name?: string
    role?: string
    ai_role?: string
    scenario?: string
    detailed_analysis?: string
    dynamic_questions?: string[]
    [key: string]: any // Flexible for scenario fields
}

// Scenario 1: Coaching
interface CoachingReportData extends GenericReportData {
    scorecard: { dimension: string; score: string; description: string; quote?: string; suggestion?: string; alternative_questions?: string[] }[]
    behavioral_signals: {
        manager_tone: string
        staff_defensiveness: string
        staff_openness: string
        emotional_safety: string
    }
    strengths: string[]
    missed_opportunities: string[]
    coaching_impact: {
        self_awareness_gained: string
        ownership_level: string
        change_likelihood: string
    }
    actionable_tips: string[]
}

// Scenario 2: Sales
interface SalesReportData extends GenericReportData {
    scorecard: { dimension: string; score: string; description: string; quote?: string; suggestion?: string; alternative_questions?: string[] }[]
    simulation_analysis: {
        objections_raised: string
        objection_escalation: string
        sentiment_trend: string
    }
    what_worked: string[]
    what_limited_effectiveness: string[]
    revenue_impact: {
        price_risk: string
        missed_upsell: string
        trust_impact: string
    }
    sales_recommendations: string[]
}

// Scenario 3: Learning
interface LearningReportData extends GenericReportData {
    context_summary: { situation: string; challenge_area: string }
    key_insights: string[]
    reflective_questions: string[]
    skill_focus_areas: string[]
    behavioral_shifts: { from: string; to: string }[]
    practice_plan: string[]
    growth_outcome: string
}

// Custom
interface CustomReportData extends GenericReportData {
    interaction_quality: { engagement: string; tone: string; talk_listen_ratio: string }
    core_skills: { skill: string; rating: string; feedback: string }[]
    strengths_observed: string[]
    development_opportunities: string[]
    guidance: { continue: string[]; adjust: string[]; try_next: string[] }
}

const containerVars: Variants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.1 }
    }
}

const itemVars: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 50 } }
}

export default function Report() {
    const params = useParams()
    const navigate = useNavigate()
    const sessionId = params.sessionId as string
    const [data, setData] = useState<GenericReportData | null>(null)
    const [loading, setLoading] = useState(true)
    const [showTranscript, setShowTranscript] = useState(false)

    useEffect(() => {
        const fetchReport = async () => {
            try {
                if (!sessionId) return

                // Get auth token for authenticated request
                const { data: { session } } = await supabase.auth.getSession();
                const headers: Record<string, string> = {
                    'Content-Type': 'application/json'
                };
                if (session?.access_token) {
                    headers['Authorization'] = `Bearer ${session.access_token}`;
                }

                const response = await fetch(getApiUrl(`/api/session/${sessionId}/report_data`), { headers })
                if (!response.ok) throw new Error("Failed to fetch report data")
                const data: GenericReportData = await response.json()
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
            // Get auth token for authenticated request
            const { data: { session } } = await supabase.auth.getSession();
            const headers: Record<string, string> = {};
            if (session?.access_token) {
                headers['Authorization'] = `Bearer ${session.access_token}`;
            }

            const response = await fetch(getApiUrl(`/api/report/${sessionId}`), { headers })
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
                    <div className="w-16 h-16 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin"></div>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Zap className="w-6 h-6 text-blue-400 animate-pulse" />
                    </div>
                </div>
                <p className="text-slate-400 animate-pulse font-medium tracking-wide">GENERATING ANALYSIS...</p>
            </div>
        )
    }

    if (!data || !data.meta) {
        return (
            <div className="min-h-screen bg-slate-950 p-12 flex flex-col items-center justify-center font-sans">
                <AlertCircle className="h-16 w-16 text-amber-500 mb-6" />
                <h2 className="text-3xl font-bold text-white mb-3">Report Unavailable</h2>
                <Button onClick={() => navigate("/")} variant="secondary">Return Home</Button>
            </div>
        )
    }

    // Determine Scenario Type
    const type = (data.type || data.meta.scenario_type || 'custom').toLowerCase()

    // Render Logic
    const renderContent = () => {
        if (type.includes('coaching')) return <CoachingView data={data as CoachingReportData} />
        if (type.includes('sales') || type.includes('negotiation')) return <SalesView data={data as SalesReportData} />
        if (type.includes('learning') || type.includes('reflection')) return <LearningView data={data as LearningReportData} />
        return <CustomView data={data as CustomReportData} />
    }

    const isSuccess = data.meta.outcome_status?.toLowerCase().includes('success') || data.meta.outcome_status?.toLowerCase().includes('completed')

    return (
        <div className="min-h-screen bg-[#0B0F19] text-slate-200 font-sans selection:bg-indigo-500/30">
            <Navigation />

            {/* Background Gradients */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/5 rounded-full blur-[120px]" />
                <div className="absolute top-[20%] right-[-10%] w-[30%] h-[30%] bg-purple-500/5 rounded-full blur-[100px]" />
            </div>

            <main className="relative container mx-auto px-4 sm:px-6 py-24 sm:py-32 space-y-12">

                {/* HEADERS */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row gap-8 justify-between items-start relative"
                >
                    <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-blue-500/20 rounded-full blur-[100px] -z-10 pointer-events-none" />

                    <div className="space-y-6 max-w-3xl">
                        <div className="flex flex-col gap-4">
                            <div>
                                <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] border backdrop-blur-md ${isSuccess ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
                                    {data.meta.outcome_status}
                                </span>
                            </div>
                            <h1 className="text-5xl md:text-7xl font-black text-white tracking-tighter leading-[0.9]">
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-500">
                                    {(data.meta.scenario_id || "REPORT").toUpperCase()}
                                </span>
                            </h1>
                        </div>

                        {/* Character Branding */}
                        <div className="flex items-center gap-5 mt-4 p-4 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-sm w-fit">
                            <div className="h-14 w-14 rounded-full overflow-hidden border-2 border-white/10 ring-4 ring-blue-500/10 shadow-lg">
                                <img
                                    src={data.ai_character === 'sarah'
                                        ? "/sarah.png"
                                        : "/alex.png"
                                    }
                                    alt={data.ai_character || 'Coach'}
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Analysis by</div>
                                <div className="text-xl font-bold text-white tracking-tight">
                                    Coach {data.ai_character ? (data.ai_character.charAt(0).toUpperCase() + data.ai_character.slice(1)) : 'Alex'}
                                </div>
                            </div>
                        </div>

                        <p className="text-slate-300 text-lg leading-relaxed border-l-4 border-blue-500/50 pl-6 max-w-2xl font-medium">
                            {data.meta.summary}
                        </p>
                    </div>

                    <div className="flex flex-col items-end gap-6 min-w-[240px]">
                        {/* User Name Display */}
                        {data.user_name && (
                            <div className="text-right">
                                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Prepared for</div>
                                <div className="text-2xl font-serif text-slate-200 italic border-b border-white/10 pb-1 px-4">{data.user_name}</div>
                            </div>
                        )}

                        {/* Show Grade ONLY if not learning/reflection (regardless of character) */}
                        {type !== 'learning' && type !== 'reflection' && (
                            <div className="text-right relative group">
                                <div className="absolute inset-0 bg-blue-500/20 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                                <div className="text-xs font-bold text-blue-400 uppercase tracking-[0.2em] mb-2 text-right">Overall Score</div>
                                <div className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white via-blue-200 to-blue-500 leading-none tracking-tighter drop-shadow-2xl">
                                    {data.meta.overall_grade}
                                </div>
                            </div>
                        )}
                        <Button onClick={handleDownload} variant="outline" className="gap-2 border-white/10 hover:bg-white/10 hover:text-white transition-all w-full h-12 text-sm uppercase tracking-wider font-bold">
                            <Download className="w-4 h-4" /> Export Assessment
                        </Button>
                    </div>
                </motion.div>

                {/* SCENARIO CONTEXT */}
                {(data.role || data.ai_role || data.scenario) && (
                    <motion.div variants={itemVars} initial="hidden" animate="show">
                        <GlassCard className="border-l-4 border-l-slate-500">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="p-3 rounded-xl bg-slate-500/10 ring-1 ring-white/5">
                                    <MessageSquare className="w-6 h-6 text-slate-400" />
                                </div>
                                <h2 className="text-xl font-bold text-white tracking-wide uppercase">Scenario Context</h2>
                            </div>

                            <div className="grid md:grid-cols-3 gap-6">
                                <div className="space-y-4 md:col-span-1">
                                    <div>
                                        <div className="text-xs text-slate-500 uppercase font-bold mb-1">Your Role</div>
                                        <div className="text-lg text-white font-medium">{data.role}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-slate-500 uppercase font-bold mb-1">Partner Role</div>
                                        <div className="text-lg text-blue-300 font-medium">{data.ai_role}</div>
                                    </div>
                                </div>
                                <div className="md:col-span-2 bg-slate-950/30 p-5 rounded-xl border border-white/5">
                                    <div className="text-xs text-slate-500 uppercase font-bold mb-2">Situation</div>
                                    <p className="text-slate-300 leading-relaxed italic">"{data.scenario}"</p>
                                </div>
                            </div>
                        </GlassCard>
                    </motion.div>
                )}

                {/* DETAILED ANALYSIS */}
                {data.detailed_analysis && (
                    <motion.div variants={itemVars} initial="hidden" animate="show">
                        <GlassCard className="border-l-4 border-l-blue-500">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="p-3 rounded-xl bg-blue-500/10 ring-1 ring-white/5">
                                    <BookOpen className="w-6 h-6 text-blue-400" />
                                </div>
                                <h2 className="text-xl font-bold text-white tracking-wide uppercase">Detailed Analysis</h2>
                            </div>
                            <div className="bg-slate-950/30 p-6 rounded-xl border border-white/5">
                                <p className="text-slate-200 leading-relaxed text-lg whitespace-pre-wrap">{data.detailed_analysis}</p>
                            </div>
                        </GlassCard>
                    </motion.div>
                )}

                {/* DYNAMIC QUESTIONS */}
                {data.dynamic_questions && data.dynamic_questions.length > 0 && (
                    <motion.div variants={itemVars} initial="hidden" animate="show">
                        <GlassCard className="border-l-4 border-l-indigo-500">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="p-3 rounded-xl bg-indigo-500/10 ring-1 ring-white/5">
                                    <MessageSquare className="w-6 h-6 text-indigo-400" />
                                </div>
                                <h2 className="text-xl font-bold text-white tracking-wide uppercase">Deep-Dive Questions</h2>
                            </div>
                            <div className="grid gap-4">
                                {data.dynamic_questions.map((q, i) => (
                                    <div key={i} className="flex gap-4 p-5 bg-slate-950/30 rounded-xl border border-white/5 hover:border-indigo-500/30 transition-colors group">
                                        <div className="h-8 w-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold shrink-0">?</div>
                                        <p className="text-slate-200 text-lg font-medium leading-relaxed italic group-hover:text-white transition-colors">"{q}"</p>
                                    </div>
                                ))}
                            </div>
                        </GlassCard>
                    </motion.div>
                )}

                {/* CONTENT */}
                <motion.div variants={containerVars} initial="hidden" animate="show">
                    {renderContent()}
                </motion.div>

                {/* SCORING METHODOLOGY */}
                {type !== 'learning' && type !== 'reflection' && (
                    <motion.div variants={itemVars} initial="hidden" animate="show">
                        <GlassCard className="bg-slate-900/60">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="h-1 w-6 bg-slate-600 rounded-full"></div>
                                <h2 className="text-xs font-bold text-slate-500 tracking-[0.2em] uppercase">Scoring Methodology</h2>
                            </div>

                            <div className="grid md:grid-cols-2 gap-4">
                                <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10 flex gap-4">
                                    <div className="text-emerald-400 font-bold text-lg whitespace-nowrap">9 - 10</div>
                                    <div>
                                        <div className="text-white font-bold text-sm mb-1">Expert</div>
                                        <p className="text-xs text-slate-400 leading-relaxed">Exceptional application of skills. Creates deep psychological safety and handles conflict with mastery.</p>
                                    </div>
                                </div>
                                <div className="p-4 rounded-xl bg-emerald-900/10 border border-emerald-500/10 flex gap-4">
                                    <div className="text-emerald-300 font-bold text-lg whitespace-nowrap">7 - 8</div>
                                    <div>
                                        <div className="text-white font-bold text-sm mb-1">Proficient</div>
                                        <p className="text-xs text-slate-400 leading-relaxed">Strong performance. Meets objectives effectively with good empathy and strategy.</p>
                                    </div>
                                </div>
                                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 flex gap-4">
                                    <div className="text-amber-400 font-bold text-lg whitespace-nowrap">4 - 6</div>
                                    <div>
                                        <div className="text-white font-bold text-sm mb-1">Competent</div>
                                        <p className="text-xs text-slate-400 leading-relaxed">Functional performance. Achieves basic goals but may be robotic or miss subtle cues.</p>
                                    </div>
                                </div>
                                <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/10 flex gap-4">
                                    <div className="text-rose-400 font-bold text-lg whitespace-nowrap">1 - 3</div>
                                    <div>
                                        <div className="text-white font-bold text-sm mb-1">Needs Ops</div>
                                        <p className="text-xs text-slate-400 leading-relaxed">Struggles with core skills. May be defensive or dismissive. Immediate practice required.</p>
                                    </div>
                                </div>
                            </div>
                        </GlassCard>
                    </motion.div>
                )}

                {/* TRANSCRIPT */}
                {data.transcript && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        className="rounded-3xl bg-slate-900/40 border border-white/5 overflow-hidden backdrop-blur-sm"
                    >
                        <div
                            className="px-8 py-6 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors group"
                            onClick={() => setShowTranscript(!showTranscript)}
                        >
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-indigo-500/10 transition-colors group-hover:bg-indigo-500/20">
                                    <History className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Session Transcript</h3>
                                    <p className="text-sm text-slate-500">Review the full conversation log</p>
                                </div>
                            </div>
                            <ChevronRight className={`w-5 h-5 text-slate-500 transition-transform ${showTranscript ? 'rotate-90' : ''}`} />
                        </div>
                        {showTranscript && (
                            <div className="p-8 max-h-[600px] overflow-y-auto space-y-6 border-t border-white/5 bg-slate-950/30">
                                {data.transcript.map((msg, idx) => (
                                    <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`p-4 rounded-2xl max-w-[80%] text-sm leading-relaxed shadow-lg ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-slate-800 text-slate-200 rounded-bl-none'}`}>
                                            {msg.content}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </motion.div>
                )}
            </main>
        </div>
    )
}

// --- VIEW COMPONENTS & UTILS ---

const ScoreItem = ({ label, score, desc, quote, suggestion, alternative_questions }: any) => {
    const numScore = parseFloat(score?.split('/')[0] || 0)
    const color = numScore >= 8 ? 'emerald' : numScore >= 5 ? 'amber' : 'rose'

    return (
        <div className={`group relative overflow-hidden rounded-2xl bg-slate-900/40 border border-white/5 hover:border-${color}-500/30 transition-all duration-500`}>
            <div className={`absolute top-0 right-0 p-20 rounded-full blur-3xl opacity-0 group-hover:opacity-10 bg-${color}-500 transition-opacity duration-500 pointer-events-none`} />

            <div className="relative z-10 p-6">
                <div className="flex justify-between items-start mb-4">
                    <h4 className="text-xl font-bold text-white tracking-tight">{label}</h4>
                    <div className={`px-3 py-1 rounded-full text-xs font-black bg-${color}-500/10 text-${color}-400 border border-${color}-500/20`}>
                        {score}
                    </div>
                </div>

                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mb-6">
                    <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${numScore * 10}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className={`h-full bg-${color}-500 shadow-[0_0_10px_rgba(var(--${color}-500),0.5)]`}
                    />
                </div>

                <div className="space-y-4">
                    <p className="text-slate-300 leading-relaxed font-medium">{desc}</p>

                    {quote && (
                        <div className="bg-black/20 rounded-xl p-4 border border-white/5">
                            <div className="flex items-center gap-2 mb-2">
                                <MessageSquare className="w-3 h-3 text-slate-500" />
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Evidence</span>
                            </div>
                            <p className="text-sm text-slate-400 italic">"{quote}"</p>
                        </div>
                    )}

                    {(suggestion || (alternative_questions && alternative_questions.length > 0)) && (
                        <div className={`rounded-xl p-4 border border-${color}-500/10 bg-${color}-500/5`}>
                            {suggestion && (
                                <div className="mb-3 last:mb-0">
                                    <div className={`text-xs font-bold text-${color}-400 uppercase tracking-widest mb-1 flex items-center gap-2`}>
                                        <Zap className="w-3 h-3" />
                                        Suggestion
                                    </div>
                                    <p className={`text-sm text-${color}-200/80`}>{suggestion}</p>
                                </div>
                            )}

                            {alternative_questions && alternative_questions.length > 0 && (
                                <div>
                                    <div className={`text-xs font-bold text-${color}-400 uppercase tracking-widest mb-2 flex items-center gap-2`}>
                                        <Target className="w-3 h-3" />
                                        Try Asking
                                    </div>
                                    <div className="space-y-3">
                                        {alternative_questions.map((q: any, i: number) => {
                                            const questionText = typeof q === 'string' ? q : q.question
                                            const rationale = typeof q === 'string' ? null : q.rationale

                                            return (
                                                <div key={i} className={`flex flex-col gap-1 text-sm text-${color}-200/80`}>
                                                    <div className="flex items-start gap-2 italic">
                                                        <ArrowRight className="w-3 h-3 mt-1 flex-shrink-0 opacity-50" />
                                                        <span>"{questionText}"</span>
                                                    </div>
                                                    {rationale && (
                                                        <div className={`text-xs ml-5 px-2 py-1 bg-${color}-500/10 rounded border border-${color}-500/10 text-${color}-100/70`}>
                                                            <span className="font-bold uppercase tracking-wider text-[10px] opacity-70">Reasoning:</span> {rationale}
                                                        </div>
                                                    )}
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

const GlassCard = ({ children, className = "" }: any) => (
    <motion.div
        variants={itemVars}
        className={`bg-slate-900/60 backdrop-blur-xl rounded-3xl border border-white/10 p-8 shadow-2xl relative overflow-hidden ${className}`}
    >
        {children}
    </motion.div>
)

const SectionHeader = ({ icon: Icon, title, colorClass = "text-blue-400", bgClass = "bg-blue-500/10" }: any) => (
    <div className="flex items-center gap-4 mb-6">
        <div className={`p-3 rounded-xl ${bgClass} ring-1 ring-white/5`}>
            <Icon className={`w-6 h-6 ${colorClass}`} />
        </div>
        <h2 className="text-xl font-bold text-white tracking-wide uppercase">{title}</h2>
    </div>
)

const ProgressBar = ({ value, colorClass = "bg-blue-500" }: { value: number, colorClass?: string }) => (
    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
        <motion.div
            initial={{ width: 0 }}
            whileInView={{ width: `${value}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className={`h-full ${colorClass}`}
        />
    </div>
)

const KeyValueRow = ({ label, value, highlight = false }: any) => (
    <div className="flex justify-between items-center py-3 border-b border-white/5 last:border-0 hover:bg-white/5 px-2 rounded-lg transition-colors">
        <span className="text-slate-400 text-sm font-medium uppercase tracking-wide">{label}</span>
        <span className={`font-bold ${highlight ? 'text-white' : 'text-slate-300'}`}>{value}</span>
    </div>
)

// --- CHARTS ---


const SkillsRadarChart = ({ data }: { data: any[] }) => {
    // Process data: extract label and score
    if (!data || data.length === 0) return null;

    // Pass full details to the chart data for the tooltip
    const chartData = data.map(item => ({
        subject: item.dimension,
        A: parseFloat(item.score?.split('/')[0] || 0),
        fullMark: 10,
        quote: item.quote,
        suggestion: item.suggestion,
        desc: item.description
    }));

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-slate-900/95 border border-white/10 p-4 rounded-xl shadow-2xl max-w-xs backdrop-blur-xl">
                    <p className="font-bold text-white text-lg mb-1">{data.subject}</p>
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl font-black text-blue-400">{data.A}</span>
                        <span className="text-slate-500 text-xs uppercase font-bold tracking-wider">/ 10 Score</span>
                    </div>

                    {data.quote && (
                        <div className="mb-3 bg-white/5 p-2 rounded-lg border border-white/5">
                            <div className="flex items-center gap-1 mb-1 opacity-70">
                                <MessageSquare className="w-3 h-3 text-slate-400" />
                                <span className="text-[10px] font-bold text-slate-400 uppercase">Proof</span>
                            </div>
                            <p className="text-xs text-slate-300 italic">"{data.quote}"</p>
                        </div>
                    )}

                    {data.suggestion && (
                        <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/10">
                            <div className="flex items-center gap-1 mb-1">
                                <Zap className="w-3 h-3 text-emerald-400" />
                                <span className="text-[10px] font-bold text-emerald-400 uppercase">Suggestion</span>
                            </div>
                            <p className="text-xs text-emerald-100/80">{data.suggestion}</p>
                        </div>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="h-[300px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Radar
                        name="Skills"
                        dataKey="A"
                        stroke="#3b82f6"
                        strokeWidth={3}
                        fill="#3b82f6"
                        fillOpacity={0.3}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};

// --- SCENARIO 1: COACHING ---
const CoachingView = ({ data }: { data: CoachingReportData }) => (
    <div className="space-y-8">
        <GlassCard className="overflow-hidden">
            <SectionHeader icon={Briefcase} title="Coaching Scorecard" />

            {/* RADICAL VISUALIZATION */}
            <div className="grid lg:grid-cols-2 gap-12 mb-8">
                <div className="flex flex-col justify-center items-center bg-slate-950/20 rounded-2xl p-4 border border-white/5">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-2">Skill Fingerprint</h3>
                    <SkillsRadarChart data={data.scorecard} />
                </div>
                <div className="space-y-6 flex flex-col justify-center">
                    <div className="bg-slate-950/30 p-6 rounded-xl border border-white/5">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">Behavioral Analysis</h3>
                        <KeyValueRow label="Manager Tone" value={data.behavioral_signals?.manager_tone} highlight />
                        <KeyValueRow label="Staff Openness" value={data.behavioral_signals?.staff_openness} />
                        <KeyValueRow label="Psych Safety" value={data.behavioral_signals?.emotional_safety} />
                        <KeyValueRow label="Staff Reaction" value={data.behavioral_signals?.staff_defensiveness} />
                    </div>
                </div>
            </div>

            <div className="space-y-8">
                <div className="space-y-8">
                    {data.scorecard?.map((s, i) => (
                        <ScoreItem
                            key={i}
                            label={s.dimension}
                            score={s.score}
                            desc={s.description}
                            quote={s.quote}
                            suggestion={s.suggestion}
                            alternative_questions={s.alternative_questions}
                        />
                    ))}
                </div>
            </div>
        </GlassCard>

        <div className="grid md:grid-cols-2 gap-6">
            <GlassCard>
                <SectionHeader icon={Award} title="Key Strengths" colorClass="text-emerald-400" bgClass="bg-emerald-500/10" />
                <div className="space-y-4">
                    {data.strengths?.map((s, i) => (
                        <div key={i} className="flex gap-4 p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                            <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                            <span className="text-slate-200">{s}</span>
                        </div>
                    ))}
                </div>
            </GlassCard>
            <GlassCard>
                <SectionHeader icon={AlertCircle} title="Missed Opportunities" colorClass="text-amber-400" bgClass="bg-amber-500/10" />
                <div className="space-y-4">
                    {data.missed_opportunities?.map((s, i) => (
                        <div key={i} className="flex gap-4 p-4 rounded-xl bg-amber-500/5 border border-amber-500/10">
                            <Zap className="w-5 h-5 text-amber-400 flex-shrink-0" />
                            <span className="text-slate-200">{s}</span>
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>

        <GlassCard>
            <SectionHeader icon={Target} title="Impact & Action Plan" colorClass="text-purple-400" bgClass="bg-purple-500/10" />
            <div className="grid lg:grid-cols-3 gap-8">
                <div className="lg:col-span-1 space-y-4 bg-slate-950/30 p-6 rounded-xl">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">Coaching Impact</h3>
                    <div className="space-y-4">
                        <div>
                            <div className="text-xs text-slate-400 uppercase">Self-Awareness Gained</div>
                            <div className="text-lg font-bold text-white">{data.coaching_impact?.self_awareness_gained}</div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 uppercase">Ownership Level</div>
                            <div className="text-lg font-bold text-white">{data.coaching_impact?.ownership_level}</div>
                        </div>
                    </div>
                </div>
                <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-2">Recommended Actions</h3>
                    {data.actionable_tips?.map((tip, i) => (
                        <div key={i} className="flex items-start gap-3 text-slate-300">
                            <ArrowRight className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
                            <span className="leading-relaxed">{tip}</span>
                        </div>
                    ))}
                </div>
            </div>
        </GlassCard>
    </div >
)

// --- SCENARIO 2: SALES ---
const SalesView = ({ data }: { data: SalesReportData }) => (
    <div className="space-y-8">
        <GlassCard>
            <SectionHeader icon={Target} title="Sales Performance" colorClass="text-emerald-400" bgClass="bg-emerald-500/10" />
            <div className="grid lg:grid-cols-2 gap-12">
                <div className="flex flex-col justify-center items-center bg-slate-950/20 rounded-2xl p-4 border border-white/5 mb-8 lg:mb-0">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-2">Performance Radar</h3>
                    <SkillsRadarChart data={data.scorecard} />
                </div>
                <div className="space-y-8">
                    {data.scorecard?.map((s, i) => (
                        <ScoreItem
                            key={i}
                            label={s.dimension}
                            score={s.score}
                            desc={s.description}
                            quote={s.quote}
                            suggestion={s.suggestion}
                            alternative_questions={s.alternative_questions}
                        />
                    ))}
                </div>
            </div>
            <div className="space-y-6 mt-8">
                <div className="bg-slate-950/30 p-6 rounded-xl border border-white/5 space-y-4">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest">Simulation Stats</h3>
                    <KeyValueRow label="Objections" value={data.simulation_analysis?.objections_raised} />
                    <KeyValueRow label="Escalation" value={data.simulation_analysis?.objection_escalation} />
                    <KeyValueRow label="User Sentiment" value={data.simulation_analysis?.sentiment_trend} highlight />
                </div>
                <div className="bg-rose-500/5 p-6 rounded-xl border border-rose-500/10">
                    <h4 className="text-xs font-bold text-rose-400 uppercase mb-2">Revenue Risk Factpr</h4>
                    <p className="text-slate-200 font-medium">{data.revenue_impact?.price_risk}</p>
                </div>
            </div>
        </GlassCard>

        <div className="grid md:grid-cols-2 gap-6">
            <GlassCard>
                <SectionHeader icon={Award} title="Effective Tactics" colorClass="text-blue-400" bgClass="bg-blue-500/10" />
                <div className="space-y-2">
                    {data.what_worked?.map((w, i) => (
                        <div key={i} className="flex gap-3 text-slate-300 py-2 border-b border-white/5 last:border-0">
                            <Check className="w-4 h-4 text-blue-400 mt-1" />
                            {w}
                        </div>
                    ))}
                </div>
            </GlassCard>
            <GlassCard>
                <SectionHeader icon={AlertCircle} title="Performance Gaps" colorClass="text-rose-400" bgClass="bg-rose-500/10" />
                <div className="space-y-2">
                    {data.what_limited_effectiveness?.map((w, i) => (
                        <div key={i} className="flex gap-3 text-slate-300 py-2 border-b border-white/5 last:border-0">
                            <X className="w-4 h-4 text-rose-400 mt-1" />
                            {w}
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>

        <GlassCard className="border-t-4 border-t-emerald-500">
            <h2 className="text-lg font-bold text-white mb-6">STRATEGIC RECOMMENDATIONS</h2>
            <div className="grid md:grid-cols-2 gap-6">
                {data.sales_recommendations?.map((rec, i) => (
                    <div key={i} className="bg-slate-800/50 p-5 rounded-xl border border-white/5 text-slate-300 text-sm leading-relaxed hover:bg-slate-800 transition-colors">
                        {rec}
                    </div>
                ))}
            </div>
        </GlassCard>
    </div>
)

// --- SCENARIO 3: LEARNING ---
const LearningView = ({ data }: { data: LearningReportData }) => (
    <div className="space-y-8">
        <div className="grid lg:grid-cols-3 gap-6">
            <GlassCard className="col-span-1 bg-gradient-to-b from-blue-900/20 to-slate-900/40">
                <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-4">Learning Context</h3>
                <p className="text-lg text-white font-medium mb-4 leading-relaxed">"{data.context_summary?.situation}"</p>
                <div className="inline-block bg-blue-500/20 text-blue-300 px-3 py-1 rounded text-xs font-bold uppercase tracking-wide">
                    {data.context_summary?.challenge_area}
                </div>
            </GlassCard>
            <GlassCard className="col-span-2">
                <SectionHeader icon={BookOpen} title="Key Insights" colorClass="text-purple-400" bgClass="bg-purple-500/10" />
                <div className="space-y-4">
                    {data.key_insights?.map((insight, i) => (
                        <div key={i} className="flex gap-4 p-4 rounded-xl bg-purple-500/5 border border-purple-500/10">
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-2 flex-shrink-0" />
                            <p className="text-slate-200 leading-relaxed">{insight}</p>
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
            <GlassCard>
                <SectionHeader icon={MessageSquare} title="Reflective Questions" colorClass="text-indigo-400" bgClass="bg-indigo-500/10" />
                <ul className="space-y-6">
                    {data.reflective_questions?.map((q, i) => (
                        <li key={i} className="text-indigo-200 italic text-lg opacity-90 pl-4 border-l-2 border-indigo-500/30">
                            "{q}"
                        </li>
                    ))}
                </ul>
            </GlassCard>
            <GlassCard>
                <SectionHeader icon={History} title="Behavioral Shifts" colorClass="text-emerald-400" bgClass="bg-emerald-500/10" />
                <div className="space-y-4">
                    {data.behavioral_shifts?.map((shift, i) => (
                        <div key={i} className="flex items-center justify-between gap-4 p-4 bg-slate-950/30 rounded-xl border border-white/5">
                            <span className="text-rose-400/80 line-through text-sm">{shift.from}</span>
                            <ArrowRight className="w-4 h-4 text-slate-600" />
                            <span className="text-emerald-400 font-bold">{shift.to}</span>
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>

        <GlassCard className="border-t-4 border-t-amber-500">
            <SectionHeader icon={Zap} title="Practice Plan" colorClass="text-amber-400" bgClass="bg-amber-500/10" />
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {data.practice_plan?.map((plan, i) => (
                    <div key={i} className="p-5 bg-slate-800/40 rounded-xl border border-white/5 hover:border-amber-500/30 transition-colors">
                        <div className="text-xs font-bold text-amber-500 mb-2">EXERCISE 0{i + 1}</div>
                        <p className="text-slate-300 text-sm">{plan}</p>
                    </div>
                ))}
            </div>
            <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-8 rounded-2xl text-center border border-white/5">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Growth Vision</h3>
                <p className="text-2xl text-white font-serif italic max-w-2xl mx-auto leading-relaxed">{data.growth_outcome}</p>
            </div>
        </GlassCard>
    </div>
)

// --- CUSTOM SCENARIO ---
const CustomView = ({ data }: { data: CustomReportData }) => (
    <div className="space-y-8">
        <div className="grid md:grid-cols-2 gap-6">
            <GlassCard>
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">Interaction Quality</h3>
                <div className="space-y-4">
                    <KeyValueRow label="Tone" value={data.interaction_quality?.tone} highlight />
                    <KeyValueRow label="Engagement" value={data.interaction_quality?.engagement} />
                    <KeyValueRow label="Balance" value={data.interaction_quality?.talk_listen_ratio} />
                </div>
            </GlassCard>
            <GlassCard>
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">Core Skills</h3>
                <div className="space-y-6">
                    {data.core_skills?.map((s, i) => (
                        <div key={i}>
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-white font-bold">{s.skill}</span>
                                <span className="text-blue-400 font-mono">{s.rating}</span>
                            </div>
                            <ProgressBar value={s.rating === 'High' ? 90 : s.rating === 'Medium' ? 60 : 30} />
                            <p className="text-xs text-slate-500 mt-2">{s.feedback}</p>
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>

        <GlassCard>
            <SectionHeader icon={Target} title="Adaptive Guidance" colorClass="text-purple-400" bgClass="bg-purple-500/10" />
            <div className="grid md:grid-cols-3 gap-8">
                <div className="space-y-4">
                    <h4 className="font-bold text-emerald-400 flex items-center gap-2"><Check className="w-4 h-4" /> Continue</h4>
                    <ul className="space-y-2">
                        {data.guidance?.continue?.map((item, i) => <li key={i} className="text-sm text-slate-300 bg-emerald-500/5 p-3 rounded-lg border border-emerald-500/10">{item}</li>)}
                    </ul>
                </div>
                <div className="space-y-4">
                    <h4 className="font-bold text-amber-400 flex items-center gap-2"><AlertCircle className="w-4 h-4" /> Adjust</h4>
                    <ul className="space-y-2">
                        {data.guidance?.adjust?.map((item, i) => <li key={i} className="text-sm text-slate-300 bg-amber-500/5 p-3 rounded-lg border border-amber-500/10">{item}</li>)}
                    </ul>
                </div>
                <div className="space-y-4">
                    <h4 className="font-bold text-blue-400 flex items-center gap-2"><ArrowRight className="w-4 h-4" /> Try Next</h4>
                    <ul className="space-y-2">
                        {data.guidance?.try_next?.map((item, i) => <li key={i} className="text-sm text-slate-300 bg-blue-500/5 p-3 rounded-lg border border-blue-500/10">{item}</li>)}
                    </ul>
                </div>
            </div>
        </GlassCard>
    </div>
)
