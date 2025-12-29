"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Input } from "@/components/ui/input"
import { motion, AnimatePresence } from "framer-motion"
import {
    Loader2, Sparkles, ChevronRight,
    DollarSign,
    UserCog,
    Briefcase, Users,
    Presentation,
    Briefcase as BriefcaseIcon
} from "lucide-react"
import Navigation from "../components/landing/Navigation"
import { startSession } from "../lib/api"

// Organized by category with real-world scenarios
const SCENARIO_CATEGORIES = [
    {
        name: "Change Management",
        color: "from-blue-600 to-indigo-500",
        scenarios: [
            {
                title: "Legacy Plan Migration",
                description: "Upsell a resistant customer.",
                ai_role: "Stubborn Customer who has been on a cheap legacy plan for years. They refuse to pay more, don't care about new features, and feel the company is betraying loyalty.",
                ai_role_short: "Stubborn Customer",
                user_role: "Sales Rep",
                scenario: "You are calling a loyal customer to inform them their $45/month legacy plan is being retired. They must move to a new $60/month plan. The customer is happy with what they have and will resist any price increase aggressively.",
                icon: DollarSign,
            },
            {
                title: "Process Change Resistance",
                description: "Implement new software.",
                ai_role: "'Sarah', a veteran graphic designer of 8 years. She loves ease and speed, hates complex tools, and thinks the new process is a waste of time.",
                ai_role_short: "Sarah (Veteran Designer)",
                user_role: "Team Manager",
                scenario: "You need to tell Sarah that starting next week, all design submissions must go through 'ProjectFlow', a complex new management tool, instead of just emailing attachments. She will argue that email is faster and works fine.",
                icon: UserCog,
            },
            {
                title: "Remote Policy Pushback",
                description: "Enforce core hours.",
                ai_role: "'Mike', a talented remote developer. He is a night owl, productive, but fiercely protective of his flexible schedule and autonomy.",
                ai_role_short: "Mike (Remote Dev)",
                user_role: "HR Manager",
                scenario: "You are introducing a new company policy requiring all remote workers to be logged in between 10 AM and 3 PM. Mike works best late at night and will argue that this arbitrary rule will hurt his productivity.",
                icon: Users,
            },
            {
                title: "Role Restructuring",
                description: "Change job responsibilities.",
                ai_role: "'David', a social media specialist. He loves creative work and hates technical writing. He feels this change is a 'bait and switch' from his original job.",
                ai_role_short: "David (Social Media)",
                user_role: "Head of Marketing",
                scenario: "Due to team restructuring, you must tell David that 50% of his role will now involve writing technical white papers. He was hired for social media and will resist doing work he dislikes and wasn't hired for.",
                icon: Briefcase,
            },
            {
                title: "Training Skeptic",
                description: "Mandate new workflow.",
                ai_role: "'Alex', a top-performing sales employee. They are arrogant because of their results and believe their own method is superior to your 'corporate script'.",
                ai_role_short: "Alex (Top Performer)",
                user_role: "Corporate Trainer",
                scenario: "You just presented a mandatory new 5-step client call workflow. Alex interrupts to say they are already hitting targets with their own style and shouldn't have to change what works.",
                icon: Presentation,
            },
        ]
    }
]

