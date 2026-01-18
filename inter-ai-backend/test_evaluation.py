from cli_report import analyze_full_report_data, generate_report

# Mock Transcripts
TRANSCRIPT_COACHING = [
    {"role": "assistant", "content": "Hi there. I noticed you've been a bit quiet lately. Is everything okay?"},
    {"role": "user", "content": "Yeah, I'm fine. Just tired."},
    {"role": "assistant", "content": "I get that. But your sales numbers have dropped significantly. What's going on?"},
    {"role": "user", "content": "Look, traffic has been slow. It's not my fault."},
    {"role": "assistant", "content": "I'm not blaming you. I want to help. What can we do to get you back on track?"},
    {"role": "user", "content": "Maybe I could use some help on the floor during peak hours."}
]

TRANSCRIPT_SALES = [
    {"role": "assistant", "content": "Welcome! Are you looking for anything specific today?"},
    {"role": "user", "content": "I'm looking at this laptop, but $2000 is way over my budget."},
    {"role": "assistant", "content": "I understand. What kind of work do you do?"},
    {"role": "user", "content": "I'm a graphic designer, so I need performance."},
    {"role": "assistant", "content": "Perfect. This model has the M3 chip which saves you hours in rendering time. Does that sound valuable?"},
    {"role": "user", "content": "Yes, time is money. But can you do any better on the price?"},
    {"role": "assistant", "content": "I can't drop the price, but I can include a 3-year warranty worth $300."}
]

def test_scenario(name, transcript, role, ai_role, scenario, scenario_type):
    print(f"\n--- Testing Scenario: {name} ({scenario_type}) ---")
    try:
        report = analyze_full_report_data(
            transcript=transcript,
            role=role,
            ai_role=ai_role,
            scenario=scenario,
            framework="GROW",
            mode="evaluation", 
            scenario_type=scenario_type
        )
        
        print(f"Outcome: {report.get('meta', {}).get('outcome_status')}")
        print("Metrics (Pulse):")
        for m in report.get("layer_1_pulse", []):
            print(f"  - {m['metric']}: {m['score']}")
            
        # Generate PDF to test parsing logic
        filename = f"test_report_{scenario_type}.pdf"
        generate_report(
            transcript=transcript,
            role=role,
            ai_role=ai_role,
            scenario=scenario,
            framework="GROW",
            mode="evaluation",
            precomputed_data=report,
            scenario_type=scenario_type,
            filename=filename
        )
        print(f"PDF Generated: {filename}")
        
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run Tests
print("Starting Evaluation Test...")

# 1. Coaching
test_scenario(
    "Coaching Effectiveness", 
TRANSCRIPT_COACHING, 
    "Store Manager", 
    "Sales Associate", 
    "Manager coaching staff on performance drop.",
    "coaching"
)

# 2. Negotiation
test_scenario(
    "Sales Negotiation", 
    TRANSCRIPT_SALES, 
    "Salesperson", 
    "Customer", 
    "Customer wants a discount on laptop.",
    "negotiation"
)

# 3. Reflection (Learning) - expecting NO scores
test_scenario(
    "Learning Reflection", 
    TRANSCRIPT_COACHING, # using same transcript for simplicity
    "Retail Staff", 
    "Coach Alex", 
    "Reflection on the coaching session.",
    "reflection"
)
