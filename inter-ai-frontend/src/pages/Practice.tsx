"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Input } from "@/components/ui/input"
import { motion } from "framer-motion"
import {
    Loader2, Sparkles,
    Swords,
    UserCog,
    Briefcase as BriefcaseIcon,
    DollarSign, Users, ShoppingCart, GraduationCap, AlertTriangle
} from "lucide-react"
import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "../lib/api"

const ICON_MAP: any = {
    Users, ShoppingCart, GraduationCap, AlertTriangle, DollarSign, UserCog
}

const DEFAULT_SCENARIOS = [
    {
        name: "Exercise Test Scenarios",
        color: "from-orange-600 to-red-500",
        scenarios: [
            {
                title: "Scenario 1: Retail Coaching",
                description: "A staff member's recent performance has dropped (sales, energy, engagement). The manager is initiating a coaching conversation, not a disciplinary one.",
                ai_role: "Retail Sales Associate",
                user_role: "Retail Store Manager",
                scenario: "CONTEXT: The conversation takes place inside a retail store. The staff member's recent performance has dropped: Missed sales targets, Low energy on the floor, Poor customer engagement. The manager is initiating a coaching conversation, not a disciplinary one. \n\nAI BEHAVIOR: Start with mild defensiveness (justification, hesitation). Only become more open if the manager shows empathy, looks for root causes, and avoids blame. If the manager is directive or accusatory, remain closed.",
                icon: "Users",
                output_type: "scored_report",
                mode: "evaluation"
            },
            {
                title: "Scenario 2: Low-Price Negotiation",
                description: "Customer is interested in purchasing a high-value product but has concerns about price being too high, competitor offers, and is asking for discounts.",
                ai_role: "Retail Customer",
                user_role: "Salesperson",
                scenario: "CONTEXT: Customer is interested in purchasing a high-value product but has concerns: Price is too high, Comparing with competitor offers, Asking for discounts or add-ons. \n\nAI BEHAVIOR: Be a curious but cautious customer. Push back on price. Test the salesperson's value explanation. Become more agreeable ONLY if value is demonstrated well. If they discount too early, push for more.",
                icon: "ShoppingCart",
                output_type: "scored_report",
                mode: "evaluation"
            },
            {
                title: "Scenario 3: Learning Reflection",
                description: "The user explains how they handled a recent customer interaction (or simulates a short one) to receive coaching guidance.",
                ai_role: "Coach Alex",
                user_role: "Retail Staff",
                scenario: "CONTEXT: The user will explain how they handled a recent customer interaction (or simulate a short one). \n\nAI BEHAVIOR: Do NOT judge or score. Use reflection, curiosity, and learning prompts. Demonstrate 'how to think', not 'what to say'. Guide them to realize their own patterns.",
                icon: "GraduationCap",
                output_type: "learning_plan",
                mode: "coaching"
            }
        ]
    }
]

