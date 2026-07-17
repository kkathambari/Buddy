import os
import sys
import unittest
import asyncio

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.productivity.coding_assistant import CodingAssistant
from brain.productivity.viva import LearningViva
from brain.productivity.career import CareerCoach
from brain.agents.coding_agent import CodingAgent
from brain.agents.document_agent import DocumentAgent
from brain.planner import TaskNode
from core.permissions import global_permission_manager

class TestProductivityFeatures(unittest.TestCase):
    
    def setUp(self):
        # Grant permissions for agent checks
        global_permission_manager.set_local_only_mode(True)
        global_permission_manager.grant_permission("coding_agent", "filesystem")
        global_permission_manager.grant_permission("coding_agent", "terminal")
        global_permission_manager.grant_permission("document_agent", "filesystem")

    def test_coding_assistant_code_review(self):
        diff = """--- a/core/runtime.py
+++ b/core/runtime.py
@@ -10,5 +10,12 @@
+    print("staged debug print statement")
+    try:
+        run_code()
+    except:
+        pass
+    # TODO: fix this later
"""
        annotations = CodingAssistant.review_pull_request(diff)
        self.assertEqual(len(annotations), 3)
        
        # Verify print statement annotation
        print_ann = [a for a in annotations if "print" in a["comment"]][0]
        self.assertEqual(print_ann["severity"], "warning")
        
        # Verify except statement annotation
        except_ann = [a for a in annotations if "generic Exception" in a["comment"]][0]
        self.assertEqual(except_ann["severity"], "error")
        
        # Verify TODO annotation
        todo_ann = [a for a in annotations if "TODO" in a["comment"]][0]
        self.assertEqual(todo_ann["severity"], "info")

    def test_coding_assistant_stack_trace_debug(self):
         traceback = """Traceback (most recent call last):
  File "brain/planner.py", line 45, in resolve_graph
    current = node.dependencies[0]
IndexError: list index out of range
"""
         debug_info = CodingAssistant.debug_stack_trace(traceback)
         self.assertIn("planner.py", debug_info["file"])
         self.assertEqual(debug_info["line"], 45)
         self.assertIn("IndexError", debug_info["exception"])
         self.assertIn("out of range", debug_info["suggestion"].lower())

    def test_learning_viva_question_compiler(self):
        text = "Docker is a containerization platform. Error occurs when resource limits are reached."
        questions = LearningViva.generate_viva_questions(text)
        
        self.assertEqual(len(questions), 2)
        
        # Verify definition
        self.assertEqual(questions[0]["question"], "What is Docker?")
        self.assertIn("containerization", questions[0]["answer"])
        
        # Verify cause-effect
        self.assertEqual(questions[1]["question"], "When does Error occur?")
        self.assertIn("resource limits", questions[1]["answer"])

    def test_career_coach_resume_ats(self):
        resume = "Experienced python developer with deep SQL knowledge and Git control."
        job_desc = "Wanted a Python developer who knows Docker and SQL."
        
        analysis = CareerCoach.analyze_resume_ats(resume, job_desc)
        self.assertEqual(analysis["match_score"], 66)
        self.assertIn("python", analysis["matched_keywords"])
        self.assertIn("docker", analysis["missing_keywords"])
        self.assertTrue(len(analysis["improvements"]) > 0)

    async def _run_agent_productivity_tasks_async(self):
        # CodingAgent task reviews
        c_agent = CodingAgent()
        task_review = TaskNode("t0", "Review staged pull request", "coding")
        task_review.description = "+++ b/src/core.py\n+print(1)"
        res_review = await c_agent.execute_task(task_review)
        self.assertIn("annotations", res_review)
        
        # DocumentAgent task vivas
        d_agent = DocumentAgent()
        task_viva = TaskNode("t1", "Generate Viva study cards", "document")
        task_viva.description = "React is a UI framework."
        res_viva = await d_agent.execute_task(task_viva)
        self.assertIn("React", res_viva)

    def test_agent_productivity_tasks(self):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._run_agent_productivity_tasks_async())
        finally:
            loop.close()

if __name__ == "__main__":
    unittest.main()
