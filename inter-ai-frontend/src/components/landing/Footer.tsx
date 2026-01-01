import { motion } from 'framer-motion';
import { Sparkles, Twitter, Github, Linkedin, Mail } from 'lucide-react';
import { Link } from 'react-router-dom';

const Footer = () => {
    return (
        <footer className="bg-slate-950 border-t border-slate-800 pt-16 pb-8 relative overflow-hidden">
            <div className="container mx-auto px-6 relative z-10">
                <div className="grid md:grid-cols-4 gap-12 mb-12">
                    {/* Brand */}
                    <div className="col-span-1 md:col-span-2">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                                <Sparkles className="w-6 h-6 text-white" />
                            </div>
                            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                                CoAct<span className="text-blue-500">.AI</span>
                            </span>
                        </div>
                        <p className="text-slate-400 max-w-sm mb-6 leading-relaxed">
                            The advanced AI coaching platform designed to help you master communication,
                            build confidence, and achieve your professional goals through realistic practice.
                        </p>
                        <div className="flex gap-4">
                            {[Twitter, Github, Linkedin, Mail].map((Icon, i) => (
                                <motion.a
                                    key={i}
                                    href="#"
                                    className="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center text-slate-400 hover:bg-blue-600 hover:text-white transition-all duration-300"
                                    whileHover={{ y: -3 }}
                                >
                                    <Icon className="w-5 h-5" />
                                </motion.a>
                            ))}
                        </div>
                    </div>

                    {/* Links */}
                    <div>
                        <h4 className="text-white font-bold mb-6">Platform</h4>
                        <ul className="space-y-4">
                            <li><Link to="/practice" className="text-slate-400 hover:text-blue-400 transition-colors">Practice Scenarios</Link></li>
                            <li><Link to="/history" className="text-slate-400 hover:text-blue-400 transition-colors">Your History</Link></li>
                            <li><a href="#features" className="text-slate-400 hover:text-blue-400 transition-colors">Features</a></li>
                            <li><a href="#how-it-works" className="text-slate-400 hover:text-blue-400 transition-colors">How It Works</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-white font-bold mb-6">Legal</h4>
                        <ul className="space-y-4">
                            <li><a href="#" className="text-slate-400 hover:text-blue-400 transition-colors">Privacy Policy</a></li>
                            <li><a href="#" className="text-slate-400 hover:text-blue-400 transition-colors">Terms of Service</a></li>
                            <li><a href="#" className="text-slate-400 hover:text-blue-400 transition-colors">Cookie Policy</a></li>
                            <li><a href="#" className="text-slate-400 hover:text-blue-400 transition-colors">Contact Support</a></li>
                        </ul>
                    </div>
                </div>

                <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-center md:text-left">
                    <p className="text-slate-500 text-sm">
                        © {new Date().getFullYear()} CoAct AI. All rights reserved.
                    </p>
                    <div className="flex gap-2 items-center text-slate-500 text-sm">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        System Operational
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
