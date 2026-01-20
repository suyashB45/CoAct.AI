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
                title: "Scenario 1: Coaching Effectiveness",
                description: "Manager coaching staff in a retail store. \n\nKey Metrics: Listening and Empathy, Questioning Quality, Psychological Safety, Coaching vs. Telling.",
                ai_role: "Retail Sales Associate",
                user_role: "Retail Store Manager",
                scenario: "CONTEXT: Manager coaching staff in a retail store. \n\nFOCUS AREAS: Creating safe dialogue spaces and allowing self-reflection while reducing directive \"telling\" responses. \n\nAI BEHAVIOR: Start with mild defensiveness. Only become more open if the manager shows empathy and asks open questions. If the manager tells you what to do, remain closed.",
                icon: "Users",
                output_type: "scored_report",
                mode: "evaluation",
                scenario_type: "coaching"
            },
            {
                title: "Scenario 2: Sales and Negotiation",
                description: "Sales and negotiation practice. \n\nKey Metrics: Rapport Building, Needs Discovery, Objection Handling, Value Articulation.",
                ai_role: "Retail Customer",
                user_role: "Salesperson",
                scenario: "CONTEXT: Sales and negotiation coaching for retail staff. \n\nFOCUS AREAS: Developing deeper need-based questioning and delaying price discounting until value is established. \n\nAI BEHAVIOR: Be a customer interested in a high-value item but hesitant about price. Push for a discount early. Only agree if the salesperson builds rapport, discovers your actual needs, and articulates value first.",
                icon: "ShoppingCart",
                output_type: "scored_report",
                mode: "evaluation",
                scenario_type: "negotiation"
            },
            {
                title: "Scenario 3: Skill Development & Learning",
                description: "AI coach developing employee skills. \n\nKey Skills: Questioning techniques, Active listening, Value-based communication.",
                ai_role: "Coach Alex",
                user_role: "Retail Staff",
                scenario: "CONTEXT: AI coach developing employee skills. \n\nFOCUS AREAS: Transitioning from feature-focused explanations to needs exploration and implementing conversational pauses. \n\nAI BEHAVIOR: Do NOT judge or score. Act as a supportive coach helping the user reflect on a recent interaction. Guide them to realize they need to ask more questions and pause more often.",
                icon: "GraduationCap",
                output_type: "learning_plan",
                mode: "coaching",
                scenario_type: "reflection"
            }
        ]
    }
]

export default function Practice() {
    const navigate = useNavigate()

    // No longer need sessionMode - scenario_type is auto-detected

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
        scenario_type?: string
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
                    framework: 'auto',
                    scenario_type: data.scenario_type,
                    user_id: JSON.parse(localStorage.getItem('coact_user') || '{}').id
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
                    scenario_type: result.scenario_type || 'custom'
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
                                            // Use scenario_type for badge display
                                            const scenarioType = scenario.scenario_type || 'custom'
                                            const typeLabels: any = {
                                                'coaching': 'Coaching',
                                                'negotiation': 'Negotiation',
                                                'reflection': 'Reflection',
                                                'custom': 'Custom'
                                            }
                                            const typeColors: any = {
                                                'coaching': 'bg-blue-500/20 text-blue-300 border-blue-500/30',
                                                'negotiation': 'bg-green-500/20 text-green-300 border-green-500/30',
                                                'reflection': 'bg-purple-500/20 text-purple-300 border-purple-500/30',
                                                'custom': 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                                            }
                                            const typeIcons: any = {
                                                'coaching': Users,
                                                'negotiation': ShoppingCart,
                                                'reflection': GraduationCap,
                                                'custom': Sparkles
                                            }
                                            const modeLabel = typeLabels[scenarioType] || 'Custom'
                                            const ModeIcon = typeIcons[scenarioType] || Sparkles
                                            const badgeColor = typeColors[scenarioType] || typeColors['custom']

                                            return (
                                                <div
                                                    key={sIdx}
                                                    onClick={() => handleStartSession({
                                                        role: scenario.user_role,
                                                        ai_role: scenario.ai_role,
                                                        scenario: scenario.scenario,
                                                        scenario_type: scenario.scenario_type
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
                                <p className="text-slate-400 text-lg mb-8">Describe any situation, and our AI will improvise the role. The report type will be auto-detected.</p>

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
