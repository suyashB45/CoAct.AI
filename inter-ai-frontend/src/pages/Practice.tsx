"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Input } from "@/components/ui/input"
import { motion } from "framer-motion"
import {
    Loader2, Sparkles,
    UserCog,
    Briefcase as BriefcaseIcon,
    DollarSign, Users, ShoppingCart, GraduationCap, AlertTriangle, Check, ArrowRight
} from "lucide-react"
import Navigation from "../components/landing/Navigation"
import { getApiUrl } from "../lib/api"
import { supabase } from "../lib/supabase"

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
                description: "A staff member's recent performance has dropped (sales, energy, engagement). The manager is initiating a coaching conversation to address the decline.",
                ai_role: "Retail Sales Associate",
                user_role: "Retail Store Manager",
                scenario: "CONTEXT: A staff member's recent performance has dropped (sales, energy, engagement). The manager is initiating a coaching conversation. \n\nFOCUS AREAS: Root cause analysis, empathy, and active listening. \n\nAI BEHAVIOR: You are the staff member. You feel burnt out and unappreciated. Start with mild defensiveness. Only become more open if the manager shows empathy and asks open questions.",
                icon: "Users",
                output_type: "scored_report",
                mode: "evaluation",
                scenario_type: "coaching"
            },
            {
                title: "Scenario 2: Sales and Negotiation",
                description: "A customer is interested in a high-value item but is hesitant about the price. You need to build rapport, discover their actual needs, and articulate value before offering any discounts.",
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
                description: "You are the retail staff member receiving coaching from 'Coach Alex'. The goal is to reflect on a recent interaction, identify where you missed opportunities to ask questions, and practice better responses.",
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

    const [selectedCharacter, setSelectedCharacter] = useState<"alex" | "sarah">("alex")
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
        ai_character?: string
    }) => {
        setLoading(true)
        try {
            // Get authenticated user from Supabase
            const { data: { user } } = await supabase.auth.getUser();

            if (!user) {
                toast.error("Please log in", {
                    description: "You need to be logged in to start a session."
                });
                setLoading(false);
                return;
            }

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
                    user_id: user.id,  // Use Supabase user ID
                    ai_character: data.ai_character // Pass character choice
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
                    scenario_type: result.scenario_type || 'custom',
                    ai_character: result.ai_character || data.ai_character // Prioritize backend confirmation
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

                    {/* Character Selection */}
                    <div className="flex flex-col items-center mb-20 relative">
                        <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent -z-10" />
                        <div className="bg-slate-950 px-4 relative z-10 mb-8">
                            <span className="text-xs font-black text-blue-500 tracking-[0.2em] uppercase border border-blue-900/50 bg-blue-900/20 px-3 py-1 rounded-full">Step 01</span>
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-8 tracking-tight">Select Your Partner</h3>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 md:gap-8 w-full max-w-2xl px-4">
                            {[
                                {
                                    id: "alex",
                                    name: "Alex",
                                    role: "Senior AI Coach",
                                    desc: "Fully adaptive roleplay partner. Shifts dynamically between evaluation and mentorship.",
                                    img: "/alex.png",
                                    voice: "Deep Male Voice (Onyx)",
                                    color: "blue",
                                    traits: ["Scenario Adaptive", "Real-time Feedback", "Role Improvisation"]
                                },
                                {
                                    id: "sarah",
                                    name: "Sarah",
                                    role: "Senior AI Coach",
                                    desc: "Fully adaptive roleplay partner. Shifts dynamically between evaluation and mentorship.",
                                    img: "/sarah.png",
                                    voice: "Natural Female Voice (Nova)",
                                    color: "purple",
                                    traits: ["Scenario Adaptive", "Real-time Feedback", "Role Improvisation"]
                                }
                            ].map((char) => (
                                <motion.button
                                    key={char.id}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => setSelectedCharacter(char.id as any)}
                                    className={`relative group overflow-hidden rounded-3xl border-2 transition-all duration-300 text-left h-full flex flex-col ${selectedCharacter === char.id
                                        ? `border-${char.color}-500 bg-gradient-to-b from-${char.color}-900/40 to-slate-900/80 shadow-[0_0_40px_rgba(${char.color === 'blue' ? '59,130,246' : '168,85,247'},0.3)]`
                                        : "border-white/5 bg-slate-900/40 hover:bg-slate-800/60 hover:border-white/10"
                                        }`}
                                >
                                    <div className="relative h-64 overflow-hidden w-full">
                                        <div className={`absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent z-10`} />
                                        <img
                                            src={char.img}
                                            alt={char.name}
                                            className={`w-full h-full object-cover transition-transform duration-700 ${selectedCharacter === char.id ? 'scale-105' : 'group-hover:scale-110 opacity-60 group-hover:opacity-100'}`}
                                        />

                                        {/* Selection Check */}
                                        {selectedCharacter === char.id && (
                                            <div className="absolute top-4 right-4 z-20">
                                                <motion.div
                                                    initial={{ scale: 0 }}
                                                    animate={{ scale: 1 }}
                                                    className={`w-10 h-10 rounded-full bg-${char.color}-500 flex items-center justify-center shadow-lg border-2 border-white/20`}
                                                >
                                                    <Check className="w-6 h-6 text-white" />
                                                </motion.div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="p-6 relative z-20 -mt-20 flex-1 flex flex-col">
                                        <div className="mb-auto">
                                            <h4 className={`text-3xl font-black mb-1 ${selectedCharacter === char.id ? "text-white" : "text-slate-200"}`}>{char.name}</h4>
                                            <p className={`text-xs font-bold uppercase tracking-widest mb-4 ${selectedCharacter === char.id ? `text-${char.color}-400` : "text-slate-500"}`}>{char.role}</p>

                                            <p className="text-sm text-slate-300 leading-relaxed">
                                                {char.desc}
                                            </p>
                                        </div>
                                    </div>
                                </motion.button>
                            ))}
                        </div>
                    </div>

                    {/* Step 2 Header */}
                    <div className="flex flex-col items-center mb-8 relative">
                        <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent -z-10" />
                        <div className="bg-slate-950 px-4 relative z-10 mb-8">
                            <span className="text-xs font-black text-indigo-500 tracking-[0.2em] uppercase border border-indigo-900/50 bg-indigo-900/20 px-3 py-1 rounded-full">Step 02</span>
                        </div>
                        <h3 className="text-2xl font-bold text-white tracking-tight">Choose Your Challenge</h3>
                    </div>

                    {/* Tab Toggle */}
                    <div className="flex justify-center mb-12">
                        <div className="p-1.5 bg-slate-900/80 backdrop-blur-lg rounded-2xl border border-white/10 flex gap-1 shadow-2xl">
                            <button
                                onClick={() => setActiveTab("preset")}
                                className={`px-6 py-3 rounded-xl text-sm font-bold tracking-wide transition-all duration-300 ${activeTab === "preset" ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20" : "text-slate-400 hover:text-white hover:bg-white/5"}`}
                            >
                                Guided Exercises
                            </button>
                            <button
                                onClick={() => setActiveTab("custom")}
                                className={`px-6 py-3 rounded-xl text-sm font-bold tracking-wide transition-all duration-300 ${activeTab === "custom" ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-purple-500/20" : "text-slate-400 hover:text-white hover:bg-white/5"}`}
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
                    className="max-w-6xl mx-auto"
                >
                    {activeTab === "preset" ? (
                        <div className="space-y-16">
                            {categories.map((category, idx) => (
                                <div key={idx} className="space-y-6">
                                    <div className="flex items-center gap-4">
                                        <div className={`h-10 w-1.5 bg-gradient-to-b ${category.color} rounded-full`} />
                                        <h3 className="text-3xl font-bold text-white tracking-tight">{category.name}</h3>
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
                                            const gradient = category.color;

                                            return (
                                                <div
                                                    key={sIdx}
                                                    onClick={() => handleStartSession({
                                                        role: scenario.user_role,
                                                        ai_role: scenario.ai_role,
                                                        scenario: scenario.scenario,
                                                        scenario_type: scenario.scenario_type,
                                                        ai_character: selectedCharacter
                                                    })}
                                                    className="group relative p-8 bg-slate-900/40 hover:bg-slate-800/80 border border-white/5 hover:border-white/20 rounded-3xl transition-all duration-300 cursor-pointer overflow-hidden backdrop-blur-sm"
                                                >
                                                    {/* Hover Gradient */}
                                                    <div className={`absolute top-0 right-0 w-[120%] h-[120%] bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500 blur-3xl rounded-full translate-x-10 -translate-y-10`} />

                                                    <div className="relative z-10 flex flex-col h-full">
                                                        <div className="flex justify-between items-start mb-6">
                                                            <div className={`w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-500 shadow-inner border border-white/5`}>
                                                                <Icon className="w-7 h-7 text-slate-300 group-hover:text-white transition-colors" />
                                                            </div>
                                                            <div className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${badgeColor} flex items-center gap-1.5`}>
                                                                <ModeIcon className="w-3 h-3" />
                                                                {modeLabel}
                                                            </div>
                                                        </div>

                                                        <h4 className="text-xl font-bold text-white mb-3 group-hover:text-blue-200 transition-colors leading-tight">{scenario.title}</h4>
                                                        <p className="text-slate-400 text-sm leading-relaxed mb-6">{scenario.description}</p>

                                                        <div className="mt-auto pt-6 border-t border-white/5 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500 group-hover:text-white transition-colors">
                                                            <span>Start Practice</span>
                                                            <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-blue-500 group-hover:text-white transition-all">
                                                                <ArrowRight className="w-4 h-4" />
                                                            </div>
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
                        <div className="card-ultra-glass p-10 md:p-14 border border-white/10 shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />

                            <div className="text-center mb-12 relative z-10">
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
                                        ai_character: selectedCharacter
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
