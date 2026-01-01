import { motion } from 'framer-motion';
import { Star, Quote } from 'lucide-react';

const TestimonialsSection = () => {
    const testimonials = [
        {
            name: "Sarah Jenkins",
            role: "Product Manager",
            image: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
            quote: "CoAct AI helped me prepare for a difficult salary negotiation. I practiced the conversation 5 times with the AI, and when the real meeting came, I was calm, collected, and got the raise I wanted!",
            rating: 5
        },
        {
            name: "David Chen",
            role: "Sales Director",
            image: "https://api.dicebear.com/7.x/avataaars/svg?seed=David",
            quote: "The 'tough client' simulator is scarily realistic. It pushed back exactly like my real customers do. My team's closing rate has improved by 20% since we started using this for training.",
            rating: 5
        },
        {
            name: "Elena Rodriguez",
            role: "HR Specialist",
            image: "https://api.dicebear.com/7.x/avataaars/svg?seed=Elena",
            quote: "I use this to practice delivering constructive feedback. The 'Radical Candor' framework tracking is a game changer. It keeps me honest and clear without being aggressive.",
            rating: 5
        }
    ];

    return (
        <section className="relative py-24 overflow-hidden bg-slate-900">
            <div className="container mx-auto px-6 relative z-10">
                <div className="text-center mb-16">
                    <motion.h2
                        className="text-4xl md:text-5xl font-bold text-white mb-6"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        Loved by <span className="text-ultra-gradient">Professionals</span>
                    </motion.h2>
                    <motion.p
                        className="text-xl text-slate-400"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.1 }}
                    >
                        See how CoAct AI is transforming careers and communication.
                    </motion.p>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    {testimonials.map((t, index) => (
                        <motion.div
                            key={index}
                            className="testimonial-card group"
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <div className="flex items-center gap-1 mb-6 text-yellow-500">
                                {[...Array(t.rating)].map((_, i) => (
                                    <Star key={i} className="w-5 h-5 fill-current" />
                                ))}
                            </div>

                            <p className="text-slate-700 text-lg mb-8 italic relative z-10 leading-relaxed">
                                "{t.quote}"
                            </p>

                            <div className="flex items-center gap-4">
                                <img
                                    src={t.image}
                                    alt={t.name}
                                    className="w-12 h-12 rounded-full border-2 border-purple-100"
                                />
                                <div>
                                    <h4 className="font-bold text-slate-900">{t.name}</h4>
                                    <div className="text-sm text-slate-500">{t.role}</div>
                                </div>
                            </div>

                            <Quote className="absolute top-6 right-6 w-12 h-12 text-purple-100 -z-0 transform group-hover:scale-110 transition-transform duration-300" />
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default TestimonialsSection;
