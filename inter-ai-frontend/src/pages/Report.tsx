"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Loader2, Download, AlertCircle, TrendingUp, Target, User, Bot, History, CheckCircle, Zap, MessageCircle } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "@/lib/api"

// --- INTERFACES FOR UNIFIED REPORT STRUCTURE (Matching PDF) ---

interface TranscriptMessage {
    role: "user" | "assistant"
    content: string
    audio_url?: string | null
}

interface SkillScore {
    dimension: string
    score?: number
    level?: string
    interpretation: string
    evidence?: string
    improvement_tip?: string
}

interface TacticalObservation {
    moment: string
    analysis: string
    impact?: string
    replication?: string
    alternative?: string
    prevention?: string
}

interface ExecutiveSummary {
    performance_overview: string
    key_strengths: string[]
    areas_for_growth: string[]
    recommended_next_steps: string
}

interface PersonalizedRecommendations {
    immediate_actions: string[]
    focus_areas: string[]
    reflection_prompts: string[]
    practice_suggestions: { action: string, frequency: string, success_indicator?: string }[]
}

interface ConversationAnalytics {
    total_exchanges?: number
    user_talk_time_percentage?: number
    question_to_statement_ratio?: string
    emotional_tone_progression?: string
    framework_adherence?: string
}

interface ReportData {
    meta: {
        summary: string
        emotional_trajectory?: string
        session_quality?: string
        key_themes?: string[]
        scenario_type?: string
    }
    scenario_type?: "coaching" | "negotiation" | "reflection" | "custom"
    mode?: string

    // Unified structure (matching PDF)
    executive_summary?: ExecutiveSummary
    conversation_analytics?: ConversationAnalytics
    skill_analysis?: SkillScore[]
    skill_dimension_scores?: SkillScore[]
    tactical_observations?: {
        success?: TacticalObservation
        risk?: TacticalObservation
    }
    observed_strengths?: { title: string, observation: string, business_impact?: string }[]
    growth_opportunities?: { title: string, observation: string, suggestion?: string, practice_method?: string }[]
    personalized_recommendations?: PersonalizedRecommendations
    learning_outcome?: string

    // Legacy fields
    readiness_indicator?: { label: string, score: number, next_level_requirements?: string, estimated_timeline?: string }
    manager_recommendations?: { immediate_action?: string, next_simulation?: string, development_focus?: string }
    personalized_learning_path?: { skill: string, priority: string, timeline: string }[]

