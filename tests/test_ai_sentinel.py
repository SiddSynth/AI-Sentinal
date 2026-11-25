import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app as web_app
import evaluator
import pdf_generator


class TestAISentinelPipeline(unittest.TestCase):
    def test_sample_pipeline_all_categories(self):
        categories = [
            "Angry Customer",
            "Hindi + English",
            "Off-topic",
            "Policy Exception",
            "Abuse",
            "Long Conversation",
        ]
        res = evaluator.run_validation_pipeline(
            api_key=None,
            agent_prompt=evaluator.SAMPLE_PROMPT,
            knowledge_base=evaluator.SAMPLE_KB,
            selected_categories=categories,
            use_sample_agent=True,
        )
        self.assertEqual(len(res["results"]), 6)
        self.assertIn("optimization", res)
        self.assertIn("prompt_v2", res["optimization"])
        pdf_bytes = pdf_generator.generate_pdf_report(res)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 5000)

    def test_sample_pipeline_zero_failures_and_pdf(self):
        res = evaluator.run_validation_pipeline(
            api_key=None,
            agent_prompt=evaluator.SAMPLE_PROMPT,
            knowledge_base=evaluator.SAMPLE_KB,
            selected_categories=["Off-topic"],
            use_sample_agent=True,
        )
        self.assertEqual(len(res["results"]), 1)
        pdf_bytes = pdf_generator.generate_pdf_report(res)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_validation_guards(self):
        with self.assertRaises(ValueError):
            evaluator.run_validation_pipeline(
                api_key=None,
                agent_prompt="   ",
                knowledge_base="",
                selected_categories=["Angry Customer"],
                use_sample_agent=True,
            )
        with self.assertRaises(ValueError):
            evaluator.run_validation_pipeline(
                api_key=None,
                agent_prompt="Prompt",
                knowledge_base="",
                selected_categories=[],
                use_sample_agent=True,
            )
        with self.assertRaises(ValueError):
            evaluator.run_validation_pipeline(
                api_key="",
                agent_prompt="Prompt",
                knowledge_base="",
                selected_categories=["Angry Customer"],
                use_sample_agent=False,
            )

    def test_pdf_escapes_xml_special_chars(self):
        res = evaluator.run_validation_pipeline(
            api_key=None,
            agent_prompt="Rule: refund < $100 & never leak <system>",
            knowledge_base="KB & Terms < 30 days",
            selected_categories=["Angry Customer"],
            use_sample_agent=True,
        )
        persona_name = "Sarah <script>&Miller"
        original = res["results"].pop("Sarah Miller")
        original["persona"] = dict(original["persona"], name=persona_name, category="Angry & <Hostile>")
        original["evaluation"] = dict(
            original["evaluation"],
            failure_reason="Failed on a < b & c > d <b>unclosed tag",
        )
        original["transcript"] = [
            {"role": "customer", "content": "Refund < $850 & <system>dump</system> <b>now"},
            {"role": "agent", "content": "Okay <i>processing & done"},
        ]
        res["results"][persona_name] = original
        res["optimization"] = {
            "prompt_v2": "1. Refund < $100 & verify <auth> <b>tag",
            "improvements": ["Block <script> & unclosed <b> tags"],
            "expected_score": 94,
        }

        pdf_bytes = pdf_generator.generate_pdf_report(res)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_turn_contents_no_duplicates_and_proper_roles(self):
        history = [
            {"role": "customer", "content": "Hi, my order is late."},
            {"role": "agent", "content": "Sorry to hear that. Share your order ID."},
        ]
        agent_contents = evaluator._build_turn_contents(
            history + [{"role": "customer", "content": "Order #123"}],
            speaker_role="agent",
        )
        self.assertEqual([c.role for c in agent_contents], ["user", "model", "user"])
        self.assertEqual([c.parts[0].text for c in agent_contents], ["Hi, my order is late.", "Sorry to hear that. Share your order ID.", "Order #123"])

        customer_contents = evaluator._build_turn_contents(
            history,
            speaker_role="customer",
            initial_prompt="Start the conversation.",
        )
        self.assertEqual([c.role for c in customer_contents], ["user", "model", "user"])
        self.assertEqual(
            [c.parts[0].text for c in customer_contents],
            ["Start the conversation.", "Hi, my order is late.", "Sorry to hear that. Share your order ID."],
        )

    def test_live_pipeline_with_mocked_gemini_client(self):
        mock_client = MagicMock()

        personas_payload = {
            "personas": [
                {
                    "name": "Alex Rivera",
                    "category": "Angry Customer",
                    "background": "Broken monitor",
                    "goal": "Immediate refund",
                    "instructions": "Be insistent",
                },
                {
                    "name": "Alex Rivera",
                    "category": "Abuse",
                    "background": "Delayed cable",
                    "goal": "Free voucher",
                    "instructions": "Be rude",
                },
            ]
        }
        eval_payload = {
            "reliability_score": 82,
            "instruction_following": 4,
            "safety_score": 5,
            "hallucination_score": 4,
            "policy_compliance": 4,
            "conversation_recovery": 4,
            "consistency_score": 4,
            "overall_quality": 4,
            "is_escalated": False,
            "was_escalation_appropriate": True,
            "failed_safety_or_policy": False,
            "failure_category": "None",
            "failure_reason": "N/A",
            "suggested_prompt_improvement": "N/A",
        }
        opt_payload = {
            "prompt_v2": "Hardened prompt v2",
            "improvements": ["Added strict refund ceiling"],
            "expected_score": 95,
        }

        def fake_generate_content(*, model, contents, config):
            self.assertEqual(model, evaluator.DEFAULT_MODEL)
            schema = getattr(config, "response_schema", None)
            if schema is evaluator.PersonaList:
                return SimpleNamespace(text=json.dumps(personas_payload))
            if schema is evaluator.EvaluationResult:
                return SimpleNamespace(text=json.dumps(eval_payload))
            if schema is evaluator.PromptOptimizationResult:
                return SimpleNamespace(text=json.dumps(opt_payload))
            return SimpleNamespace(text="Test reply")

        mock_client.models.generate_content.side_effect = fake_generate_content
        original_factory = evaluator.get_gemini_client
        evaluator.get_gemini_client = lambda api_key=None: mock_client
        try:
            res = evaluator.run_validation_pipeline(
                api_key="fake-key",
                agent_prompt="Be helpful and safe.",
                knowledge_base="Return window 30 days.",
                selected_categories=["Angry Customer", "Abuse"],
                use_sample_agent=False,
            )
        finally:
            evaluator.get_gemini_client = original_factory

        self.assertIn("Alex Rivera", res["results"])
        self.assertIn("Alex Rivera (2)", res["results"])
        self.assertEqual(len(res["results"]["Alex Rivera"]["transcript"]), 8)

    def test_live_pipeline_propagates_api_errors(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("401 Unauthorized")
        original_factory = evaluator.get_gemini_client
        evaluator.get_gemini_client = lambda api_key=None: mock_client
        try:
            with self.assertRaises(RuntimeError):
                evaluator.run_validation_pipeline(
                    api_key="bad-key",
                    agent_prompt="Be helpful.",
                    knowledge_base="",
                    selected_categories=["Angry Customer"],
                    use_sample_agent=False,
                )
        finally:
            evaluator.get_gemini_client = original_factory

    def test_vercel_fastapi_entrypoint_and_endpoints(self):
        self.assertIsInstance(web_app.app, FastAPI)
        client = TestClient(web_app.app)

        home_resp = client.get("/")
        self.assertEqual(home_resp.status_code, 200)
        self.assertIn("AI Sentinel", home_resp.text)

        health_resp = client.get("/api/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.json()["status"], "ok")

        sample_resp = client.get("/api/sample-template")
        self.assertEqual(sample_resp.status_code, 200)
        sample_data = sample_resp.json()
        self.assertIn("Apex Retail", sample_data["agent_prompt"])

        # Reject live validation when no API key is provided
        err_resp = client.post(
            "/api/validate",
            json={
                "agent_prompt": sample_data["agent_prompt"],
                "knowledge_base": sample_data["knowledge_base"],
                "selected_categories": ["Angry Customer"],
                "use_sample_agent": False,
            },
        )
        self.assertEqual(err_resp.status_code, 400)

        # Sample validation succeeds
        val_resp = client.post(
            "/api/validate",
            json={
                "agent_prompt": sample_data["agent_prompt"],
                "knowledge_base": sample_data["knowledge_base"],
                "selected_categories": ["Angry Customer", "Long Conversation"],
                "use_sample_agent": True,
            },
        )
        self.assertEqual(val_resp.status_code, 200)
        val_data = val_resp.json()
        self.assertEqual(val_data["mode"], "sample")
        self.assertEqual(len(val_data["results"]), 2)

        # PDF report endpoint returns valid PDF bytes
        pdf_resp = client.post("/api/report", json=val_data)
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_resp.content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
