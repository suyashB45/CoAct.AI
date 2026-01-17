#!/usr/bin/env python3
"""
Test script for enhanced reporting system
"""

import json
import os
from cli_report import generate_report, analyze_full_report_data

# Sample transcript for testing
sample_transcript = [
    {"role": "user", "content": "I'm struggling with giving feedback to my team member who's been underperforming."},
    {"role": "assistant", "content": "That sounds challenging. What specific behaviors have you noticed that concern you?"},
    {"role": "user", "content": "They miss deadlines frequently and their work quality has declined. I don't want to demotivate them."},
    {"role": "assistant", "content": "I understand your concern about maintaining their motivation. What do you think might be contributing to these changes in their performance?"},
    {"role": "user", "content": "Maybe they're overwhelmed? Or perhaps they don't understand the expectations clearly."},
    {"role": "assistant", "content": "Those are thoughtful possibilities. How might you explore which of these factors is at play?"},
    {"role": "user", "content": "I could have a one-on-one conversation with them to understand their perspective."},
    {"role": "assistant", "content": "That sounds like a good approach. What would you want to accomplish in that conversation?"}
]

def test_enhanced_reports():
    """Test both learning and assessment mode reports with enhanced features"""
    
    print("🧪 Testing Enhanced Reporting System...")
    
    # Test Assessment Mode
    print("\n1️⃣ Testing Assessment Mode...")
    try:
        generate_report(
            transcript=sample_transcript,
            role="Manager",
            ai_role="Team Member",
            scenario="Performance Management Conversation",
            framework="GROW",
            filename="reports/test_assessment_enhanced.pdf",
            mode="evaluation"
        )
        print("✅ Assessment mode report generated successfully")
    except Exception as e:
        print(f"❌ Assessment mode failed: {e}")
    
    # Test Learning Mode
    print("\n2️⃣ Testing Learning Mode...")
    try:
        generate_report(
            transcript=sample_transcript,
            role="Manager",
            ai_role="Team Member", 
            scenario="Performance Management Conversation",
            framework="GROW",
            filename="reports/test_learning_enhanced.pdf",
            mode="coaching"
        )
        print("✅ Learning mode report generated successfully")
    except Exception as e:
        print(f"❌ Learning mode failed: {e}")
    
    # Test data generation separately
    print("\n3️⃣ Testing Enhanced Data Generation...")
    try:
        assessment_data = analyze_full_report_data(
            transcript=sample_transcript,
            role="Manager",
            ai_role="Team Member",
            scenario="Performance Management Conversation", 
            framework="GROW",
            mode="evaluation"
        )
        
        learning_data = analyze_full_report_data(
            transcript=sample_transcript,
            role="Manager", 
            ai_role="Team Member",
            scenario="Performance Management Conversation",
            framework="GROW", 
            mode="coaching"
        )
        
        print("✅ Enhanced data generation successful")
        print(f"Assessment data keys: {list(assessment_data.keys())}")
        print(f"Learning data keys: {list(learning_data.keys())}")
        
        # Save sample data for inspection
        with open("reports/sample_assessment_data.json", "w") as f:
            json.dump(assessment_data, f, indent=2)
        with open("reports/sample_learning_data.json", "w") as f:
            json.dump(learning_data, f, indent=2)
            
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
    
    print("\n🎉 Enhanced reporting test completed!")

if __name__ == "__main__":
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    test_enhanced_reports()