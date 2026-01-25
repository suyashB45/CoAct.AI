import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { supabase } from '../lib/supabase';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const [loading, setLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const location = useLocation();

    useEffect(() => {
        let mounted = true;

        const checkAuth = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession();
                if (mounted) {
                    setIsAuthenticated(!!session);
                    // Only set loading to false if we have a session, otherwise wait for auth state change
                    // or set it after a short timeout? 
                    // actually, getSession is the source of truth for "restoring" persistence.
                    // If it returns null, we probably aren't logged in.
                    setLoading(false);
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                if (mounted) {
                    setIsAuthenticated(false);
                    setLoading(false);
                }
            }
        };

        checkAuth();

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (mounted) {
                setIsAuthenticated(!!session);
                setLoading(false);
            }
        });

        return () => {
            mounted = false;
            subscription.unsubscribe();
        };
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen hero-ultra-modern flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        // Redirect to login with the intended destination
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return <>{children}</>;
};

export default ProtectedRoute;
