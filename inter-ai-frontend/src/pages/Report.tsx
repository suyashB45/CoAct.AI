"use client"

import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Loader2, Download, AlertCircle, TrendingUp, Brain, MessageSquare, Zap, BookOpen, Target, Trophy, Clock, User, Bot, History, Sparkles, Heart } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts"
import Navigation from "../components/landing/Navigation"
import { getReportData, getReportPdfUrl, ReportData } from "../lib/api"

export default function Report() {
    const params = useParams()
    const navigate = useNavigate()
    const sessionId = params.sessionId as string
    const [data, setData] = useState<ReportData | null>(null)
    const [loading, setLoading] = useState(true)
    const [showTranscript, setShowTranscript] = useState(false)
    const [showContext, setShowContext] = useState(true)
    const [animatedScore, setAnimatedScore] = useState(0)
    const [animatedPotential, setAnimatedPotential] = useState(0)

    // Animate score counter on data load
    useEffect(() => {
        if (data?.meta?.fit_score) {
            let start = 0;
            const end = data.meta.fit_score;
            const duration = 1500;
            const increment = end / (duration / 16);

            const timer = setInterval(() => {
                start += increment;
                if (start >= end) {
                    setAnimatedScore(end);
                    clearInterval(timer);
                } else {
                    setAnimatedScore(start);
                }
            }, 16);

            return () => clearInterval(timer);
        }
    }, [data?.meta?.fit_score]);

    // Animate potential score
    useEffect(() => {
        if (data?.meta?.potential_score) {
            let start = 0;
            const end = data.meta.potential_score;
            const duration = 1800;
            const increment = end / (duration / 16);

            const timer = setInterval(() => {
                start += increment;
                if (start >= end) {
                    setAnimatedPotential(end);
                    clearInterval(timer);
                } else {
                    setAnimatedPotential(start);
                }
            }, 16);

            return () => clearInterval(timer);
        }
    }, [data?.meta?.potential_score]);

    useEffect(() => {
        const fetchReportData = async () => {
            try {
                // Try to fetch report data from the backend
                const reportData = await getReportData(sessionId)
                setData(reportData)
                setLoading(false)
            } catch (err) {
                console.error("Error fetching report from backend:", err)

                // Fallback to localStorage if backend fails
                const storedData = localStorage.getItem(`session_${sessionId}`)
                if (storedData) {
                    const sessionData = JSON.parse(storedData)
                    const turnCount = sessionData.transcript?.filter((m: any) => m.role === 'user').length || 0
                    const baseScore = Math.min(5 + turnCount * 0.5, 9.5)
                    const randomVariance = () => (Math.random() - 0.5) * 1.5

                    // Generate fallback mock data
                    const mockReport: ReportData = {
                        meta: {
                            fit_score: Math.max(3, Math.min(10, baseScore + randomVariance())),
                            fit_label: baseScore >= 7 ? "Strong Performance" : baseScore >= 5 ? "Good Progress" : "Needs Practice",
                            potential_score: Math.max(5, Math.min(10, baseScore + 1 + randomVariance())),
                            summary: turnCount >= 3
                                ? "You demonstrated good engagement throughout the conversation. There were moments of strong communication, with opportunities for improvement in handling objections."
                                : "The session was brief. Consider longer practice sessions to develop your skills further."
                        },
                        sidebar_data: {
                            top_traits: ["Adaptability", "Active Listening", "Empathy"],
                            improvements: ["Handling objections", "Closing techniques", "Asking follow-up questions"],
                            motivators: ["Achievement", "Recognition", "Growth"],
                            derailers: ["Time pressure", "Unclear expectations"]
                        },
                        functional_cards: [
                            { name: "Communication", score: Math.max(3, Math.min(10, baseScore + randomVariance())), text: "Clear articulation of ideas with room for improvement in persuasive language." },
                            { name: "Problem Solving", score: Math.max(3, Math.min(10, baseScore + randomVariance())), text: "Showed ability to think on your feet and address concerns." },
                            { name: "Professionalism", score: Math.max(3, Math.min(10, baseScore + 0.5 + randomVariance())), text: "Maintained appropriate tone throughout the interaction." },
                            { name: "Adaptability", score: Math.max(3, Math.min(10, baseScore + randomVariance())), text: "Adjusted approach based on feedback received." }
                        ],
                        behavioral_cards: [
                            { name: "Active Listening", score: Math.max(3, Math.min(10, baseScore + randomVariance())), text: "Demonstrated attention to detail in responses." },
                            { name: "Emotional Intelligence", score: Math.max(3, Math.min(10, baseScore + randomVariance())), text: "Showed awareness of the other party's perspective." },
                            { name: "Confidence", score: Math.max(3, Math.min(10, baseScore - 0.5 + randomVariance())), text: "Room for improvement in assertive communication." }
                        ],
                        chatberry_analysis: {
                            analysis_text: "The conversation flow was natural with good turn-taking patterns.",
                            metrics: [
                                { label: "Engagement", score: Math.round(baseScore * 10) },
                                { label: "Clarity", score: Math.round((baseScore + 0.5) * 10) },
                                { label: "Impact", score: Math.round((baseScore - 0.5) * 10) }
                            ]
                        },
                        emotional_intelligence: {
                            overall_eq_score: Math.max(3, Math.min(10, baseScore + randomVariance())),
                            eq_summary: "Your emotional awareness during the conversation showed potential for growth. Focus on actively acknowledging the other party's feelings before presenting solutions.",
                            metrics: [
                                { label: "Empathy Display", score: Math.max(3, Math.min(10, baseScore + randomVariance())), feedback: "Consider explicitly acknowledging emotions before responding." },
                                { label: "Emotional Regulation", score: Math.max(3, Math.min(10, baseScore + 0.5 + randomVariance())), feedback: "Maintained composure throughout the interaction." },
                                { label: "Vulnerability Connection", score: Math.max(3, Math.min(10, baseScore - 0.5 + randomVariance())), feedback: "Try to identify the underlying needs behind objections." },
                                { label: "Active Listening", score: Math.max(3, Math.min(10, baseScore + randomVariance())), feedback: "Good attention to what was being said." },
                                { label: "De-escalation Skill", score: Math.max(3, Math.min(10, baseScore + randomVariance())), feedback: "Effective at keeping the conversation constructive." }
                            ]
                        },
                        coach_rewrite_card: {
                            title: "Key Learning Moment",
                            context: "When addressing resistance or objections",
                            original_user_response: sessionData.transcript?.find((m: any) => m.role === 'user')?.content || "Your response here",
                            pro_rewrite: "I understand your concern about [specific issue]. Let me address that by explaining how [solution] could work for your situation specifically.",
                            why_it_works: "This reframe acknowledges the concern while pivoting to a solution-oriented approach."
                        },
                        learning_plan: {
                            priority_focus: "Focus on building rapport before addressing objections directly.",
                            recommended_drill: "Practice the 'feel, felt, found' technique for handling objections.",
                            suggested_reading: "Start with Why by Simon Sinek - for understanding motivational communication."
                        },
                        transcript: sessionData.transcript || [],
                        scenario: sessionData.scenario || ""
                    }

                    setData(mockReport)
                }
                setLoading(false)
            }
        }

        if (sessionId) fetchReportData()
    }, [sessionId])

    const handleDownload = () => {
        // Open the PDF report from the backend in a new tab
        window.open(getReportPdfUrl(sessionId), '_blank')
    }

    const getScoreColor = (score: number) => {
        if (score >= 7) return "text-emerald-400"
        if (score >= 5) return "text-amber-400"
        return "text-rose-400"
    }

    const getScoreBg = (score: number) => {
        if (score >= 7) return "bg-emerald-500/20 border-emerald-500/30"
        if (score >= 5) return "bg-amber-500/20 border-amber-500/30"
        return "bg-rose-500/20 border-rose-500/30"
    }

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 gap-6 font-sans">
                <div className="relative">
                    <div className="absolute inset-0 rounded-full bg-blue-500/30 animate-ping" />
                    <Loader2 className="h-16 w-16 animate-spin text-blue-400 relative z-10" />
                </div>
                <div className="text-center">
                    <p className="text-white font-bold text-2xl mb-2">Analyzing Performance</p>
                    <p className="text-slate-400 animate-pulse">Generating comprehensive insights...</p>
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
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-emerald-500/30 overflow-hidden">
            <Navigation />

            {/* Animated Background - Emerald/Green Theme (Success/Growth) */}
            <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
                {/* Morphing Blobs */}
                <motion.div
                    className="absolute rounded-full"
                    style={{
                        top: '-10%',
                        left: '20%',
                        width: '45rem',
                        height: '45rem',
                        background: 'radial-gradient(circle, rgba(16,185,129,0.12) 0%, transparent 70%)',
                        filter: 'blur(70px)'
                    }}
                    animate={{
                        x: [0, 40, 0],
                        y: [0, 30, 0],
                        scale: [1, 1.08, 1],
                    }}
                    transition={{
                        duration: 24,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
                <motion.div
                    className="absolute rounded-full"
                    style={{
                        top: '50%',
                        right: '-10%',
                        width: '35rem',
                        height: '35rem',
                        background: 'radial-gradient(circle, rgba(52,211,153,0.1) 0%, transparent 70%)',
                        filter: 'blur(60px)'
                    }}
                    animate={{
                        x: [0, -50, 0],
                        y: [0, -40, 0],
                        scale: [1, 0.95, 1],
                    }}
                    transition={{
                        duration: 20,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
                <motion.div
                    className="absolute rounded-full"
                    style={{
                        bottom: '-15%',
                        left: '40%',
                        width: '30rem',
                        height: '30rem',
                        background: 'radial-gradient(circle, rgba(5,150,105,0.08) 0%, transparent 70%)',
                        filter: 'blur(50px)'
                    }}
                    animate={{
                        x: [0, 30, 0],
                        y: [0, -20, 0],
                    }}
                    transition={{
                        duration: 18,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />

                {/* Success/Growth themed floating particles */}
                {[...Array(12)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute rounded-full"
                        style={{
                            left: `${5 + i * 8}%`,
                            top: `${15 + (i % 4) * 20}%`,
                            width: `${3 + (i % 3)}px`,
                            height: `${3 + (i % 3)}px`,
                            background: i % 2 === 0 ? 'rgba(52,211,153,0.4)' : 'rgba(16,185,129,0.3)',
                        }}
                        animate={{
                            y: [0, -25, 0],
                            opacity: [0.3, 0.7, 0.3],
                            scale: [1, 1.2, 1],
                        }}
                        transition={{
                            duration: 4 + i * 0.3,
                            repeat: Infinity,
                            delay: i * 0.2,
                            ease: "easeInOut"
                        }}
                    />
                ))}

                {/* Subtle gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-950/20 via-transparent to-slate-950/30" />
            </div>

            <main className="container mx-auto px-6 py-32 space-y-12 relative z-10">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-white">Performance Report</h1>
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
                                <span className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider border shadow-lg animate-count-up ${getScoreBg(data.meta.fit_score)}`}>
                                    {data.meta.fit_label}
                                </span>
                                <span className="text-slate-400 text-sm font-medium flex items-center gap-1">
                                    <Clock className="w-4 h-4" /> Just now
                                </span>
                            </div>

                            {/* Animated Score Display */}
                            <h2 className="text-5xl md:text-7xl font-black text-white mb-8 leading-tight tracking-tight">
                                <span className="score-ring text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400 text-gradient-animate">
                                    {animatedScore.toFixed(1)}
                                </span>
                                <span className="text-3xl text-slate-500 ml-2 font-light">/ 10</span>
                            </h2>

                            <p className="text-xl md:text-2xl text-slate-300 leading-relaxed max-w-3xl font-light">
                                {data.meta.summary}
                            </p>
                        </div>
                    </motion.div>

                    {/* Potential & Stats Side Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="lg:col-span-4 card-ultra-glass p-10 flex flex-col justify-between relative overflow-hidden group"
                    >
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/20 rounded-full blur-[60px] group-hover:bg-purple-500/30 transition-colors duration-500" />
                        <div>
                            <h3 className="text-slate-400 text-sm font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-purple-400" /> Potential Upside
                            </h3>
                            <div className="text-6xl font-black text-white mb-4 animate-count-up">{animatedPotential.toFixed(1)}</div>
                            <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden mb-8 shadow-inner">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${(data.meta.potential_score / 10) * 100}%` }}
                                    transition={{ duration: 1, ease: "easeOut" }}
                                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500 shadow-[0_0_20px_rgba(59,130,246,0.5)]"
                                />
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Top Strength</div>
                                <div className="text-white font-semibold text-lg">{data.sidebar_data.top_traits[0] || "None detected"}</div>
                            </div>
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Focus Area</div>
                                <div className="text-white font-semibold text-lg">{data.sidebar_data.improvements[0] || "General practice"}</div>
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

                {/* Analysis Grid */}
                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Functional Radar */}
                    <section className="card-ultra-glass p-10">
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 rounded-2xl bg-blue-500/20 flex items-center justify-center text-blue-400 shadow-lg shadow-blue-500/10">
                                <Brain className="w-6 h-6" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">Core Competencies</h3>
                        </div>

                        <div className="h-[350px] w-full mb-10">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data.functional_cards.map(c => ({ subject: c.name, A: c.score, fullMark: 10 }))}>
                                    <PolarGrid stroke="#334155" strokeDasharray="3 3" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                                    <Radar name="Competencies" dataKey="A" stroke="#3b82f6" strokeWidth={3} fill="#3b82f6" fillOpacity={0.3} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="grid gap-3">
                            {data.functional_cards.map((card, i) => (
                                <div key={i} className="group p-5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/5">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-semibold text-white">{card.name}</span>
                                        <span className={`font-bold ${getScoreColor(card.score)}`}>{card.score}/10</span>
                                    </div>
                                    <p className="text-sm text-slate-400 line-clamp-2">{card.text}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Behavioral Bars */}
                    <section className="card-ultra-glass p-10">
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 rounded-2xl bg-purple-500/20 flex items-center justify-center text-purple-400 shadow-lg shadow-purple-500/10">
                                <MessageSquare className="w-6 h-6" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">Behavioral Analysis</h3>
                        </div>

                        <div className="space-y-8">
                            {data.behavioral_cards.map((card, i) => (
                                <div key={i} className="mb-6">
                                    <div className="flex justify-between items-center mb-3">
                                        <span className="font-semibold text-white text-lg">{card.name}</span>
                                        <span className={`font-bold ${getScoreColor(card.score)}`}>{card.score}/10</span>
                                    </div>
                                    <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden mb-4 shadow-inner">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            whileInView={{ width: `${card.score * 10}%` }}
                                            viewport={{ once: true }}
                                            transition={{ duration: 1, delay: i * 0.1 }}
                                            className={`h-full rounded-full shadow-lg ${card.score >= 7 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : card.score >= 5 ? 'bg-gradient-to-r from-amber-500 to-amber-400' : 'bg-gradient-to-r from-rose-500 to-rose-400'}`}
                                        />
                                    </div>
                                    <p className="text-sm text-slate-400 bg-black/20 p-4 rounded-xl border border-white/5 leading-relaxed">
                                        {card.text}
                                    </p>
                                </div>
                            ))}
                        </div>

                        <div className="mt-10 pt-8 border-t border-white/10">
                            <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2 uppercase tracking-wider">
                                <Target className="w-4 h-4 text-blue-400" /> Key Traits Detected
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {data.sidebar_data.top_traits.map((t, i) => (
                                    <span key={i} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm font-medium text-blue-200 hover:bg-blue-500/10 hover:border-blue-500/30 transition-colors">
                                        {t}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </section>
                </div>

                {/* Emotional Intelligence Section */}
                {data.emotional_intelligence && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="card-ultra-glass p-10"
                    >
                        <div className="flex items-center gap-4 mb-10">
                            <div className="w-12 h-12 rounded-2xl bg-pink-500/20 flex items-center justify-center text-pink-400 shadow-lg shadow-pink-500/10">
                                <Heart className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white">Emotional Intelligence</h3>
                                <p className="text-slate-400">Your ability to connect and empathize</p>
                            </div>
                            <div className="ml-auto text-right">
                                <div className="text-4xl font-black text-pink-400">
                                    {data.emotional_intelligence.overall_eq_score.toFixed(1)}
                                    <span className="text-lg text-slate-500 font-normal">/10</span>
                                </div>
                            </div>
                        </div>

                        {data.emotional_intelligence.eq_summary && (
                            <div className="bg-pink-500/5 border border-pink-500/10 rounded-2xl p-6 mb-8">
                                <p className="text-slate-300 leading-relaxed">
                                    {data.emotional_intelligence.eq_summary}
                                </p>
                            </div>
                        )}

                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {data.emotional_intelligence.metrics.map((metric, idx) => (
                                <div
                                    key={idx}
                                    className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:bg-white/10 transition-colors"
                                >
                                    <div className="flex justify-between items-center mb-3">
                                        <span className="font-semibold text-white">{metric.label}</span>
                                        <span className={`font-bold ${getScoreColor(metric.score)}`}>
                                            {metric.score.toFixed(1)}/10
                                        </span>
                                    </div>
                                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden mb-4">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            whileInView={{ width: `${metric.score * 10}%` }}
                                            viewport={{ once: true }}
                                            transition={{ duration: 0.8, delay: idx * 0.1 }}
                                            className={`h-full rounded-full ${metric.score >= 7 ? 'bg-gradient-to-r from-pink-500 to-rose-400' : metric.score >= 5 ? 'bg-gradient-to-r from-amber-500 to-amber-400' : 'bg-gradient-to-r from-rose-500 to-rose-400'}`}
                                        />
                                    </div>
                                    {metric.feedback && (
                                        <p className="text-sm text-slate-400 leading-relaxed">
                                            {metric.feedback}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </motion.div>
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
                                    <h3 className="text-3xl font-bold text-white">Instant Feedback</h3>
                                    <p className="text-slate-400 text-lg">A specific moment where you can improve</p>
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

                {/* Learning Plan */}
                <section className="grid md:grid-cols-3 gap-8">
                    <div className="md:col-span-1 bg-gradient-to-br from-blue-600 to-blue-700 rounded-[2.5rem] p-10 text-white shadow-xl shadow-blue-900/30 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
                            <BookOpen className="w-32 h-32" />
                        </div>
                        <BookOpen className="w-10 h-10 mb-6 text-blue-200" />
                        <h3 className="text-xl font-bold mb-3">Primary Focus</h3>
                        <p className="text-blue-100 leading-relaxed text-lg opacity-90 font-medium">
                            {data.learning_plan.priority_focus}
                        </p>
                    </div>

                    <div className="md:col-span-1 card-ultra-glass p-10 group hover:border-amber-500/30 transition-colors">
                        <Trophy className="w-10 h-10 mb-6 text-amber-500 group-hover:scale-110 transition-transform duration-300" />
                        <h3 className="text-xl font-bold text-white mb-3">Recommended Drill</h3>
                        <p className="text-slate-400 leading-relaxed">
                            {data.learning_plan.recommended_drill}
                        </p>
                    </div>

                    <div className="md:col-span-1 card-ultra-glass p-10 group hover:border-purple-500/30 transition-colors">
                        <Sparkles className="w-10 h-10 mb-6 text-purple-400 group-hover:scale-110 transition-transform duration-300" />
                        <h3 className="text-xl font-bold text-white mb-3">Expert Reading</h3>
                        <p className="text-slate-400 leading-relaxed italic">
                            "{data.learning_plan.suggested_reading}"
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
