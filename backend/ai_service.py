import os
import base64
import json
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
import requests
from dotenv import load_dotenv

load_dotenv()

class AIProctorService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")
        self.use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        self.confidence_threshold = float(os.getenv("ALERT_CONFIDENCE_THRESHOLD", "0.7"))

        if self.openai_api_key and not self.use_ollama:
            self.client = OpenAI(api_key=self.openai_api_key)

    def analyze_frame(self, webcam_image_base64: str, screen_image_base64: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze webcam and screen frames for cheating behavior
        Returns: (is_suspicious, analysis_data)
        """
        if self.use_ollama:
            return self._analyze_with_ollama(webcam_image_base64, screen_image_base64)
        elif self.openai_api_key:
            return self._analyze_with_openai(webcam_image_base64, screen_image_base64)
        else:
            raise ValueError("No AI service configured. Enable USE_OLLAMA=true or set OPENAI_API_KEY")

    def _analyze_with_openai(self, webcam_image_base64: str, screen_image_base64: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Use OpenAI GPT-4 Vision for analysis"""

        prompt = """You are an AI exam proctor. Analyze the webcam image for CLEAR and OBVIOUS signs of cheating during an online exam.

IMPORTANT: Students naturally look around, think, adjust posture, or glance away briefly. These are NORMAL behaviors. Only flag SUSTAINED or CLEAR violations.

Flag ONLY these CLEAR violations:
1. **Multiple people clearly visible** - Another person is helping or talking to the student
2. **Phone/device in use** - Student is clearly holding and looking at a phone or electronic device
3. **Reading from materials** - Student is obviously reading from books, notes, or papers for extended periods
4. **Student absent** - Student has left the frame entirely or is not at their desk
5. **Talking to someone** - Student is clearly speaking to someone off-camera

DO NOT FLAG these normal behaviors:
- Brief glances away (thinking, resting eyes)
- Looking up while thinking
- Natural eye movements
- Adjusting position or posture
- Occasional hand gestures
- Fidgeting or touching face briefly

Respond in JSON format:
{
    "is_suspicious": true/false,
    "confidence": 0.0-1.0,
    "detected_issues": ["issue1", "issue2"],
    "severity": 1-5,
    "description": "Brief description of what was detected",
    "alert_type": "looking_away" | "multiple_people" | "phone_detected" | "reading_from_material" | "suspicious_activity" | "none"
}

Be LENIENT. Only flag with high confidence (>0.85) when you are certain of a violation."""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{webcam_image_base64}"
                        }
                    }
                ]
            }
        ]

        # Add screen capture if available
        if screen_image_base64:
            screen_prompt = "\nAlso analyze the screen capture for suspicious activities like switching tabs, opening unauthorized applications, or searching for answers."
            messages[0]["content"].insert(1, {"type": "text", "text": screen_prompt})
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screen_image_base64}"
                }
            })

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )

            # Parse the JSON response
            content = response.choices[0].message.content

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            analysis = json.loads(content)

            is_suspicious = analysis.get("is_suspicious", False) and analysis.get("confidence", 0) >= self.confidence_threshold

            return is_suspicious, analysis

        except Exception as e:
            print(f"Error in OpenAI analysis: {e}")
            return False, {
                "error": str(e),
                "is_suspicious": False,
                "confidence": 0.0
            }

    def _analyze_with_ollama(self, webcam_image_base64: str, screen_image_base64: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Use Ollama (local Qwen3-VL 8B) for analysis"""

        prompt = """You are an expert AI exam proctor with computer vision capabilities. Carefully examine the webcam image and identify ONLY clear, obvious violations.

ANALYSIS INSTRUCTIONS:
1. First, describe what you see in the image (student position, surroundings, visible objects)
2. Compare observations against the violation criteria below
3. Only flag if you have HIGH CONFIDENCE (>0.85) of a clear violation

VIOLATIONS TO FLAG (must be CLEAR and OBVIOUS):

**CRITICAL (Severity 4-5):**
- Multiple people: Another person clearly visible in frame helping or talking to student
- Phone/device in use: Student actively holding and looking at phone, tablet, or electronic device
- Student absent: Empty chair, student not visible, or student has left the desk

**MODERATE (Severity 3-4):**
- Reading materials: Student clearly reading from books, papers, or notes for extended periods (>3 seconds)
- Talking to someone: Student's mouth clearly moving in conversation with someone off-camera

**MINOR (Severity 1-2):**
- Sustained looking away: Student looking away from screen for extended period (>5 seconds continuously)

NORMAL BEHAVIORS (DO NOT FLAG):
✓ Brief glances away (1-2 seconds) - thinking or resting eyes
✓ Looking up while thinking or concentrating
✓ Natural eye movements around the screen
✓ Adjusting posture, shifting in seat
✓ Hand gestures, touching face briefly
✓ Fidgeting with pen or hands
✓ Drinking water or brief breaks

OUTPUT FORMAT:
You must respond with ONLY valid JSON (no markdown, no explanation, no code blocks):

{
    "is_suspicious": false,
    "confidence": 0.95,
    "detected_issues": [],
    "severity": 1,
    "description": "Student sitting at desk, looking at screen, appears focused on exam. No violations detected.",
    "alert_type": "none"
}

FIELD SPECIFICATIONS:
- "is_suspicious": boolean - true ONLY if you are 85%+ confident of a violation
- "confidence": float 0.0-1.0 - your confidence level in the assessment
- "detected_issues": array of strings - specific issues found, empty if none
- "severity": integer 1-5 - severity level of the violation
- "description": string - brief description of what you observed (be specific about what you see)
- "alert_type": must be exactly one of: "looking_away", "multiple_people", "phone_detected", "reading_from_material", "suspicious_activity", "none"

CRITICAL: Be CONSERVATIVE and LENIENT. False positives harm students. Only flag with high confidence."""

        if screen_image_base64:
            prompt += "\n\nAlso analyze the screen capture for suspicious activities like switching tabs, opening unauthorized applications, or searching for answers."

        # Ollama API format with optimized parameters for accuracy
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "images": [webcam_image_base64],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,  # Lower temperature for more consistent, accurate results
                "top_p": 0.85,       # Slightly lower for more focused predictions
                "top_k": 40,         # Control vocabulary sampling
                "repeat_penalty": 1.1,  # Reduce repetition
                "num_predict": 500,  # Ensure adequate response length for JSON
                "stop": ["}}", "}\n}"]  # Stop after complete JSON
            }
        }

        # Add screen image if available
        if screen_image_base64:
            payload["images"].append(screen_image_base64)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Qwen3 models may return JSON in "thinking" field instead of "response" field
            content = result.get("response", "") or result.get("thinking", "")

            print(f"[Ollama Debug] Raw response from Ollama:")
            print(f"[Ollama Debug] Response field: {result.get('response', 'empty')[:200]}")
            print(f"[Ollama Debug] Thinking field: {result.get('thinking', 'empty')[:200]}")
            print(f"[Ollama Debug] Using content: {content[:500]}...")  # Print first 500 chars

            # Try to parse JSON with enhanced cleaning
            content = content.strip()

            # Remove common markdown artifacts
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()

            # Remove any leading/trailing text outside JSON
            if "{" in content and "}" in content:
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                content = content[start_idx:end_idx]

            # Parse JSON
            try:
                analysis = json.loads(content)
                print(f"[Ollama Debug] Successfully parsed JSON")
            except json.JSONDecodeError as json_err:
                print(f"[Ollama Debug] JSON parsing failed: {json_err}")
                print(f"[Ollama Debug] Content that failed to parse: {content[:300]}")
                # If JSON parsing fails, try to extract JSON object from text
                import re
                json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', content, re.DOTALL)
                if json_match:
                    print(f"[Ollama Debug] Attempting to extract JSON from text")
                    try:
                        analysis = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        print(f"[Ollama Debug] Extracted JSON also failed to parse")
                        raise ValueError("Could not parse JSON from response")
                else:
                    print(f"[Ollama Debug] Could not find JSON object in response")
                    raise ValueError("Could not parse JSON from response")

            # Validate and normalize the response with strict schema enforcement
            valid_alert_types = ["looking_away", "multiple_people", "phone_detected",
                               "reading_from_material", "suspicious_activity", "none"]

            alert_type = analysis.get("alert_type", "none")
            if alert_type not in valid_alert_types:
                print(f"[Ollama Debug] Invalid alert_type '{alert_type}', defaulting to 'none'")
                alert_type = "none"

            # Ensure detected_issues is a list
            detected_issues = analysis.get("detected_issues", [])
            if not isinstance(detected_issues, list):
                detected_issues = [str(detected_issues)] if detected_issues else []

            analysis = {
                "is_suspicious": bool(analysis.get("is_suspicious", False)),
                "confidence": max(0.0, min(1.0, float(analysis.get("confidence", 0.5)))),  # Clamp to 0-1
                "detected_issues": detected_issues,
                "severity": max(1, min(5, int(analysis.get("severity", 1)))),  # Clamp to 1-5
                "description": str(analysis.get("description", "Analysis completed"))[:500],  # Limit length
                "alert_type": alert_type
            }

            print(f"[Ollama Debug] Validated analysis: is_suspicious={analysis['is_suspicious']}, "
                  f"confidence={analysis['confidence']:.2f}, alert_type={analysis['alert_type']}")

            is_suspicious = analysis["is_suspicious"] and analysis["confidence"] >= self.confidence_threshold

            return is_suspicious, analysis

        except requests.exceptions.RequestException as e:
            print(f"[Ollama Error] Error connecting to Ollama: {e}")
            print(f"[Ollama Error] Make sure Ollama is running with: ollama serve")
            print(f"[Ollama Error] And that {self.ollama_model} is installed: ollama pull {self.ollama_model}")
            print(f"[Ollama Error] Check available models with: ollama list")
            return False, {
                "error": f"Connection error: {str(e)}",
                "is_suspicious": False,
                "confidence": 0.0
            }
        except Exception as e:
            print(f"Error in Ollama analysis: {e}")
            return False, {
                "error": str(e),
                "is_suspicious": False,
                "confidence": 0.0
            }

    def generate_behavior_report(self, monitoring_events: list) -> Dict[str, Any]:
        """Generate a comprehensive behavior analysis report"""

        alert_breakdown = {}
        total_alerts = len(monitoring_events)

        for event in monitoring_events:
            alert_type = event.event_type.value
            alert_breakdown[alert_type] = alert_breakdown.get(alert_type, 0) + 1

        # Calculate risk score based on number and severity of alerts
        risk_score = 0.0
        for event in monitoring_events:
            risk_score += event.severity * event.confidence

        risk_score = min(risk_score / 10, 10.0)  # Normalize to 0-10

        # Generate summary
        if risk_score < 2:
            summary = "Low risk - Student behavior appears normal with minimal suspicious activity."
        elif risk_score < 5:
            summary = "Moderate risk - Some suspicious behaviors detected. Manual review recommended."
        elif risk_score < 8:
            summary = "High risk - Multiple instances of suspicious behavior detected. Exam integrity may be compromised."
        else:
            summary = "Critical risk - Severe and frequent cheating behaviors detected. Exam should be invalidated."

        return {
            "total_alerts": total_alerts,
            "alert_breakdown": alert_breakdown,
            "risk_score": round(risk_score, 2),
            "summary": summary
        }