export default function Practice() {
    const navigate = useNavigate()

    const [sessionMode, setSessionMode] = useState<"coaching" | "evaluation">("coaching")

    const [customRole, setCustomRole] = useState("")
    const [customAiRole, setCustomAiRole] = useState("")
    const [customScenario, setCustomScenario] = useState("")
    const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset")
    const [categories, setCategories] = useState<any[]>(DEFAULT_SCENARIOS)

    // Fetch scenarios
    useEffect(() => {
        const fetchScenarios = async () => {
            try {
                const res = await fetch(getApiUrl('/api/scenarios'))
                if (res.ok) {
                    const data = await res.json()
                    setCategories(data)
                }
            } catch (e) {
                console.error(e)
            }
        }
        fetchScenarios()
    }, [])
    const [loading, setLoading] = useState(false)
    const handleStartSession = async (data: {
        role: string
        ai_role: string
        scenario: string
        mode?: "coaching" | "evaluation"
    }) => {
        setLoading(true)
        try {
            // Call backend to create session
            const response = await fetch(getApiUrl('/session/start'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    role: data.role,
                    ai_role: data.ai_role,
                    scenario: data.scenario,
                    framework: 'auto',  // AI will automatically choose the best framework
                    mode: data.mode || sessionMode // Pass specific mode if defined, else use toggle
                })
            })

            if (!response.ok) {
                throw new Error('Failed to start session')
            }

            const result = await response.json()
            const session_id = result.session_id
            const summary = result.summary

            // Also save to localStorage for offline reference
            localStorage.setItem(
                `session_${session_id}`,
                JSON.stringify({
                    role: data.role,
                    ai_role: data.ai_role,
                    scenario: data.scenario,
                    createdAt: new Date().toISOString(),
                    transcript: [{ role: "assistant", content: summary }],
                    sessionId: session_id,
                    completed: false,
                    mode: sessionMode
                }),
            )

            navigate(`/conversation/${session_id}`)

        } catch (error) {
            console.error("Error starting session:", error)

            toast.error("Failed to start session", {
                description: "Please make sure the backend is running."
            })
        } finally {
            setLoading(false)
        }
    }



    return (
        <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-purple-500/30">
            <Navigation />

            {/* Background */}
            <div className="fixed inset-0 pointer-events-none -z-10">
                <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-blue-600/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600/10 rounded-full blur-[120px]" />
            </div>

            <main className="container mx-auto px-6 pt-32 pb-12">
                {/* Hero Section */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="text-center mb-16"
                >
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="inline-flex items-center gap-2 mb-6 px-5 py-2 rounded-full bg-white/5 border border-white/10 text-sm font-semibold text-blue-300 backdrop-blur-md"
                    >
                        <Loader2 className="w-4 h-4 animate-pulse" />
                        <span>Interactive Roleplay Studio</span>
                    </motion.div>

                    <h1 className="text-4xl md:text-6xl font-black mb-6 tracking-tight text-white leading-[1.1]">
                        Practice with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">Purpose</span>
                    </h1>

                    <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed mb-8">
                        Master real conversations. From pricing negotiations to leadership challenges.
                    </p>

                    {/* Tab Toggle */}
                    <div className="flex justify-center mb-8">
                        <div className="p-1 bg-slate-900/80 backdrop-blur-lg rounded-xl border border-white/10 flex gap-1">
                            <button
                                onClick={() => setActiveTab("preset")}
                                className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === "preset" ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}
                            >
                                Guided Exercises
                            </button>
                            <button
                                onClick={() => setActiveTab("custom")}
                                className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === "custom" ? "bg-indigo-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}
                            >
                                Custom Sandbox
                            </button>
                        </div>
                    </div>

                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                    className="max-w-4xl mx-auto"
                >
                    {activeTab === "preset" ? (
                        <div className="space-y-12">
                            {categories.map((category, idx) => (
                                <div key={idx} className="space-y-6">
                                    <div className="flex items-center gap-4">
                                        <div className={`h-8 w-1 bg-gradient-to-b ${category.color} rounded-full`} />
                                        <h3 className="text-2xl font-bold text-white tracking-tight">{category.name}</h3>
                                    </div>
                                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {category.scenarios.map((scenario: any, sIdx: number) => {
                                            const Icon = ICON_MAP[scenario.icon] || Sparkles
                                            const isAssessment = scenario.output_type === 'scored_report'
                                            const modeLabel = isAssessment ? "Assessment Mode" : "Learning Mode"
                                            const ModeIcon = isAssessment ? Swords : GraduationCap
                                            const badgeColor = isAssessment ? "bg-rose-500/20 text-rose-300 border-rose-500/30" : "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"

                                            return (
                                                <div
                                                    key={sIdx}
                                                    onClick={() => handleStartSession({
                                                        role: scenario.user_role,
                                                        ai_role: scenario.ai_role,
                                                        scenario: scenario.scenario,
                                                        mode: scenario.mode
                                                    })}
                                                    className="group relative p-6 bg-slate-900/40 hover:bg-slate-800/60 border border-white/5 hover:border-blue-500/30 rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden"
                                                >
                                                    <div className={`absolute top-0 right-0 p-16 rounded-full blur-2xl opacity-0 group-hover:opacity-10 bg-gradient-to-br ${category.color} transition-opacity duration-500`} />

                                                    <div className="relative z-10">
                                                        <div className="flex justify-between items-start mb-4">
                                                            <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 text-slate-300 group-hover:text-white`}>
                                                                <Icon className="w-6 h-6" />
                                                            </div>
                                                            <div className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${badgeColor} flex items-center gap-1.5`}>
                                                                <ModeIcon className="w-3 h-3" />
                                                                {modeLabel}
                                                            </div>
                                                        </div>

                                                        <h4 className="text-lg font-bold text-white mb-2 group-hover:text-blue-200 transition-colors">{scenario.title}</h4>
                                                        <p className="text-sm text-slate-400 line-clamp-3 mb-4 leading-relaxed">{scenario.description}</p>

                                                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 group-hover:text-blue-400 transition-colors">
                                                            <span>Start Scenario</span>
                                                            <Swords className="w-3 h-3" />
                                                        </div>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="card-ultra-glass p-10 md:p-12">
                            <div className="text-center mb-10">
                                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold uppercase tracking-wider mb-6">
                                    <Sparkles className="w-4 h-4" /> AI Sandbox
                                </div>
                                <h2 className="text-3xl font-bold text-white mb-3">Design Your Scenario</h2>
                                <p className="text-slate-400 text-lg mb-8">Describe any situation, and our AI will improvise the role.</p>

                                {/* Mode Toggle - ONLY for Custom Mode */}
                                <div className="inline-flex p-1 bg-slate-950/50 rounded-xl border border-white/10 relative mb-8">
                                    <button
                                        onClick={() => setSessionMode("coaching")}
                                        className={`relative px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${sessionMode === "coaching" ? "text-white shadow-lg" : "text-slate-400 hover:text-white"}`}
                                    >
                                        {sessionMode === "coaching" && (
                                            <motion.div
                                                layoutId="mode-highlight"
                                                className="absolute inset-0 bg-blue-600 rounded-lg"
                                                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                                            />
                                        )}
                                        <span className="relative z-10 flex items-center gap-2">
                                            <GraduationCap className="w-4 h-4" /> Learning Mode
                                        </span>
                                    </button>
                                    <button
                                        onClick={() => setSessionMode("evaluation")}
                                        className={`relative px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${sessionMode === "evaluation" ? "text-white shadow-lg" : "text-slate-400 hover:text-white"}`}
                                    >
                                        {sessionMode === "evaluation" && (
                                            <motion.div
                                                layoutId="mode-highlight"
                                                className="absolute inset-0 bg-rose-600 rounded-lg"
                                                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                                            />
                                        )}
                                        <span className="relative z-10 flex items-center gap-2">
                                            <Swords className="w-4 h-4" /> Assessment Mode
                                        </span>
                                    </button>
                                </div>

                                <div className="text-left bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-sm">
                                    <p className="text-amber-300 font-semibold mb-2">💡 Tip: For best results, include:</p>
                                    <ul className="text-slate-400 space-y-1 ml-4 list-disc">
                                        <li>The context (who, what, where)</li>
                                        <li>The conflict or challenge</li>
                                        <li>Your goal in this conversation</li>
                                    </ul>
                                </div>
                            </div>


                            <div className="space-y-6">
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">Your Role</label>
                                        <div className="relative group">
                                            <BriefcaseIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
                                            <Input
                                                placeholder="Product Manager"
                                                value={customRole}
                                                onChange={(e) => setCustomRole(e.target.value)}
                                                className="bg-black/20 border-white/10 focus:border-blue-500/50 h-14 pl-12 rounded-xl text-white placeholder:text-slate-600 font-medium"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">AI Role</label>
                                        <div className="relative group">
                                            <UserCog className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-purple-400 transition-colors" />
                                            <Input
                                                placeholder="Angry Customer"
                                                value={customAiRole}
                                                onChange={(e) => setCustomAiRole(e.target.value)}
                                                className="bg-black/20 border-white/10 focus:border-purple-500/50 h-14 pl-12 rounded-xl text-white placeholder:text-slate-600 font-medium"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">The Situation</label>
                                    <textarea
                                        placeholder="Describe the context, the conflict, and your goal..."
                                        className="w-full pl-6 pr-6 py-4 rounded-2xl bg-black/20 border border-white/10 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all min-h-[160px] resize-none outline-none text-base text-white placeholder:text-slate-600 leading-relaxed"
                                        value={customScenario}
                                        onChange={(e) => setCustomScenario(e.target.value)}
                                    />
                                </div>

                                <button
                                    onClick={() => handleStartSession({
                                        role: customRole,
                                        ai_role: customAiRole,
                                        scenario: customScenario,
                                    })}
                                    disabled={!customRole || !customAiRole || !customScenario || loading}
                                    className="w-full btn-ultra-modern h-16 text-lg mt-6"
                                >
                                    {loading ? (
                                        <div className="flex items-center gap-3">
                                            <Loader2 className="h-6 w-6 animate-spin" />
                                            <span>Initializing...</span>
                                        </div>
                                    ) : (
                                        <span className="flex items-center gap-3">
                                            Launch Custom Simulation <Sparkles className="w-5 h-5" />
                                        </span>
                                    )}
                                </button>
                            </div>
                        </div>
                    )
                    }
                </motion.div >
            </main >
        </div >
    )
}
