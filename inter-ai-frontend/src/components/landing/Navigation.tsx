import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Menu, X, ChevronRight, User, LogOut } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { supabase } from '../../lib/supabase';

const Navigation = () => {
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 50);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Check auth state
    useEffect(() => {
        const checkAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            setUser(session?.user ?? null);
            setLoading(false);
        };

        checkAuth();

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null);
        });

        return () => subscription.unsubscribe();
    }, []);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        setUser(null);
        setIsMobileMenuOpen(false);
        navigate('/login');
    };

    const navItems = [
        { name: 'Features', href: '#features', page: '/' },
        { name: 'How It Works', href: '#how-it-works', page: '/' },
        { name: 'Practice', href: '/practice', page: '/practice' },
        { name: 'History', href: '/history', page: '/history' },
    ];

    const handleNavClick = (item: { name: string, href: string, page: string }) => {
        setIsMobileMenuOpen(false);

        if (item.href.startsWith('/')) {
            navigate(item.href);
            return;
        }

        // Handle hash links
        if (location.pathname !== '/') {
            navigate('/', { state: { scrollTo: item.href.substring(1) } });
        } else {
            const element = document.querySelector(item.href);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }
    };

    // Handle scroll after navigation from another page
    useEffect(() => {
        if (location.pathname === '/' && location.state && (location.state as any).scrollTo) {
            const id = (location.state as any).scrollTo;
            setTimeout(() => {
                const element = document.getElementById(id);
                if (element) element.scrollIntoView({ behavior: 'smooth' });
                // clear state
                window.history.replaceState({}, document.title);
            }, 100);
        }
    }, [location]);

    return (
        <motion.nav
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b ${isScrolled || location.pathname !== '/' ? 'bg-slate-950/80 backdrop-blur-xl border-white/5 py-3' : 'bg-transparent border-transparent py-6'}`}
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="container mx-auto px-6">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <motion.div
                        className="flex items-center gap-2 cursor-pointer group"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => navigate('/')}
                    >
                        <div className="relative w-10 h-10">
                            <div className="absolute inset-0 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-xl rotate-6 group-hover:rotate-12 transition-transform duration-300 opacity-80" />
                            <div className="absolute inset-0 bg-slate-900 rounded-xl border border-white/10 flex items-center justify-center">
                                <Sparkles className="w-5 h-5 text-blue-400" />
                            </div>
                        </div>
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                            CoAct<span className="text-blue-500">.AI</span>
                        </span>
                    </motion.div>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-8">
                        {navItems.map((item, index) => (
                            <motion.button
                                key={item.name}
                                onClick={() => handleNavClick(item)}
                                className={`text-sm font-medium transition-colors relative group ${location.pathname === item.page ? 'text-white' : 'text-slate-400 hover:text-white'}`}
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                            >
                                {item.name}
                                <span className={`absolute -bottom-1 left-0 h-px bg-blue-500 transition-all duration-300 ${location.pathname === item.page ? 'w-full' : 'w-0 group-hover:w-full'}`} />
                            </motion.button>
                        ))}
                    </div>

                    {/* Auth Buttons */}
                    <div className="hidden md:flex items-center gap-4">
                        {!loading && (
                            user ? (
                                <>
                                    <motion.button
                                        className="flex items-center gap-2 text-slate-300 hover:text-white font-medium text-sm transition-colors"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        onClick={() => navigate('/profile')}
                                    >
                                        <User className="w-4 h-4" />
                                        Profile
                                    </motion.button>
                                    <motion.button
                                        className="flex items-center gap-2 text-red-400 hover:text-red-300 font-medium text-sm transition-colors"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        onClick={handleLogout}
                                    >
                                        <LogOut className="w-4 h-4" />
                                        Logout
                                    </motion.button>
                                </>
                            ) : (
                                <>
                                    <motion.button
                                        className="text-slate-300 hover:text-white font-medium text-sm transition-colors"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.2 }}
                                        onClick={() => navigate('/login')}
                                    >
                                        Sign In
                                    </motion.button>
                                    <motion.button
                                        className="bg-white text-slate-950 px-5 py-2.5 rounded-full text-sm font-bold hover:bg-blue-50 transition-colors flex items-center gap-2 shadow-[0_0_20px_-5px_rgba(255,255,255,0.3)]"
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: 0.3 }}
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => navigate('/signup')}
                                    >
                                        Get Started <ChevronRight className="w-4 h-4" />
                                    </motion.button>
                                </>
                            )
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <motion.button
                        className="md:hidden text-white p-2"
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        whileTap={{ scale: 0.9 }}
                    >
                        {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                    </motion.button>
                </div>

                {/* Mobile Menu */}
                <AnimatePresence>
                    {isMobileMenuOpen && (
                        <motion.div
                            className="md:hidden border-t border-white/10 mt-4 bg-slate-900/95 backdrop-blur-xl rounded-2xl overflow-hidden"
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                        >
                            <div className="p-4 space-y-2">
                                {navItems.map((item) => (
                                    <button
                                        key={item.name}
                                        onClick={() => handleNavClick(item)}
                                        className={`block w-full text-left px-4 py-3 rounded-xl font-medium transition-colors ${location.pathname === item.page ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
                                    >
                                        {item.name}
                                    </button>
                                ))}
                                <div className="pt-4 flex flex-col gap-3">
                                    {user ? (
                                        <>
                                            <button
                                                onClick={() => {
                                                    navigate('/profile');
                                                    setIsMobileMenuOpen(false);
                                                }}
                                                className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl font-medium text-white bg-purple-600"
                                            >
                                                <User className="w-4 h-4" /> Profile
                                            </button>
                                            <button
                                                onClick={handleLogout}
                                                className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl font-medium text-red-400 hover:bg-red-500/20"
                                            >
                                                <LogOut className="w-4 h-4" /> Logout
                                            </button>
                                        </>
                                    ) : (
                                        <>
                                            <button
                                                onClick={() => {
                                                    navigate('/login');
                                                    setIsMobileMenuOpen(false);
                                                }}
                                                className="block w-full text-center px-4 py-3 rounded-xl font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                                            >
                                                Sign In
                                            </button>
                                            <button
                                                onClick={() => {
                                                    navigate('/signup');
                                                    setIsMobileMenuOpen(false);
                                                }}
                                                className="w-full bg-blue-600 text-white px-4 py-3 rounded-xl font-bold flex items-center justify-center gap-2"
                                            >
                                                Get Started <ChevronRight className="w-4 h-4" />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.nav>
    );
};

export default Navigation;
