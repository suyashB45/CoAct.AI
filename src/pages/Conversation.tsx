"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Mic, Square, ArrowLeft, Clock, User, Bot, Send, Sparkles, Volume2, History, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface TranscriptMessage {
    role: "user" | "assistant"
    content: string
}

interface SessionData {
    role: string
    ai_role: string
    scenario: string
    createdAt: string
    transcript: TranscriptMessage[]
    sessionId?: string
}

interface ConversationState {
    transcript: TranscriptMessage[]
    isRecording: boolean
    isProcessing: boolean
    turnCount: number
    sessionData: SessionData | null
    elapsedSeconds: number
    currentDraft: string
    showTranscript: boolean
}

const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
}

export default function Conversation() {
    const params = useParams()
    const navigate = useNavigate()
    const sessionId = params.sessionId as string
    const recognitionRef = useRef<any>(null)
    const transcriptEndRef = useRef<HTMLDivElement>(null);

    const [state, setState] = useState<ConversationState>({
        transcript: [],
        isRecording: false,
        isProcessing: false,
        turnCount: 0,
        sessionData: null,
        elapsedSeconds: 0,
        currentDraft: "",
        showTranscript: false,
    })
    const [isAiSpeaking, setIsAiSpeaking] = useState(false)

    // Scroll to bottom of transcript only if it's open
    useEffect(() => {
        if (state.showTranscript) {
            transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [state.transcript, state.currentDraft, state.showTranscript]);

    useEffect(() => {
        const timer = setInterval(() => {
            setState(prev => ({ ...prev, elapsedSeconds: prev.elapsedSeconds + 1 }))
        }, 1000)
        return () => clearInterval(timer)
    }, [])

    const mediaRecorderRef = useRef<MediaRecorder | null>(null)

    const audioRef = useRef<HTMLAudioElement | null>(null)

    const speakText = async (text: string) => {
        // Stop any current audio
        if (audioRef.current) {
            audioRef.current.pause()
            audioRef.current = null
        }
        window.speechSynthesis.cancel() // Safety clear

        try {
            setIsAiSpeaking(true)

            // Remove "internal thoughts" or other artifacts if any slipped through, 
            // though the backend should handle this. 
            // Also, we can send a style here if we parse emotions from the text!
            // For now, simpler is better.

            const response = await fetch("/api/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            })

            if (!response.ok) throw new Error("TTS Failed")

            const blob = await response.blob()
            const url = URL.createObjectURL(blob)
            const audio = new Audio(url)

            audioRef.current = audio
            audio.onended = () => {
                setIsAiSpeaking(false)
                URL.revokeObjectURL(url)
                startRecording()
            }
            audio.onerror = () => {
                setIsAiSpeaking(false)
                // Optional: maintain flow even on error?
                // startRecording() 
            }

            await audio.play()

        } catch (error) {
            console.error("TTS Playback Error:", error)
            setIsAiSpeaking(false)
            // Fallback to browser if server fails?
            // const speech = new SpeechSynthesisUtterance(text)
            // window.speechSynthesis.speak(speech) 
        }
    }

    useEffect(() => {
        const storedData = localStorage.getItem(`session_${sessionId}`)
        if (storedData) {
            const sessionData: SessionData = JSON.parse(storedData)

            const initialTranscript = sessionData.transcript.length > 0
                ? sessionData.transcript
                : [{
                    role: "assistant",
                    content: `Hello! I'm your ${sessionData.ai_role}. We are here to practice: ${sessionData.scenario}. Ready?`
                }]

            setState((prev) => ({
                ...prev,
                sessionData,
                transcript: initialTranscript as TranscriptMessage[],
            }))

            const latestMsg = initialTranscript[initialTranscript.length - 1]
            if (latestMsg.role === 'assistant') {
                const timer = setTimeout(() => {
                    speakText(latestMsg.content)
                }, 500)
                return () => clearTimeout(timer)
            }
        }
    }, [sessionId])

    useEffect(() => {
        return () => {
            if ("speechSynthesis" in window) {
                window.speechSynthesis.cancel()
            }
            if (recognitionRef.current) {
                recognitionRef.current.stop()
            }
        }
    }, [])

    const stopRecording = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop()
        }
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop()
            if (mediaRecorderRef.current.stream) {
                mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop())
            }
        }
        setState((prev) => ({ ...prev, isRecording: false }))
    }, [])

    const startRecording = async () => {
        if (isAiSpeaking) return

        try {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

            if (SpeechRecognition) {
                const recognition = new SpeechRecognition()
                recognition.continuous = true
                recognition.interimResults = true
                recognition.lang = 'en-US'

                recognition.onstart = () => {
                    setState(prev => ({ ...prev, isRecording: true }))
                }

                recognition.onresult = (event: any) => {
                    let finalTranscript = ""
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript + " "
                        }
                    }

                    if (finalTranscript) {
                        setState(prev => ({ ...prev, currentDraft: prev.currentDraft + finalTranscript }))
                    }
                }

                recognition.onerror = (event: any) => {
                    console.error("Speech Recognition Error", event.error)
                    if (event.error === 'not-allowed') {
                        toast.error("Microphone Access Denied", {
                            description: "Please check your browser permissions."
                        })
                        stopRecording()
                    }
                }

                recognition.onend = () => {
                    setState(prev => ({ ...prev, isRecording: false }))
                }

                recognitionRef.current = recognition
                recognition.start()

            } else {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
                mediaRecorderRef.current = new MediaRecorder(stream)

                mediaRecorderRef.current.onstop = () => {
                    const mockTranscripts = [
                        "I want to focus on salary negotiation strategies.",
                        "I feel I deserve a raise based on my recent performance.",
                        "My target is a 15% increase effectively immediately.",
                    ]
                    const userMessage = mockTranscripts[Math.floor(Math.random() * mockTranscripts.length)]
                    stream.getTracks().forEach((track) => track.stop())
                    setState(prev => ({ ...prev, currentDraft: prev.currentDraft + " " + userMessage }))
                }

                mediaRecorderRef.current.start()
                setState(prev => ({ ...prev, isRecording: true }))
            }
        } catch (error) {
            console.error("Error accessing microphone:", error)
            toast.error("Microphone Error", {
                description: "Unable to access microphone. Please check permissions."
            })
        }
    }

    const handleSend = async () => {
        const message = state.currentDraft.trim()
        if (!message) return

        stopRecording()

        setState((prev) => ({
            ...prev,
            transcript: [...prev.transcript, { role: "user", content: message }],
            currentDraft: "",
            isProcessing: true,
        }))

        try {
            const response = await fetch(`/api/session/${sessionId}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            })

            if (!response.ok) throw new Error("API request failed")

            const data = await response.json()
            const aiResponse = data.follow_up

            setState((prev) => ({
                ...prev,
                transcript: [...prev.transcript, { role: "assistant", content: aiResponse }],
                turnCount: prev.turnCount + 1,
                isProcessing: false,
            }))

            speakText(aiResponse)

            if (state.sessionData) {
                const updated = {
                    ...state.sessionData,
                    transcript: [...state.sessionData.transcript,
                    { role: "user", content: message },
                    { role: "assistant", content: aiResponse }
                    ]
                }
                localStorage.setItem(`session_${sessionId}`, JSON.stringify(updated))
            }

        } catch (error) {
            console.error("Conversation Error:", error)
            setState((prev) => ({ ...prev, isProcessing: false }))

            toast.error("Connection Error", {
                description: "Failed to get response from AI Coach. Is the server running?"
            })
        }
    }

    const handleEndConversation = async () => {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel()
        }
        try {
            await fetch(`/api/session/${sessionId}/complete`, { method: "POST" })
        } catch (e) {
            console.error("Error completing session", e)
        }
        navigate(`/report/${sessionId}`)
    }

    // Get the latest message for captioning
    const lastMessage = state.transcript.length > 0 ? state.transcript[state.transcript.length - 1] : null

    return (
        <div className="min-h-screen bg-slate-950 text-white relative overflow-hidden flex flex-col font-sans">
            {/* Animated Background */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-[20%] left-[20%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px] animate-pulse duration-[10s]" />
                <div className="absolute bottom-[20%] right-[20%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] animate-pulse duration-[8s]" />
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay"></div>
            </div>

            {/* Header */}
            <header className="relative z-50 px-6 py-6 flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => navigate("/practice")}
                        className="text-white hover:bg-white/10 rounded-full w-10 h-10 border border-white/5 backdrop-blur-md"
                    >
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div className="bg-white/5 backdrop-blur-xl px-4 py-2 rounded-full border border-white/10 flex items-center gap-3 shadow-lg">
                        <div className={`w-2 h-2 rounded-full ${state.isRecording ? 'bg-red-500 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]'}`} />
                        <span className="text-sm font-semibold tracking-wide text-slate-200">
                            {state.isRecording ? "Listening..." : isAiSpeaking ? "AI Speaking" : "Connected"}
                        </span>
                        <div className="w-px h-4 bg-white/10" />
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span className="text-sm text-slate-400 font-mono tracking-wider">{formatTime(state.elapsedSeconds)}</span>
                    </div>
                </div>

                <div className="flex gap-3">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setState(prev => ({ ...prev, showTranscript: true }))}
                        className="text-slate-400 hover:text-white rounded-full bg-white/5 border border-white/10 w-10 h-10 backdrop-blur-md"
                    >
                        <History className="h-5 w-5" />
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleEndConversation}
                        className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-full px-6 font-semibold backdrop-blur-md transition-all duration-300"
                    >
                        End Session
                    </Button>
                </div>
            </header>

            {/* Main Content - Voice Sphere */}
            <main className="flex-1 flex flex-col items-center justify-center relative z-10 p-6 min-h-[600px]">

                {/* The Sphere Container */}
                <div className="relative mb-16 group">
                    {/* Ring 1 - Outer Pulse */}
                    <motion.div
                        animate={{
                            scale: isAiSpeaking ? [1, 1.4, 1] : state.isProcessing ? [1, 1.1, 1] : 1,
                            opacity: isAiSpeaking ? [0.1, 0.2, 0.1] : 0.05
                        }}
                        transition={{ duration: isAiSpeaking ? 2 : 3, repeat: Infinity, ease: "easeInOut" }}
                        className={`absolute inset-0 rounded-full blur-2xl transition-colors duration-1000 ${state.isRecording ? 'bg-red-500/30' : 'bg-blue-500/20'}`}
                    />

                    {/* Ring 2 - Inner Pulse */}
                    <motion.div
                        animate={{
                            scale: isAiSpeaking ? [1, 1.15, 1] : 1,
                            borderColor: state.isRecording ? "rgba(239, 68, 68, 0.4)" : "rgba(59, 130, 246, 0.2)"
                        }}
                        transition={{ duration: 0.5 }}
                        className="absolute -inset-6 border border-white/5 rounded-full backdrop-blur-[1px]"
                    />

                    {/* Core Sphere */}
                    <motion.div
                        animate={{
                            scale: isAiSpeaking ? [1, 1.05, 1] : 1,
                            background: state.isRecording
                                ? "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
                                : isAiSpeaking
                                    ? "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)"
                                    : "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
                        }}
                        className={`w-48 h-48 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex items-center justify-center relative overflow-hidden transition-all duration-500 border border-white/10`}
                    >
                        {/* Internal Shine/Reflection */}
                        <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-white/20 via-transparent to-transparent rounded-full" />
                        <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-black/40 to-transparent rounded-full" />

                        {/* Icon */}
                        <div className="relative z-10 transition-transform duration-300">
                            {state.isRecording ? (
                                <Mic className="w-16 h-16 text-white drop-shadow-[0_4px_8px_rgba(0,0,0,0.3)]" />
                            ) : isAiSpeaking ? (
                                <Volume2 className="w-16 h-16 text-white drop-shadow-[0_4px_8px_rgba(0,0,0,0.3)] animate-pulse" />
                            ) : state.isProcessing ? (
                                <Sparkles className="w-16 h-16 text-blue-200 drop-shadow-[0_4px_8px_rgba(0,0,0,0.3)] animate-spin-slow" />
                            ) : (
                                <Bot className="w-16 h-16 text-slate-400 drop-shadow-[0_4px_8px_rgba(0,0,0,0.3)]" />
                            )}
                        </div>
                    </motion.div>
                </div>

                {/* Subtitles / Captions */}
                <div className="max-w-4xl w-full text-center px-4 min-h-[140px] flex flex-col items-center justify-start relative z-20">
                    <AnimatePresence mode="wait">
                        {state.currentDraft ? (
                            <motion.div
                                key="draft"
                                initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
                                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                                exit={{ opacity: 0, y: -20, filter: "blur(10px)" }}
                                className="relative"
                            >
                                <p className="text-3xl md:text-4xl font-semibold text-white/90 leading-tight tracking-tight">
                                    "{state.currentDraft}"
                                    <span className="inline-block w-3 h-8 bg-blue-500/80 rounded-full animate-pulse ml-2 align-middle shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                                </p>
                                <p className="text-sm text-slate-400 mt-4 font-medium uppercase tracking-widest">Listening...</p>
                            </motion.div>
                        ) : lastMessage ? (
                            <motion.div
                                key="last-msg"
                                initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
                                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                                exit={{ opacity: 0, y: -20, filter: "blur(10px)" }}
                                className="relative"
                            >
                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest mb-6 border ${lastMessage.role === 'assistant'
                                    ? 'bg-blue-500/10 border-blue-500/20 text-blue-400'
                                    : 'bg-slate-700/30 border-slate-600/30 text-slate-400'
                                    }`}>
                                    {lastMessage.role === 'assistant' ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                                    {lastMessage.role === 'assistant' ? 'AI Coach' : 'You'}
                                </div>

                                <p className={`text-2xl md:text-4xl font-medium leading-tight tracking-tight ${lastMessage.role === 'assistant'
                                    ? 'text-transparent bg-clip-text bg-gradient-to-r from-blue-100 via-blue-50 to-white drop-shadow-sm'
                                    : 'text-slate-300'
                                    }`}>
                                    "{lastMessage.content}"
                                </p>
                            </motion.div>
                        ) : (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-center"
                            >
                                <p className="text-slate-500 text-xl font-medium">Tap the microphone to start the conversation</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

            </main>

            {/* Bottom Controls */}
            <div className="relative z-50 p-10 flex justify-center items-center gap-10">

                {/* Cancel Button (Hidden but usable for layout balance if needed, or keeping simplified) */}
                <div className="w-20 hidden md:block" />

                <div className="relative group">
                    {/* Ripple Effect */}
                    {state.isRecording && (
                        <div className="absolute inset-0 rounded-full bg-red-500/30 animate-ping duration-1000" />
                    )}

                    <Button
                        onClick={state.isRecording ? stopRecording : startRecording}
                        disabled={isAiSpeaking || state.isProcessing}
                        className={`h-24 w-24 rounded-full shadow-2xl transition-all duration-300 relative z-10 border-4 border-slate-900 ${state.isRecording
                            ? "bg-gradient-to-br from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 scale-110 shadow-[0_0_40px_rgba(239,68,68,0.4)]"
                            : "bg-white text-slate-900 hover:bg-slate-100 hover:scale-105 shadow-[0_0_30px_rgba(255,255,255,0.1)]"
                            }`}
                    >
                        {state.isRecording ? (
                            <Square className="w-10 h-10 fill-current text-white" />
                        ) : (
                            <Mic className="w-10 h-10 text-slate-900" />
                        )}
                    </Button>
                </div>

                <div className="w-20 flex justify-start">
                    <AnimatePresence>
                        {state.currentDraft && !state.isProcessing && (
                            <motion.div
                                initial={{ scale: 0, opacity: 0, x: -20 }}
                                animate={{ scale: 1, opacity: 1, x: 0 }}
                                exit={{ scale: 0, opacity: 0, x: -20 }}
                            >
                                <Button
                                    onClick={handleSend}
                                    className="h-16 w-16 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-xl shadow-blue-500/20 border border-white/10"
                                >
                                    <Send className="w-7 h-7 ml-0.5" />
                                </Button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Transcript Drawer / Panel */}
            <AnimatePresence>
                {state.showTranscript && (
                    <div className="fixed inset-0 z-[100] flex justify-end">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setState(prev => ({ ...prev, showTranscript: false }))}
                            className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ x: "100%" }}
                            animate={{ x: 0 }}
                            exit={{ x: "100%" }}
                            transition={{ type: "spring", damping: 30, stiffness: 300 }}
                            className="relative w-full max-w-lg h-full bg-slate-900/90 backdrop-blur-xl border-l border-white/10 shadow-2xl flex flex-col"
                        >
                            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
                                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                        <History className="w-5 h-5 text-blue-400" />
                                    </div>
                                    Session Transcript
                                </h3>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => setState(prev => ({ ...prev, showTranscript: false }))}
                                    className="hover:bg-white/10 rounded-full"
                                >
                                    <X className="w-5 h-5 text-slate-400" />
                                </Button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                                {state.transcript.map((msg, idx) => (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.05 * idx }}
                                        key={idx}
                                        className={`flex flex-col gap-2 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                                    >
                                        <div className={`flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest ${msg.role === 'user' ? 'text-slate-500 flex-row-reverse' : 'text-blue-400'}`}>
                                            {msg.role === 'user' ? (
                                                <>You <div className="w-6 h-[1px] bg-slate-700"></div></>
                                            ) : (
                                                <>AI Coach <div className="w-6 h-[1px] bg-blue-900"></div></>
                                            )}
                                        </div>

                                        <div className={`p-5 rounded-2xl max-w-[85%] text-sm leading-relaxed backdrop-blur-md border shadow-lg ${msg.role === 'user'
                                            ? 'bg-white/10 border-white/5 text-slate-100 rounded-tr-sm'
                                            : 'bg-gradient-to-br from-blue-600/20 to-indigo-600/20 border-blue-500/20 text-blue-50 rounded-tl-sm'
                                            }`}>
                                            {msg.content}
                                        </div>
                                    </motion.div>
                                ))}
                                <div ref={transcriptEndRef} />
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}


