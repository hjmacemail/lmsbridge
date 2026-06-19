"""Deterministic mock provider.

Used for local development, CI, and any environment without external API access.
It produces pedagogically-shaped output so the full pipeline can be exercised
end-to-end without a live model or sending student data anywhere.
"""
from __future__ import annotations

import json
import re

from app.llm.base import LLMMessage, LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    name = "mock"

    def complete(self, messages: list[LLMMessage], *, json_mode: bool = False) -> LLMResponse:
        all_text = "\n".join(m.content for m in messages)
        user_msgs = [m.content for m in messages if m.role == "user"]
        user_text = "\n".join(user_msgs)
        concept = self._extract(all_text, "Topic of this session:", "") \
            or self._extract(all_text, "Concept:", "the target concept")

        is_tutor = "interactive one-on-one tutoring session" in all_text.lower()
        # "Student response:" appears only in the feedback prompt (a reliable discriminator).
        is_feedback = "student response:" in user_text.lower()

        if is_tutor:
            text = self._mock_tutor_turn(concept, user_msgs, all_text)
        elif is_feedback:
            text = self._mock_feedback(user_text)
        elif json_mode:
            text = self._mock_activities_json(concept)
        else:
            text = self._mock_explanation(concept)
        return LLMResponse(text=text, model=self.model, provider=self.name, raw={"mock": True})

    @staticmethod
    def _evidence(all_text: str) -> dict:
        """Pull the student's actual missed question / wrong answer / misconception out of the
        prompt so even the mock can be course-specific (the real LLM uses the full context)."""
        q = re.search(r'- Q:\s*"(.*?)"', all_text, re.DOTALL)
        ca = re.search(r'chose\s*"(.*?)"\s*\(correct:\s*"(.*?)"\)', all_text, re.DOTALL)
        mis = re.search(r"likely misconception:\s*(.+)", all_text)
        return {
            "question": q.group(1).strip() if q else "",
            "chose": ca.group(1).strip() if ca else "",
            "correct": ca.group(2).strip() if ca else "",
            "misconception": mis.group(1).strip() if mis else "",
        }

    def _mock_tutor_turn(self, concept: str, user_msgs: list[str], all_text: str = "") -> str:
        """Deterministic interactive-tutor turn, grounded in the student's actual evidence.

        The opening turn is requested via a special user prompt; later turns count the
        student's substantive replies and complete the session once enough understanding
        has been shown (capped so it always terminates).
        """
        ev = self._evidence(all_text)
        opening = bool(user_msgs) and "open the tutoring session" in user_msgs[-1].lower()
        # Student turns = user messages that are not the opening/instruction prompt.
        student_turns = [u for u in user_msgs if "open the tutoring session" not in u.lower()]
        last = student_turns[-1].strip() if student_turns else ""
        substantive = (len(last) >= 25 and "i don't know" not in last.lower()
                       and last.lower() != "idk")

        if opening or not student_turns:
            if ev["question"] and ev["chose"]:
                reply = (
                    f"Hi! Let's work through {concept}. On the question “{ev['question']}” "
                    f"you chose “{ev['chose']}”, and the correct answer is "
                    f"“{ev['correct']}”. That points to a specific gap"
                    + (f": {ev['misconception']} " if ev['misconception'] else ". ")
                    + f"Before I say why, walk me through it: what made “{ev['chose']}” "
                    "look right to you?"
                )
            else:
                reply = (
                    f"Hi! Let's work through {concept} together. To start, in your own words: what "
                    f"does {concept} mean, and where did your reasoning take a turn?"
                )
            return json.dumps({"reply": reply, "complete": False})

        n = len([u for u in student_turns if len(u.strip()) >= 25])
        done = (n >= 3 and substantive) or len(student_turns) >= 6
        if done:
            target = f"“{ev['question']}”" if ev["question"] else f"{concept}"
            reply = (
                f"That's it — your reasoning now lands on “{ev['correct']}” for the right "
                f"reason. You've shown the gap on {concept} is closing. Carry that habit of naming "
                "the rule before each step into the next problem."
                if ev["correct"] else
                f"That's it — you applied {concept} consistently this time. Nice work; the gap "
                f"on {target} is closing."
            )
            return json.dumps({"reply": reply, "complete": True})

        if substantive:
            reply = (
                f"Good — you're close. Now test it against your earlier answer: if the rule for "
                f"{concept} is applied correctly, what should “{ev['question'] or 'that case'}"
                "” give, and why isn't it "
                + (f"“{ev['chose']}”?" if ev["chose"] else "what you first picked?")
            )
        else:
            hint = ev["misconception"] or f"the core rule behind {concept}"
            reply = (
                f"No problem — the likely snag is: {hint} Start from the definition of {concept}: "
                "what is the first thing that must be true? Try applying just that one step"
                + (f" to “{ev['chose']}”." if ev["chose"] else ".")
            )
        return json.dumps({"reply": reply, "complete": False})

    @staticmethod
    def _extract(text: str, marker: str, default: str) -> str:
        for line in text.splitlines():
            if marker.lower() in line.lower():
                return line.split(":", 1)[-1].strip() or default
        return default

    def _mock_activities_json(self, concept: str) -> str:
        payload = {
            "title": f"Rebuilding your foundation in {concept}",
            "rationale": (
                f"Recent assessment evidence suggests a gap in {concept}. This module "
                "uses retrieval practice and Socratic prompts to surface and correct the "
                "underlying misconception before it compounds."
            ),
            "activities": [
                {
                    "activity_type": "retrieval",
                    "prompt": f"Without looking at your notes, explain in your own words "
                              f"what {concept} means and why it matters.",
                    "payload": {"focus": "free recall", "hint": "Start from the definition."},
                },
                {
                    "activity_type": "socratic",
                    "prompt": f"Consider a case where {concept} is applied incorrectly. "
                              "What single assumption is the mistake hiding?",
                    "payload": {"focus": "diagnose the misconception"},
                },
                {
                    "activity_type": "practice",
                    "prompt": f"Work through one short problem involving {concept}. "
                              "Show each step of your reasoning.",
                    "payload": {
                        "focus": "guided application",
                        "hint": "Name the rule at each step.",
                    },
                },
            ],
        }
        return json.dumps(payload, indent=2)

    def _mock_feedback(self, user_text: str) -> str:
        response = self._extract(user_text, "Student response:", "")
        resolved = len(response.strip()) > 40 and "i don't know" not in response.lower()
        payload = {
            "is_correct": resolved,
            "resolves_misconception": resolved,
            "feedback": (
                "Good — your reasoning names the key rule and applies it consistently. "
                "Notice how stating the rule at each step kept you from the earlier slip."
                if resolved else
                "You're on the right track, but the central step is still assumed rather "
                "than justified. Try restating the underlying rule before applying it — what "
                "must be true for your move to be valid?"
            ),
        }
        return json.dumps(payload)

    def _mock_explanation(self, concept: str) -> str:
        return (
            f"Let's reason about {concept} together. First, recall the core idea, then we'll "
            "test it against an example. What do you already know that must stay true here?"
        )


# Helper used by the engine to robustly parse JSON out of model text.
def extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return json.loads(match.group(0))
