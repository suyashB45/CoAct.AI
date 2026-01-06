"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Input } from "@/components/ui/input"
import { motion, AnimatePresence } from "framer-motion"
import {
    Loader2, Sparkles, ChevronRight,
    MonitorPlay, Swords,
    DollarSign,
    UserCog,
    Briefcase, Users,
    Presentation,
    Briefcase as BriefcaseIcon,
    Phone, Search, Target, Handshake, AlertTriangle, TrendingUp, MessageSquare
} from "lucide-react"
import Navigation from "../components/landing/Navigation"



export default function Practice() {
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset")
    const [sessionMode, setSessionMode] = useState<"coaching" | "evaluation">("coaching")
    const [activeCategory] = useState(0)
    const [customRole, setCustomRole] = useState("")
    const [customAiRole, setCustomAiRole] = useState("")
    const [customScenario, setCustomScenario] = useState("")
    const [loading, setLoading] = useState(false)
    const [categories, setCategories] = useState<any[]>([])
    const [isLoadingData, setIsLoadingData] = useState(true)

    // Icons map for dynamic rendering
    const ICON_MAP: any = {
        DollarSign, UserCog, Users, Briefcase, Presentation, Sparkles,
        Phone, Search, Target, Handshake, AlertTriangle, TrendingUp, MessageSquare
    }

    // Fetch scenarios on mount
    useState(() => {
        const fetchScenarios = async () => {
            try {
                // Use relative URL so it works with proxy, or env var. 
                // Hardcoding localhost:8000 for now as requested or relative.
                // Best practice: use VITE_API_URL or relative /api if proxy setup.
                // Assuming local setup:
                const res = await fetch('http://localhost:8000/api/scenarios')
                if (res.ok) {
                    const data = await res.json()
                    setCategories(data)
                } else {
                    console.error("Failed to fetch scenarios")
                }
            } catch (e) {
                console.error(e)
            } finally {
                setIsLoadingData(false)
            }
        }
        fetchScenarios()
    })


    const handleStartSession = async (data: {
        role: string
        ai_role: string
        scenario: string
    }) => {
        setLoading(true)
        try {
            // Call backend to create session
            const response = await fetch('http://localhost:8000/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    role: data.role,
                    ai_role: data.ai_role,
                    scenario: data.scenario,
                    framework: 'auto',  // AI will automatically choose the best framework
                    mode: sessionMode // Pass the selected mode
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

    const currentCategory = categories[activeCategory] || { scenarios: [], color: "from-gray-500 to-slate-500" }

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
                        <Sparkles className="w-4 h-4 animate-pulse" />
                        <span>Interactive Roleplay Studio</span>
                    </motion.div>

                    <h1 className="text-4xl md:text-6xl font-black mb-6 tracking-tight text-white leading-[1.1]">
                        Practice with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">Purpose</span>
                    </h1>

                    <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed mb-8">
                        Master real conversations. From pricing negotiations to leadership challenges.
                    </p>

                    {/* Mode Toggle */}
                    <div className="inline-flex p-1 bg-slate-900/80 backdrop-blur-lg rounded-xl border border-white/10 relative">
                        <button
                            onClick={() => setSessionMode("coaching")}
                            className={`relative px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${sessionMode === "coaching" ? "text-white shadow-lg" : "text-slate-400 hover:text-white"
                                }`}
                        >
                            {sessionMode === "coaching" && (
                                <motion.div
                                    layoutId="mode-highlight"
                                    className="absolute inset-0 bg-blue-600 rounded-lg"
                                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                                />
                            )}
                            <span className="relative z-10 flex items-center gap-2">
                                <MonitorPlay className="w-4 h-4" /> Coaching Mode
                            </span>
                        </button>
                        <button
                            onClick={() => setSessionMode("evaluation")}
                            className={`relative px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${sessionMode === "evaluation" ? "text-white shadow-lg" : "text-slate-400 hover:text-white"
                                }`}
                        >
                            {sessionMode === "evaluation" && (
                                <motion.div
                                    layoutId="mode-highlight"
                                    className="absolute inset-0 bg-rose-600 rounded-lg"
                                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                                />
                            )}
                            <span className="relative z-10 flex items-center gap-2">
                                <Swords className="w-4 h-4" /> Evaluation Mode
                            </span>
                        </button>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                    className="max-w-2xl mx-auto"
                >
                    <div className="card-ultra-glass p-10 md:p-12">
                        <div className="text-center mb-10">
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold uppercase tracking-wider mb-6">
                                <Sparkles className="w-4 h-4" /> AI Sandbox
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-3">Design Your Scenario</h2>
                            <p className="text-slate-400 text-lg mb-4">Describe any situation, and our AI will improvise the role.</p>
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
                </motion.div>
            </main>
        </div>
    )
}