    transcript?: TranscriptMessage[]
    scenario?: string
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
                <p className="text-slate-400 mb-8 text-center max-w-md text-lg">We couldn't load the analysis data.</p>
                <button onClick={() => navigate("/")} className="btn-ultra-modern px-8 py-3">Go Home</button>
            </div>
        )
    }

    // Determine scenario type and styling
    const scenarioType = data.scenario_type || data.meta?.scenario_type || 'custom'
    const skills = data.skill_analysis || data.skill_dimension_scores || []
    const hasScores = skills.some(s => s.score !== undefined)

    const scenarioConfig: Record<string, { label: string, color: string, borderColor: string, bgColor: string, textColor: string, icon: any }> = {
        'coaching': { label: 'COACHING & PERFORMANCE', color: 'text-blue-400', borderColor: 'border-l-blue-500', bgColor: 'bg-blue-500/10', textColor: 'text-blue-300', icon: User },
        'negotiation': { label: 'SALES & NEGOTIATION', color: 'text-emerald-400', borderColor: 'border-l-emerald-500', bgColor: 'bg-emerald-500/10', textColor: 'text-emerald-300', icon: TrendingUp },
        'reflection': { label: 'LEARNING REFLECTION', color: 'text-purple-400', borderColor: 'border-l-purple-500', bgColor: 'bg-purple-500/10', textColor: 'text-purple-300', icon: Bot },
        'custom': { label: 'CORPORATE SCENARIO', color: 'text-amber-400', borderColor: 'border-l-amber-500', bgColor: 'bg-amber-500/10', textColor: 'text-amber-300', icon: Zap },
        'leadership': { label: 'LEADERSHIP & STRATEGY', color: 'text-indigo-400', borderColor: 'border-l-indigo-500', bgColor: 'bg-indigo-500/10', textColor: 'text-indigo-300', icon: Target },
        'customer_service': { label: 'CUSTOMER SERVICE', color: 'text-red-400', borderColor: 'border-l-red-500', bgColor: 'bg-red-500/10', textColor: 'text-red-300', icon: MessageCircle }
    }

    const config = scenarioConfig[scenarioType] || scenarioConfig['custom']

    const SCENARIO_TITLES: Record<string, any> = {
        'coaching': {
            exec_summary: "PERFORMANCE IN BRIEF",
            skills: "COACHING COMPETENCIES",
            tactical: "COACHING MOMENTS",
            strengths: "EFFECTIVE BEHAVIORS",
            growth: "DEVELOPMENT OPPORTUNITIES",
            recs: "DEVELOPMENT PLAN",
            analytics: "CONVERSATION METRICS"
        },
        'negotiation': {
            exec_summary: "DEAL OVERVIEW",
            skills: "NEGOTIATION SKILLS",
            tactical: "TACTICAL MOVES & COUNTERS",
            strengths: "WINNING TACTICS",
            growth: "MISSED OPPORTUNITIES",
            recs: "STRATEGIC ADJUSTMENTS",
            analytics: "NEGOTIATION DYNAMICS"
        },
        'reflection': {
            exec_summary: "REFLECTION SUMMARY",
            skills: "LEARNING ANALYSIS",
            tactical: "KEY INSIGHTS",
            strengths: "SELF-AWARENESS HIGHLIGHTS",
            growth: "AREAS FOR DEEPER REFLECTION",
            recs: "JOURNALING & PRACTICE",
            analytics: "INTERACTION FLOW"
        },
        'custom': {
            exec_summary: "EXECUTIVE BRIEF",
            skills: "COMPETENCY MATRIX",
            tactical: "KEY STAKEHOLDER INTERACTIONS",
            strengths: "STRATEGIC ASSETS",
            growth: "PERFORMANCE GAPS",
            recs: "EXECUTIVE ACTION PLAN",
            analytics: "ENGAGEMENT METRICS"
        },
        'leadership': {
            exec_summary: "LEADERSHIP IMPACT BRIEF",
            skills: "LEADERSHIP COMPETENCIES",
            tactical: "STRATEGIC MOMENTS",
            strengths: "VISIONARY TRAITS",
            growth: "INFLUENCE GAPS",
            recs: "LEADERSHIP DEVELOPMENT PLAN",
            analytics: "PRESENCE METRICS"
        },
        'customer_service': {
            exec_summary: "SERVICE RESOLUTION REPORT",
            skills: "CLIENT RELATIONS SKILLS",
            tactical: "SERVICE RECOVERY MOMENTS",
            strengths: "EMPATHY & PATIENCE",
            growth: "RESOLUTION GAPS",
            recs: "SERVICE EXCELLENCE PLAN",
            analytics: "CUSTOMER SENTIMENT"
        }
    }

    const titles = SCENARIO_TITLES[scenarioType] || SCENARIO_TITLES['custom']

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-purple-500/30">
            <Navigation />

            {/* Background */}
            <div className="fixed inset-0 pointer-events-none -z-10">
                <div className={`absolute top-[-20%] left-1/4 w-[600px] h-[600px] rounded-full blur-[120px] ${config.bgColor}`} />
            </div>

            <main className="container mx-auto px-4 sm:px-6 py-24 sm:py-32 space-y-6">

                {/* Header with Download */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold text-white">Skill Development Report</h1>
                        <p className="text-slate-400 text-sm mt-1">Session Analysis & Recommendations</p>
                    </div>
                    <button onClick={handleDownload} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl font-semibold transition-colors border border-white/10">
                        <Download className="w-4 h-4" /> Export PDF
                    </button>
                </div>

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 1: BANNER (Matching PDF draw_banner)
                    - Scenario type badge
                    - Summary text
                    - Emotional arc, Session quality, Key themes
                ══════════════════════════════════════════════════════════════════ */}
                <motion.section
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`rounded-2xl bg-slate-900/80 border border-white/10 p-5 sm:p-6 border-l-4 ${config.borderColor}`}
                >
                    {/* Scenario Type Badge */}
                    <div className={`inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider ${config.color} mb-3`}>
                        <config.icon className="h-4 w-4" />
                        {config.label}
                    </div>

                    {/* Summary */}
                    <p className="text-base sm:text-lg text-slate-300 leading-relaxed mb-4">{data.meta.summary}</p>

                    {/* Meta Info Row */}
                    <div className="space-y-2 text-sm">
                        {data.meta.emotional_trajectory && (
                            <div className="flex items-start gap-2">
                                <span className="text-indigo-400 font-bold">›</span>
                                <span className="text-slate-500 uppercase text-xs font-bold shrink-0">EMOTIONAL ARC:</span>
                                <span className="text-slate-300">{data.meta.emotional_trajectory}</span>
                            </div>
                        )}
                        {data.meta.session_quality && (
                            <div className="flex items-start gap-2">
                                <span className="text-emerald-400 font-bold">›</span>
                                <span className="text-slate-500 uppercase text-xs font-bold shrink-0">SESSION QUALITY:</span>
                                <span className="text-slate-300">{data.meta.session_quality}</span>
                            </div>
                        )}
                        {data.meta.key_themes && data.meta.key_themes.length > 0 && (
                            <div className="flex items-start gap-2">
                                <span className="text-pink-400 font-bold">›</span>
                                <span className="text-slate-500 uppercase text-xs font-bold shrink-0">KEY THEMES:</span>
                                <span className="text-slate-400 italic">{data.meta.key_themes.join(' | ')}</span>
                            </div>
                        )}
                    </div>
                </motion.section>

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 2: EXECUTIVE SUMMARY (Matching PDF draw_executive_summary)
                    - Performance overview
                    - Two-column: Key Strengths | Areas for Growth
                    - Recommended next steps
                ══════════════════════════════════════════════════════════════════ */}
                {data.executive_summary && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.05 }}
                        className="rounded-2xl bg-slate-900/80 border border-white/10 overflow-hidden"
                    >
                        {/* Header Bar */}
                        <div className="bg-slate-800 px-5 py-3">
                            <h2 className="text-white font-bold text-sm uppercase tracking-wider">{titles.exec_summary}</h2>
                        </div>

                        <div className="p-5 sm:p-6">
                            {/* Performance Overview */}
                            <p className="text-slate-300 leading-relaxed mb-5">{data.executive_summary.performance_overview}</p>

                            {/* Two Column Grid */}
                            <div className="grid md:grid-cols-2 gap-4 mb-4">
                                {/* Key Strengths (Green background like PDF) */}
                                <div className="bg-emerald-950/30 border border-emerald-900/50 rounded-xl p-4">
                                    <h3 className="text-emerald-400 font-bold text-xs uppercase tracking-wider mb-3">KEY STRENGTHS</h3>
                                    <ul className="space-y-2">
                                        {data.executive_summary.key_strengths?.map((strength, i) => (
                                            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                                <span className="text-emerald-400 mt-0.5">+</span>
                                                {strength}
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Areas for Growth (Yellow/Amber background like PDF) */}
                                <div className="bg-amber-950/30 border border-amber-900/50 rounded-xl p-4">
                                    <h3 className="text-amber-400 font-bold text-xs uppercase tracking-wider mb-3">AREAS FOR GROWTH</h3>
                                    <ul className="space-y-2">
                                        {data.executive_summary.areas_for_growth?.map((area, i) => (
                                            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                                <span className="text-amber-400 mt-0.5">-</span>
                                                {area}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            {/* Recommended Next Steps */}
                            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-blue-400 font-bold text-xs uppercase tracking-wider">NEXT STEPS:</span>
                                </div>
                                <p className="text-slate-300 text-sm">{data.executive_summary.recommended_next_steps}</p>
                            </div>
                        </div>
                    </motion.section>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 3: CONVERSATION ANALYTICS (Matching PDF draw_conversation_analytics)
                    - Total Exchanges, Talk Time Balance, Q/S Ratio, Emotional Progression
                ══════════════════════════════════════════════════════════════════ */}
                {data.conversation_analytics && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="rounded-2xl bg-slate-900/80 border border-white/10 overflow-hidden"
                    >
                        <div className="bg-slate-800 px-5 py-3 flex items-center gap-2">
                            <MessageCircle className="w-4 h-4 text-cyan-400" />
                            <h2 className="text-white font-bold text-sm uppercase tracking-wider">{titles.analytics}</h2>
                        </div>

                        <div className="p-5 sm:p-6">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {data.conversation_analytics.total_exchanges !== undefined && (
                                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                                        <div className="text-2xl font-bold text-cyan-400">{data.conversation_analytics.total_exchanges}</div>
                                        <div className="text-xs text-slate-500 uppercase mt-1">Total Exchanges</div>
                                    </div>
                                )}
                                {data.conversation_analytics.user_talk_time_percentage !== undefined && (
                                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                                        <div className="text-2xl font-bold text-purple-400">{data.conversation_analytics.user_talk_time_percentage}%</div>
                                        <div className="text-xs text-slate-500 uppercase mt-1">Your Talk Time</div>
                                    </div>
                                )}
                                {data.conversation_analytics.question_to_statement_ratio && (
                                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                                        <div className="text-2xl font-bold text-amber-400">{data.conversation_analytics.question_to_statement_ratio}</div>
                                        <div className="text-xs text-slate-500 uppercase mt-1">Q/S Ratio</div>
                                    </div>
                                )}
                                {data.conversation_analytics.emotional_tone_progression && (
                                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                                        <div className="text-lg font-bold text-emerald-400 truncate">{data.conversation_analytics.emotional_tone_progression}</div>
                                        <div className="text-xs text-slate-500 uppercase mt-1">Emotional Progress</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.section>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 4: SKILL DIMENSION ANALYSIS (Matching PDF draw_assessment_table + draw_score_chart)
                    - Bar chart visualization
                    - Table with Dimension, Score, Interpretation, Improvement Tip
                ══════════════════════════════════════════════════════════════════ */}
                {skills.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-2xl bg-slate-900/80 border border-white/10 overflow-hidden"
                    >
                        <div className="bg-slate-800 px-5 py-3 flex items-center gap-2">
                            <Target className="w-4 h-4 text-rose-400" />
                            <h2 className="text-white font-bold text-sm uppercase tracking-wider">{titles.skills}</h2>
                        </div>

                        <div className="p-5 sm:p-6">
                            {/* Chart Visualization (if scores exist) */}
                            {hasScores && (
                                <div className="mb-6 h-48 sm:h-56 w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={skills}
                                            layout="vertical"
                                            margin={{ top: 10, right: 40, left: 10, bottom: 10 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" horizontal={false} />
                                            <XAxis type="number" domain={[0, 10]} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                                            <YAxis
                                                dataKey="dimension"
                                                type="category"
                                                width={100}
                                                tick={{ fill: '#94a3b8', fontSize: 10 }}
                                                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                                                tickLine={false}
                                            />
                                            <Tooltip
                                                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                                                contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                                itemStyle={{ color: '#fff' }}
                                                formatter={(value: any) => [`${value}/10`, 'Score']}
                                            />
                                            <ReferenceLine x={7} stroke="rgba(100, 116, 139, 0.5)" strokeDasharray="3 3" label={{ value: 'Target: 7', fill: '#64748b', fontSize: 10, position: 'top' }} />
                                            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={14}>
                                                {skills.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={
                                                        (entry.score || 0) >= 8 ? '#4ade80' :
                                                            (entry.score || 0) >= 6 ? '#fbbf24' :
                                                                '#f43f5e'
                                                    } />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {/* Table/Cards - matches PDF table structure */}
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="bg-slate-800/50 text-left">
                                            <th className="px-4 py-3 font-bold text-slate-300 text-xs uppercase">Dimension</th>
                                            {hasScores && <th className="px-4 py-3 font-bold text-slate-300 text-xs uppercase text-center">Score</th>}
                                            <th className="px-4 py-3 font-bold text-slate-300 text-xs uppercase">Interpretation</th>
                                            <th className="px-4 py-3 font-bold text-slate-300 text-xs uppercase">Improvement Tip</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {skills.map((skill, i) => (
                                            <tr key={i} className="border-t border-white/5">
                                                <td className="px-4 py-3 font-semibold text-white">{skill.dimension}</td>
                                                {hasScores && (
                                                    <td className="px-4 py-3 text-center">
                                                        <span className={`font-bold ${(skill.score || 0) >= 8 ? 'text-emerald-400' :
                                                            (skill.score || 0) >= 6 ? 'text-amber-400' : 'text-rose-400'
                                                            }`}>
                                                            {skill.score}/10
                                                        </span>
                                                    </td>
                                                )}
                                                <td className="px-4 py-3 text-slate-400 text-xs">{skill.interpretation}</td>
                                                <td className="px-4 py-3 text-blue-400 text-xs">{skill.improvement_tip}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </motion.section>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 5: TACTICAL OBSERVATIONS (Matching PDF draw_tactical_observations)
                    - Success Moment (green) | Improvement Area (red) side by side
                ══════════════════════════════════════════════════════════════════ */}
                {data.tactical_observations && (data.tactical_observations.success || data.tactical_observations.risk) && (
                    <div className="space-y-4">
                        {/* Section Header */}
                        <div className="flex items-center gap-2 mb-2">
                            <div className="h-4 w-1 bg-indigo-500 rounded-full" />
                            <h2 className="text-indigo-400 font-bold text-sm uppercase tracking-wider">{titles.tactical}</h2>
                        </div>
                        <motion.section
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            className="grid md:grid-cols-2 gap-4"
                        >
                            {/* Success Moment */}
                            {data.tactical_observations.success && (
                                <div className="rounded-2xl bg-emerald-950/30 border border-emerald-900/50 p-5">
                                    <h3 className="text-emerald-400 font-bold text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <Zap className="w-4 h-4" /> SUCCESS MOMENT
                                    </h3>
                                    <blockquote className="text-slate-300 italic border-l-2 border-emerald-500 pl-3 mb-3 text-sm">
                                        "{data.tactical_observations.success.moment}"
                                    </blockquote>
                                    {data.tactical_observations.success.impact && (
                                        <p className="text-xs text-slate-500 mb-1">
                                            <span className="text-slate-400">Impact:</span> {data.tactical_observations.success.impact}
                                        </p>
                                    )}
                                    {data.tactical_observations.success.replication && (
                                        <p className="text-xs text-slate-500">
                                            <span className="text-slate-400">Replicate by:</span> {data.tactical_observations.success.replication}
                                        </p>
                                    )}
                                </div>
                            )}

                            {/* Risk/Improvement Moment */}
                            {data.tactical_observations.risk && (
                                <div className="rounded-2xl bg-rose-950/30 border border-rose-900/50 p-5">
                                    <h3 className="text-rose-400 font-bold text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4" /> IMPROVEMENT AREA
                                    </h3>
                                    <blockquote className="text-slate-300 italic border-l-2 border-rose-500 pl-3 mb-3 text-sm">
                                        "{data.tactical_observations.risk.moment}"
                                    </blockquote>
                                    {data.tactical_observations.risk.alternative && (
                                        <p className="text-xs text-slate-500 mb-1">
                                            <span className="text-slate-400">Try instead:</span> {data.tactical_observations.risk.alternative}
                                        </p>
                                    )}
                                    {data.tactical_observations.risk.prevention && (
                                        <p className="text-xs text-slate-500">
                                            <span className="text-slate-400">Prevent by:</span> {data.tactical_observations.risk.prevention}
                                        </p>
                                    )}
                                </div>
                            )}
                        </motion.section>
                    </div>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 6: STRENGTHS IDENTIFIED (Matching PDF draw_observed_strengths)
                ══════════════════════════════════════════════════════════════════ */}
                {data.observed_strengths && data.observed_strengths.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-2xl bg-slate-900/80 border border-white/10 overflow-hidden"
                    >
                        <div className="bg-emerald-900/30 px-5 py-3 flex items-center gap-2 border-b border-emerald-800/30">
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                            <h2 className="text-emerald-400 font-bold text-sm uppercase tracking-wider">{titles.strengths}</h2>
                        </div>

                        <div className="p-5 space-y-4">
                            {data.observed_strengths.map((str, i) => (
                                <div key={i}>
                                    <h4 className="text-emerald-300 font-semibold mb-1 flex items-center gap-2">
                                        <span className="text-emerald-400">›</span> {str.title}
                                    </h4>
                                    <p className="text-sm text-slate-400 ml-4">{str.observation}</p>
                                    {str.business_impact && (
                                        <p className="text-xs text-slate-500 ml-4 mt-1 italic">Business Impact: {str.business_impact}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 7: IMPROVEMENT AREAS (Matching PDF draw_coaching_opportunities)
                ══════════════════════════════════════════════════════════════════ */}
                {data.growth_opportunities && data.growth_opportunities.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-2xl bg-slate-900/80 border border-white/10 overflow-hidden"
                    >
                        <div className="bg-amber-900/30 px-5 py-3 flex items-center gap-2 border-b border-amber-800/30">
                            <TrendingUp className="w-4 h-4 text-amber-400" />
                            <h2 className="text-amber-400 font-bold text-sm uppercase tracking-wider">{titles.growth}</h2>
                        </div>

                        <div className="p-5 space-y-4">
                            {data.growth_opportunities.map((opp, i) => (
                                <div key={i}>
                                    <h4 className="text-amber-300 font-semibold mb-1 flex items-center gap-2">
                                        <span className="text-amber-400">→</span> {opp.title}
                                    </h4>
                                    <p className="text-sm text-slate-400 ml-4">{opp.observation}</p>
                                    {opp.suggestion && (
                                        <p className="text-xs text-amber-400/80 ml-4 mt-2 bg-amber-950/30 p-2 rounded">
                                            💡 {opp.suggestion}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 8: PERSONALIZED RECOMMENDATIONS (Matching PDF draw_personalized_recommendations)
                    - Dark background block with Immediate Actions, Focus Areas, Reflection Prompts
                ══════════════════════════════════════════════════════════════════ */}
                {data.personalized_recommendations && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-2xl bg-slate-800 border border-white/10 p-5 sm:p-6"
                    >
                        <h2 className="text-white font-bold text-sm uppercase tracking-wider mb-5">{titles.recs}</h2>

                        <div className="space-y-4">
                            {/* Immediate Actions */}
                            {data.personalized_recommendations.immediate_actions?.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    <span className="text-blue-300 font-bold text-xs uppercase shrink-0">IMMEDIATE ACTIONS:</span>
                                    <span className="text-white text-sm">{data.personalized_recommendations.immediate_actions.join(', ')}</span>
                                </div>
                            )}

                            {/* Focus Areas */}
                            {data.personalized_recommendations.focus_areas?.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    <span className="text-blue-300 font-bold text-xs uppercase shrink-0">FOCUS AREAS:</span>
                                    <span className="text-white text-sm">{data.personalized_recommendations.focus_areas.join(', ')}</span>
                                </div>
                            )}

                            {/* Reflection Prompts */}
                            {data.personalized_recommendations.reflection_prompts?.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-white/10">
                                    <div className="space-y-2">
                                        {data.personalized_recommendations.reflection_prompts.slice(0, 2).map((prompt, i) => (
                                            <p key={i} className="text-slate-400 text-sm italic">
                                                <span className="text-slate-500 not-italic mr-1">?</span> {prompt}
                                            </p>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.section>
                )}

                {/* ══════════════════════════════════════════════════════════════════
                    SECTION 9: LEARNING OUTCOME (Matching PDF draw_learning_outcome)
                ══════════════════════════════════════════════════════════════════ */}
                {data.learning_outcome && (
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="rounded-2xl bg-emerald-950/30 border border-emerald-900/50 p-5"
                    >
                        <h3 className="text-emerald-400 font-bold text-xs uppercase tracking-wider mb-3">Learning Outcome</h3>
                        <p className="text-emerald-100 italic text-lg leading-relaxed">"{data.learning_outcome}"</p>
                    </motion.section>
                )}

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
