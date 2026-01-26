;
import { motion } from 'framer-motion';
import { ArrowRight, Star, Users, Zap } from 'lucide-react';
import Scene3D from './Scene3D';

const HeroSection = () => {
    // Generate random particles
    const particles = Array.from({ length: 20 }, (_, i) => ({
        id: i,
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        delay: `${Math.random() * 5}s`,
        size: 3 + Math.random() * 4,
    }));

    return (
        <section className="hero-ultra-modern section-lg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', paddingTop: '2rem' }}>

            {/* Floating Particles */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {particles.map((p) => (
                    <div
                        key={p.id}
                        className="particle"
                        style={{
                            left: p.left,
                            top: p.top,
                            width: `${p.size}px`,
                            height: `${p.size}px`,
                            animationDelay: p.delay,
                        }}
                    />
                ))}
            </div>

            {/* Animated Background Elements */}
            <div className="absolute inset-0 overflow-hidden">
                <motion.div
                    className="absolute morph-blob"
                    style={{ top: '5rem', left: '2.5rem', width: '18rem', height: '18rem', background: 'rgba(139, 92, 246, 0.15)', filter: 'blur(60px)' }}
                    animate={{
                        x: [0, 100, 0],
                        y: [0, -50, 0],
                    }}
                    transition={{
                        duration: 20,
                        repeat: Infinity,
                        ease: "linear"
                    }}
                />
                <motion.div
                    className="absolute morph-blob"
                    style={{ top: '10rem', right: '5rem', width: '22rem', height: '22rem', background: 'rgba(236, 72, 153, 0.15)', filter: 'blur(70px)' }}
                    animate={{
                        x: [0, -80, 0],
                        y: [0, 60, 0],
                    }}
                    transition={{
                        duration: 25,
                        repeat: Infinity,
                        ease: "linear"
                    }}
                />
                <motion.div
                    className="absolute morph-blob"
                    style={{ bottom: '5rem', left: '25%', width: '16rem', height: '16rem', background: 'rgba(59, 130, 246, 0.12)', filter: 'blur(50px)' }}
                    animate={{
                        x: [0, 60, 0],
                        y: [0, -40, 0],
                    }}
                    transition={{
                        duration: 18,
                        repeat: Infinity,
                        ease: "linear"
                    }}
                />
            </div>

            <div className="container" style={{ position: 'relative', zIndex: 1 }}>
                <div className="grid md:grid-cols-2 gap-12 items-center">
                    {/* Left Content */}
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
                        className="text-center lg:text-left order-2 lg:order-1"
                    >
                        {/* Badge */}
                        <motion.div
                            className="inline-flex items-center gap-2 px-4 py-2 btn-glass mb-6 animate-pulse-glow"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <Star className="w-4 h-4 text-purple-400 fill-purple-400" />
                            <span className="text-sm font-medium">AI-Powered Coaching Platform</span>
                        </motion.div>

                        {/* Headline */}
                        <motion.h1
                            className="text-6xl md:text-7xl lg:text-8xl font-bold mb-6 leading-tight"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <span className="text-white block">Transform Your</span>
                            <span className="block text-gradient-animate text-glow">Life with AI</span>
                        </motion.h1>

                        {/* Subheadline */}
                        <motion.p
                            className="text-xl text-slate-300 mb-10 leading-relaxed max-w-2xl mx-auto lg:mx-0"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            Experience personalized AI coaching that adapts to your unique goals,
                            providing real-time guidance and insights to accelerate your personal and professional growth.
                        </motion.p>

                        {/* CTA Buttons */}
                        <motion.div
                            className="flex flex-col sm:flex-row gap-4 mb-12 justify-center lg:justify-start"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                        >
                            <motion.button
                                className="btn-ultra-modern text-lg px-8 py-4 w-full sm:w-auto flex items-center justify-center"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => window.location.href = 'mailto:team@coact-ai.com'}
                            >
                                Contact Sales
                                <ArrowRight className="w-5 h-5 ml-2" />
                            </motion.button>
                            <motion.button
                                className="btn-glass text-lg px-8 py-4 w-full sm:w-auto"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                            >
                                See How It Works
                            </motion.button>
                        </motion.div>

                        {/* Trust Indicators */}
                        <motion.div
                            className="flex flex-col sm:flex-row items-center gap-8 text-slate-400 justify-center lg:justify-start"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.6 }}
                        >
                            <div className="flex items-center gap-2">
                                <Users className="w-5 h-5 text-blue-400" />
                                <span className="text-sm font-medium">10,000+ Users</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Zap className="w-5 h-5 text-purple-400" />
                                <span className="text-sm font-medium">99.9% Uptime</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                                <span className="text-sm font-medium">4.9/5 Rating</span>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* Right Content - 3D Scene */}
                    <motion.div
                        className="relative hidden md:block"
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, delay: 0.3, ease: [0.4, 0, 0.2, 1] }}
                    >
                        <div className="relative" style={{ width: '100%', height: '560px' }}>
                            <Scene3D />

                            {/* Floating Elements */}
                            <motion.div
                                className="absolute"
                                style={{ top: '1rem', right: '1rem', background: 'rgba(139,92,246,0.2)', backdropFilter: 'blur(6px)', border: '1px solid rgba(139,92,246,0.3)', borderRadius: '1rem', padding: '0.75rem' }}
                                animate={{ y: [0, -10, 0] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            >
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">95%</div>
                                    <div className="text-sm text-slate-300">Success Rate</div>
                                </div>
                            </motion.div>

                            <motion.div
                                className="absolute"
                                style={{ bottom: '1rem', left: '1rem', background: 'rgba(59,130,246,0.2)', backdropFilter: 'blur(6px)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '1rem', padding: '0.75rem' }}
                                animate={{ y: [0, 10, 0] }}
                                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            >
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">24/7</div>
                                    <div className="text-sm text-slate-300">AI Support</div>
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Scroll Indicator */}
            <motion.div
                className="absolute bottom-8 left-1/2 transform -translate-x-1/2 hidden md:block"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1, duration: 0.8 }}
            >
                <motion.div
                    className="w-6 h-10 border-2 border-slate-500 rounded-full flex justify-center"
                    animate={{ y: [0, 10, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                    <motion.div
                        className="w-1 h-3 bg-slate-400 rounded-full mt-2"
                        animate={{ y: [0, 12, 0] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    />
                </motion.div>
            </motion.div>
        </section>
    );
};

export default HeroSection;