export default function Practice() {
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset")
    const [activeCategory] = useState(0)
    const [customRole, setCustomRole] = useState("")
    const [customAiRole, setCustomAiRole] = useState("")
    const [customScenario, setCustomScenario] = useState("")
    const [loading, setLoading] = useState(false)


    const handleStartSession = async (data: {
        role: string
        ai_role: string
        scenario: string
    }) => {
        setLoading(true)
        try {
            // Call the backend API to start a session
            const response = await startSession({
                role: data.role,
                ai_role: data.ai_role,
                scenario: data.scenario,
                framework: ["GROW", "STAR", "ADKAR", "SMART", "EQ"]
            })

            // Store session data in localStorage for quick access
            localStorage.setItem(
                `session_${response.session_id}`,
                JSON.stringify({
                    role: data.role,
                    ai_role: data.ai_role,
                    scenario: data.scenario,
                    createdAt: new Date().toISOString(),
                    transcript: [{ role: "assistant", content: response.summary }],
                    sessionId: response.session_id,
                    completed: false
                }),
            )

            toast.success("Session Started", {
                description: "Connected to AI roleplay partner"
            })

            navigate(`/conversation/${response.session_id}`)

        } catch (error) {
            console.error("Error starting session:", error)

            toast.error("Failed to start session", {
                description: error instanceof Error ? error.message : "Please check if the backend is running."
            })
        } finally {
            setLoading(false)
        }
    }

    const currentCategory = SCENARIO_CATEGORIES[activeCategory]

    // Generate floating particles for background
    const particles = Array.from({ length: 15 }, (_, i) => ({
        id: i,
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        delay: Math.random() * 5,
        size: 2 + Math.random() * 3,
    }))

    return (
        <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-purple-500/30 overflow-hidden">
            <Navigation />

            {/* Animated Background - Purple/Indigo Theme */}
            <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
                {/* Floating Particles */}
                {particles.map((p) => (
                    <motion.div
                        key={p.id}
                        className="absolute rounded-full bg-purple-400/30"
                        style={{
                            left: p.left,
                            top: p.top,
                            width: `${p.size}px`,
                            height: `${p.size}px`,
                        }}
                        animate={{
                            y: [0, -30, 0],
                            opacity: [0.3, 0.8, 0.3],
                        }}
                        transition={{
                            duration: 4 + Math.random() * 2,
                            repeat: Infinity,
                            delay: p.delay,
                            ease: "easeInOut"
                        }}
                    />
                ))}

                {/* Morphing Blobs */}
                <motion.div
                    className="absolute rounded-full"
                    style={{
                        top: '-10%',
                        left: '-5%',
                        width: '40rem',
                        height: '40rem',
                        background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)',
                        filter: 'blur(60px)'
                    }}
                    animate={{
                        x: [0, 50, 0],
                        y: [0, 30, 0],
                        scale: [1, 1.1, 1],
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
                        top: '30%',
                        right: '-10%',
                        width: '35rem',
                        height: '35rem',
                        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
                        filter: 'blur(70px)'
                    }}
                    animate={{
                        x: [0, -40, 0],
                        y: [0, 50, 0],
                        scale: [1, 0.95, 1],
                    }}
                    transition={{
                        duration: 25,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
                <motion.div
                    className="absolute rounded-full"
                    style={{
                        bottom: '-15%',
                        left: '30%',
                        width: '30rem',
                        height: '30rem',
                        background: 'radial-gradient(circle, rgba(168,85,247,0.1) 0%, transparent 70%)',
                        filter: 'blur(50px)'
                    }}
                    animate={{
                        x: [0, 60, 0],
                        y: [0, -20, 0],
                    }}
                    transition={{
                        duration: 18,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />

                {/* Subtle grid overlay */}
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwgMjU1LCAyNTUsIDAuMDMpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50" />
            </div>

            <main className="container mx-auto px-6 pt-32 pb-12 relative z-10">
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
                        className="inline-flex items-center gap-2 mb-6 px-5 py-2 rounded-full bg-white/5 border border-white/10 text-sm font-semibold text-purple-300 backdrop-blur-md"
                    >
                        <Sparkles className="w-4 h-4 animate-pulse" />
                        <span>Interactive Roleplay Studio</span>
                    </motion.div>

                    <h1 className="text-4xl md:text-6xl font-black mb-6 tracking-tight text-white leading-[1.1]">
                        Practice with <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-indigo-400 to-blue-400">Purpose</span>
                    </h1>

                    <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
                        Master real conversations. From pricing negotiations to leadership challenges.
                    </p>
                </motion.div>

                {/* Tab Switcher */}
                <div className="max-w-md mx-auto mb-12 relative p-1.5 rounded-full bg-slate-900/50 backdrop-blur-xl border border-white/10 shadow-xl flex">
                    {(["preset", "custom"] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 relative py-3 rounded-full text-sm font-bold transition-all duration-300 z-10 ${activeTab === tab ? "text-white" : "text-slate-400 hover:text-white"}`}
                        >
                            {activeTab === tab && (
                                <motion.div
                                    layoutId="activeTab"
                                    className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full shadow-lg shadow-blue-500/20"
                                    initial={false}
                                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                                />
                            )}
                            <span className="relative z-10">{tab === "preset" ? "Scenarios" : "Custom Sandbox"}</span>
                        </button>
                    ))}
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === "preset" ? (
                        <motion.div
                            key="preset"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="max-w-6xl mx-auto"
                        >
                            {/* Scenarios Grid */}
                            <motion.div className="grid lg:grid-cols-2 gap-8">
                                {currentCategory.scenarios.map((scenario, idx) => (
                                    <motion.div
                                        key={scenario.title}
                                        initial={{ opacity: 0, y: 30 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        whileHover={{ y: -8, rotateX: 2, rotateY: -2 }}
                                        className="card-ultra-glass card-3d-tilt group p-8 flex flex-col h-full relative overflow-hidden"
                                        style={{ transformStyle: 'preserve-3d' }}
                                    >
                                        {/* Animated gradient orb on hover */}
                                        <div className={`absolute top-0 right-0 w-80 h-80 bg-gradient-to-br ${currentCategory.color} opacity-0 group-hover:opacity-15 blur-[100px] transition-all duration-700 rounded-full -translate-y-1/2 translate-x-1/2`} />
                                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-3xl pointer-events-none" />

                                        <div className="flex items-start gap-4 mb-6 relative z-10">
                                            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${currentCategory.color} flex items-center justify-center text-white shadow-lg shadow-blue-500/20 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
                                                <scenario.icon className="w-7 h-7 group-hover:animate-pulse" />
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-bold text-white mb-2">{scenario.title}</h3>
                                                <p className="text-slate-400 font-medium">{scenario.description}</p>
                                            </div>
                                        </div>

                                        <div className="flex flex-wrap gap-3 mb-6 relative z-10">
                                            <div className="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-bold uppercase tracking-wider">
                                                You: {scenario.user_role}
                                            </div>
                                            <div className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-bold uppercase tracking-wider">
                                                AI: {scenario.ai_role_short}
                                            </div>
                                        </div>

                                        <div className="bg-slate-950/30 rounded-2xl p-5 mb-8 border border-white/5 grow relative z-10">
                                            <p className="text-slate-300 text-sm leading-relaxed">
                                                "{scenario.scenario}"
                                            </p>
                                        </div>

                                        <button
                                            onClick={() => handleStartSession({
                                                role: scenario.user_role,
                                                ai_role: scenario.ai_role,
                                                scenario: scenario.scenario,
                                            })}
                                            disabled={loading}
                                            className="w-full btn-ultra-modern btn-press py-4 flex items-center justify-center gap-2 mt-auto relative z-10 group/btn"
                                        >
                                            {loading ? (
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                            ) : (
                                                <>
                                                    Start Session <ChevronRight className="w-5 h-5" />
                                                </>
                                            )}
                                        </button>
                                    </motion.div>
                                ))}
                            </motion.div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="custom"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="max-w-2xl mx-auto"
                        >
                            <div className="card-ultra-glass p-10 md:p-12">
                                <div className="text-center mb-10">
                                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold uppercase tracking-wider mb-6">
                                        <Sparkles className="w-4 h-4" /> AI Sandbox
                                    </div>
                                    <h2 className="text-3xl font-bold text-white mb-3">Design Your Scenario</h2>
                                    <p className="text-slate-400 text-lg">Describe any situation, and our AI will improvise the role.</p>
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
                    )}
                </AnimatePresence>
            </main>
        </div>
    )
}
