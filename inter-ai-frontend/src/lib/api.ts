// API configuration and helper functions for connecting to the backend

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || 'http://localhost:8000';

export interface SessionStartRequest {
    role: string;
    ai_role: string;
    scenario: string;
    framework?: string[];
}

export interface SessionStartResponse {
    session_id: string;
    summary: string;
    framework: string | string[];
}

export interface ChatRequest {
    message: string;
}

export interface ChatResponse {
    follow_up: string;
    framework_detected: string | null;
    framework_counts: Record<string, number>;
}

export interface SessionItem {
    id: string;
    created_at: string;
    role: string;
    ai_role: string;
    scenario: string;
    completed: boolean;
    fit_score: number;
}

export interface ReportData {
    meta: {
        fit_score: number;
        fit_label: string;
        potential_score: number;
        summary: string;
    };
    sidebar_data: {
        top_traits: string[];
        improvements: string[];
        motivators: string[];
        derailers: string[];
    };
    functional_cards: Array<{
        name: string;
        score: number;
        text: string;
    }>;
    behavioral_cards: Array<{
        name: string;
        score: number;
        text: string;
    }>;
    emotional_intelligence?: {
        overall_eq_score: number;
        eq_summary: string;
        metrics: Array<{
            label: string;
            score: number;
            feedback: string;
        }>;
    };
    chatberry_analysis: {
        analysis_text: string;
        metrics: Array<{ label: string; score: number }>;
    };
    coach_rewrite_card: {
        title: string;
        context: string;
        original_user_response: string;
        pro_rewrite: string;
        why_it_works: string;
    };
    learning_plan: {
        priority_focus: string;
        recommended_drill: string;
        suggested_reading: string;
    };
    qa_analysis?: Array<{
        question: string;
        answer: string;
        feedback: string;
        score: number;
    }>;
    transcript?: Array<{
        role: 'user' | 'assistant';
        content: string;
    }>;
    scenario?: string;
}

// API helper for starting a session
export async function startSession(data: SessionStartRequest): Promise<SessionStartResponse> {
    const response = await fetch(`${API_BASE_URL}/session/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || 'Failed to start session');
    }

    return response.json();
}

// API helper for sending chat messages
export async function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || 'Failed to send message');
    }

    return response.json();
}

// API helper for completing a session (generates PDF report)
export async function completeSession(sessionId: string): Promise<{ message: string; report_file: string }> {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || 'Failed to complete session');
    }

    return response.json();
}

// API helper for getting report data
export async function getReportData(sessionId: string): Promise<ReportData> {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/report_data`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || 'Failed to get report data');
    }

    return response.json();
}

// API helper for downloading report PDF
export function getReportPdfUrl(sessionId: string): string {
    return `${API_BASE_URL}/api/report/${sessionId}`;
}

// API helper for getting all sessions
export async function getSessions(): Promise<SessionItem[]> {
    const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || 'Failed to get sessions');
    }

    return response.json();
}

export { API_BASE_URL };
