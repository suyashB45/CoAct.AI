import Navigation from '../components/landing/Navigation'
import HeroSection from '../components/landing/HeroSection'
import FeaturesSection from '../components/landing/FeaturesSection'

function Home() {
    return (
        <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-purple-500/30">
            <Navigation />
            <main>
                <HeroSection />
                <FeaturesSection />
            </main>
        </div>
    )
}

export default Home
