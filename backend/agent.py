import asyncio
from enum import Enum
from typing import List, Dict, Any, Tuple, Callable, Awaitable

# Placeholder for LLM client - to be implemented later
class LLMClient:
    async def generate_text(self, prompt: str, context: str = "") -> str:
        await asyncio.sleep(0.1) 
        return f"LLM response to: {prompt}"

    async def generate_code(self, prompt: str, context: str = "") -> str: # For backend Python code
        await asyncio.sleep(0.1)
        return f"# LLM generated Python code for: {prompt}\nprint('Hello from generated Python code')"

    async def generate_frontend_bundle(self, prompt: str, context: str = "") -> Dict[str, str]:
        await asyncio.sleep(0.1) # Simulate network latency
        # Example: if prompt contains "create a webpage", "html", "frontend", "button"
        if "webpage" in prompt.lower() or \
           "html" in prompt.lower() or \
           "frontend" in prompt.lower() or \
           "button" in prompt.lower() or \
           "display" in prompt.lower(): # Added "display" as a common trigger
            return {
                "html": "<h1>Generated Webpage</h1><p>This is a test from the agent's frontend generator.</p><button onclick='greet()'>Say Hi from Iframe</button><div id='dynamicContent'>Dynamic content area.</div>",
                "css": "body { font-family: Arial, sans-serif; background-color: #f0f0f0; margin: 15px; } h1 { color: darkgreen; } button { padding: 10px; background-color: lightgreen; border-radius: 5px; cursor: pointer; } #dynamicContent { margin-top: 10px; padding:10px; border: 1px solid green; }",
                "js": "function greet() { console.log('Hello from the generated JS in iframe!'); alert('Hi there from the iframe button click!'); document.getElementById('dynamicContent').innerText = 'Button was clicked at ' + new Date().toLocaleTimeString() + '. Random number: ' + Math.random(); }"
            }
        return {"html": "", "css": "", "js": ""}


class ReactPhase(Enum):
    REFLECT = "Reflect"
    EVALUATE = "Evaluate"
    ANALYZE = "Analyze"
    CORRECT = "Correct"
    TEST = "Test"
    FRONTEND_GEN = "FrontendGeneration" # New phase for frontend generation


class AgentOutput:
    def __init__(self):
        self.phases_info: List[Dict[str, Any]] = [] 
        self.generated_code: str | None = None # For backend Python code
        self.test_results: Dict[str, Any] | None = None
        self.final_output: Any = None
        self.errors: List[str] = []
        self.frontend_html: str | None = None
        self.frontend_css: str | None = None
        self.frontend_js: str | None = None

    def set_frontend_content(self, html: str | None = None, css: str | None = None, js: str | None = None):
        if html is not None: self.frontend_html = html
        if css is not None: self.frontend_css = css
        if js is not None: self.frontend_js = js

    def add_phase_info(self, phase: ReactPhase, thoughts: List[str], summary: str, data: Any = None):
        self.phases_info.append({
            "phase": phase.value,
            "thoughts": thoughts,
            "summary": summary,
            "data": data or {}
        })

    def set_generated_code(self, code: str): # For backend code
        self.generated_code = code

    def set_test_results(self, results: Dict[str, Any]):
        self.test_results = results

    def add_error(self, error_message: str):
        self.errors.append(error_message)


class AutonomousAgent:
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client if llm_client else LLMClient() 
        self.current_command: str = ""
        self.output = AgentOutput()
        self.current_thoughts: List[str] = [] 
        self.update_callback: Callable[[Dict], Awaitable[None]] | None = None

    async def _send_update(self, update_data: Dict):
        if self.update_callback:
            await self.update_callback(update_data)

    async def _reflect(self) -> Tuple[str, List[str]]:
        thoughts = [
            "Starting REFLECT phase.",
            f"Interpreting user command: '{self.current_command}'."
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.REFLECT.value, "thought": thoughts[-1]})
        
        goal_prompt = f"Understand and define the primary goal for the command: '{self.current_command}'"
        defined_goal = f"Goal: Process the command '{self.current_command}' to generate appropriate code (backend or frontend)." # LLM Sim
        thoughts.append(f"LLM simulation: Defined goal - '{defined_goal}'.")
        await self._send_update({"type": "thought", "phase": ReactPhase.REFLECT.value, "thought": thoughts[-1]})
        
        thoughts.append("REFLECT phase complete.")
        await self._send_update({
            "type": "phase_summary", "phase": ReactPhase.REFLECT.value, 
            "summary": f"Goal: {defined_goal}", "thoughts": thoughts
        })
        return defined_goal, thoughts

    async def _evaluate(self, goal: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        thoughts = [
            "Starting EVALUATE phase.",
            f"Goal to evaluate: '{goal}'.",
            "Considering possible approaches (backend Python, frontend HTML/CSS/JS, or both)..."
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})

        # Heuristic: if command mentions frontend terms, lean towards frontend approach
        is_frontend_likely = any(term in self.current_command.lower() for term in ["webpage", "html", "frontend", "display", "ui", "button", "page"])
        
        approaches = [
            {"name": "Approach 1: Backend Python script", "pros": ["Good for data manipulation, complex logic"], "cons": ["Requires Python sandbox"]},
            {"name": "Approach 2: Frontend HTML/CSS/JS bundle", "pros": ["Directly renders UI", "Good for visual tasks"], "cons": ["Limited server-side capabilities"]},
        ] 
        thoughts.append(f"LLM simulation: Identified approaches - {approaches}.")
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})

        selected_approach = approaches[1] if is_frontend_likely else approaches[0]
        thoughts.append(f"Selected approach based on command: {selected_approach['name']}.")
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})
        
        thoughts.append("EVALUATE phase complete.")
        await self._send_update({
            "type": "phase_summary", "phase": ReactPhase.EVALUATE.value,
            "summary": f"Selected Approach: {selected_approach['name']}", "data": {"approaches": approaches, "selected": selected_approach["name"]}, "thoughts": thoughts
        })
        return [selected_approach], thoughts # Return list, but we use the first one

    async def _analyze(self, selected_approach: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        thoughts = [
            "Starting ANALYZE phase.",
            f"Analyzing selected approach: '{selected_approach['name']}'.",
            "Breaking down the task into logical steps..."
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "thought": thoughts[-1]})
        
        steps = []
        if "Frontend" in selected_approach['name']:
            steps = ["Step 1: Define HTML structure.", "Step 2: Style with CSS.", "Step 3: Add interactivity with JavaScript."]
        else: # Backend Python
            steps = ["Step 1: Access necessary data.", "Step 2: Generate Python code for the logic.", "Step 3: Prepare for testing the Python code."]
        
        thoughts.append(f"LLM simulation: Defined steps - {steps}.")
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "thought": thoughts[-1]})
        
        thoughts.append("ANALYZE phase complete.")
        await self._send_update({
            "type": "phase_summary", "phase": ReactPhase.ANALYZE.value,
            "summary": "Defined logical steps for selected approach.", "data": {"steps": steps}, "thoughts": thoughts
        })
        return steps, thoughts

    async def _generate_frontend_code_bundle(self, analysis_steps: List[str]) -> bool:
        thoughts = [
            "Starting Frontend Code Generation phase.",
            f"Based on analysis steps: {analysis_steps}",
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.FRONTEND_GEN.value, "sub_phase": "Bundle Generation", "thought": thoughts[-1]})

        frontend_bundle = await self.llm_client.generate_frontend_bundle(prompt=self.current_command, context=str(analysis_steps))
        
        if frontend_bundle and (frontend_bundle.get("html") or frontend_bundle.get("js")):
            self.output.set_frontend_content(
                html=frontend_bundle.get("html"),
                css=frontend_bundle.get("css"),
                js=frontend_bundle.get("js")
            )
            thoughts.append(f"LLM simulation: Generated frontend bundle. HTML: {len(self.output.frontend_html or '')} chars, CSS: {len(self.output.frontend_css or '')} chars, JS: {len(self.output.frontend_js or '')} chars.")
            await self._send_update({
                "type": "frontend_code_bundle",
                "phase": ReactPhase.FRONTEND_GEN.value,
                "html": self.output.frontend_html,
                "css": self.output.frontend_css,
                "js": self.output.frontend_js,
                "thought": thoughts[-1],
                "message": "Frontend code bundle generated."
            })
            self.output.add_phase_info(
                ReactPhase.FRONTEND_GEN, thoughts, 
                "Frontend code bundle generated.", 
                data={"html_len": len(self.output.frontend_html or ''), "css_len": len(self.output.frontend_css or ''), "js_len": len(self.output.frontend_js or '')}
            )
            return True
        else:
            thoughts.append("LLM simulation: Failed to generate a meaningful frontend bundle.")
            await self._send_update({"type": "error", "phase": ReactPhase.FRONTEND_GEN.value, "message": "Failed to generate frontend bundle from LLM.", "thought": thoughts[-1]})
            self.output.add_error("Failed to generate frontend bundle.")
            self.output.add_phase_info(ReactPhase.FRONTEND_GEN, thoughts, "Frontend bundle generation failed.", data={})
            return False


    async def _generate_code_and_prepare_test(self, analysis_steps: List[str]) -> Tuple[str | None, List[str]]: # For backend code
        thoughts = [
            "Starting Backend Code Generation and Test Preparation phase.",
            f"Based on analysis steps: {analysis_steps}",
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "sub_phase": "Backend Code Generation", "thought": thoughts[-1]})

        code_generation_prompt = f"Generate Python code for the command: '{self.current_command}', following these steps: {analysis_steps}"
        generated_code = await self.llm_client.generate_code(prompt=code_generation_prompt)
        
        thoughts.append(f"LLM simulation: Generated backend code:\n{generated_code}")
        self.output.set_generated_code(generated_code) # Sets backend code
        await self._send_update({
            "type": "code_generated", "phase": ReactPhase.ANALYZE.value, "sub_phase": "Backend Code Generation", 
            "code": generated_code, "thought": thoughts[-1]
        })
        
        thoughts.append("Backend Code Generation complete.")
        # Summary for this specific action is added to AgentOutput within process_command
        return generated_code, thoughts

    async def _test(self, code_to_test: str, iteration: int) -> Tuple[Dict[str, Any], List[str]]:
        thoughts = [
            f"Starting TEST phase (Iteration {iteration}) for backend code.",
            f"Code to test:\n{code_to_test}"
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.TEST.value, "iteration": iteration, "thought": thoughts[-1]})
        
        simulated_results = {
            "status": "success", 
            "stdout": f"Simulated backend execution output for iteration {iteration}.",
            "stderr": "",
            "result": f"Simulated backend result data for iteration {iteration}"
        }
        if iteration == 1 and "error" in self.current_command.lower() and "backend" in self.current_command.lower(): # Test error path for backend
             simulated_results["status"] = "failure"
             simulated_results["stderr"] = "Simulated backend error: Division by zero on iteration 1."
             simulated_results["result"] = None

        thoughts.append(f"Sandbox simulation: Test results for backend code - {simulated_results}.")
        self.output.set_test_results(simulated_results) 
        await self._send_update({
            "type": "test_result", "phase": ReactPhase.TEST.value, "iteration": iteration,
            "results": simulated_results, "thought": thoughts[-1]
        })
        
        thoughts.append(f"TEST phase (Iteration {iteration}) for backend code complete.")
        await self._send_update({
            "type": "phase_summary", "phase": ReactPhase.TEST.value, "iteration": iteration,
            "summary": f"Backend Test Attempt {iteration} Results: {simulated_results['status']}", 
            "data": simulated_results, "thoughts": thoughts
        })
        return simulated_results, thoughts

    async def _correct(self, test_results: Dict[str, Any], iteration: int) -> Tuple[bool, List[str]]: # For backend code
        thoughts = [
            f"Starting CORRECT phase (Iteration {iteration}) for backend code.",
            f"Analyzing test results: {test_results}."
        ]
        await self._send_update({"type": "thought", "phase": ReactPhase.CORRECT.value, "iteration": iteration, "thought": thoughts[-1]})

        needs_correction = test_results.get("status") != "success"
        correction_applied_or_attempted = False

        if needs_correction:
            error_message = test_results.get("stderr", "Unknown error")
            thoughts.append(f"Error detected in backend code: {error_message}.")
            await self._send_update({"type": "thought", "phase": ReactPhase.CORRECT.value, "iteration": iteration, "thought": thoughts[-1]})
            
            thoughts.append("LLM simulation: Attempting to generate corrected backend code...")
            await self._send_update({"type": "thought", "phase": ReactPhase.CORRECT.value, "iteration": iteration, "thought": thoughts[-1]})
            
            correction_prompt = f"The following Python code produced an error: {error_message}. Original command: '{self.current_command}'. Code:\n{self.output.generated_code}\nPlease provide corrected code."
            corrected_code_simulation = await self.llm_client.generate_code(prompt=correction_prompt, context=f"Previous attempt (Iter {iteration}) failed. Error: {error_message}")
            self.output.set_generated_code(corrected_code_simulation) 
            correction_applied_or_attempted = True
            
            thoughts.append(f"LLM simulation: Generated new corrected backend code:\n{corrected_code_simulation}")
            await self._send_update({
                "type": "code_corrected", "phase": ReactPhase.CORRECT.value, "iteration": iteration,
                "new_code": corrected_code_simulation, "thought": thoughts[-1] # For backend code
            })
            self.output.add_error(f"Backend code correction attempted for (Iter {iteration}): {error_message}")
        else:
            thoughts.append("No errors detected in backend code. No correction needed.")
            await self._send_update({"type": "thought", "phase": ReactPhase.CORRECT.value, "iteration": iteration, "thought": thoughts[-1]})
        
        thoughts.append(f"CORRECT phase (Iteration {iteration}) for backend code complete.")
        summary_msg = f"Backend Correction Attempt {iteration}: {'Applied' if correction_applied_or_attempted else 'Not Needed'}"
        await self._send_update({
            "type": "phase_summary", "phase": ReactPhase.CORRECT.value, "iteration": iteration,
            "summary": summary_msg, 
            "data": {"successful_after_correction": not needs_correction, "correction_applied": correction_applied_or_attempted}, 
            "thoughts": thoughts
        })
        return not needs_correction, thoughts


    async def process_command(self, user_command: str, update_callback: Callable[[Dict], Awaitable[None]] | None = None) -> AgentOutput:
        self.current_command = user_command
        self.output = AgentOutput() 
        self.current_thoughts = [] 
        self.update_callback = update_callback

        await self._send_update({"type": "process_start", "command": user_command})

        # --- REFLECT ---
        goal, reflect_thoughts = await self._reflect()
        self.output.add_phase_info(ReactPhase.REFLECT, reflect_thoughts, f"Goal: {goal}")
        self.current_thoughts.extend(reflect_thoughts)

        # --- EVALUATE ---
        approaches, eval_thoughts = await self._evaluate(goal)
        selected_approach_info = approaches[0] # Assuming one is primarily selected for now
        self.output.add_phase_info(ReactPhase.EVALUATE, eval_thoughts, f"Selected Approach: {selected_approach_info['name']}", data={"approaches": approaches})
        self.current_thoughts.extend(eval_thoughts)

        # --- ANALYZE ---
        steps, analyze_thoughts = await self._analyze(selected_approach_info)
        self.output.add_phase_info(ReactPhase.ANALYZE, analyze_thoughts, "Defined logical steps", data={"steps": steps})
        self.current_thoughts.extend(analyze_thoughts)

        # --- GENERATE CONTENT (Frontend or Backend) ---
        if "Frontend" in selected_approach_info['name']:
            frontend_generated_successfully = await self._generate_frontend_code_bundle(steps)
            if frontend_generated_successfully:
                summary_msg = "Frontend code bundle generated and sent. Process complete."
                self.output.final_output = summary_msg
                self.current_thoughts.append(summary_msg)
                await self._send_update({"type": "process_end", "status": "success", "final_output": summary_msg, "has_frontend_code": True})
                return self.output
            else: # Frontend generation was attempted but failed
                error_msg = "Attempted frontend generation based on evaluation, but it failed."
                self.output.add_error(error_msg)
                self.current_thoughts.append(error_msg)
                await self._send_update({"type": "error", "message": error_msg})
                await self._send_update({"type": "process_end", "status": "failure", "error": error_msg})
                return self.output
        else: # Backend Python approach
            await self._send_update({"type": "info", "phase": "BACKEND_GENERATION", "message": "Proceeding with backend code generation."})
            generated_code, code_gen_thoughts = await self._generate_code_and_prepare_test(steps)
            self.current_thoughts.extend(code_gen_thoughts)
            
            # Update AgentOutput phase info for backend code generation
            if self.output.phases_info and self.output.phases_info[-1]["phase"] == ReactPhase.ANALYZE.value:
                self.output.phases_info[-1]['thoughts'].extend(code_gen_thoughts) 
                self.output.phases_info[-1]['summary'] += " + Backend Code Generation"
            else: 
                self.output.add_phase_info(ReactPhase.ANALYZE, code_gen_thoughts, "Backend Code Generation", data={})

            if not self.output.generated_code:
                error_msg = "Failed to generate backend code."
                self.output.add_error(error_msg)
                self.current_thoughts.append(error_msg)
                await self._send_update({"type": "error", "message": error_msg})
                await self._send_update({"type": "process_end", "status": "failure", "error": error_msg})
                return self.output

            # --- TEST & CORRECT LOOP (for backend code) ---
            max_iterations = 3 
            current_iteration = 0
            code_is_correct = False

            while current_iteration < max_iterations and not code_is_correct:
                current_iteration += 1
                thoughts_prefix = f"Backend Iteration {current_iteration}: "
                current_code_to_test = self.output.generated_code
                
                test_results, test_thoughts = await self._test(current_code_to_test, current_iteration)
                prefixed_test_thoughts = [thoughts_prefix + t for t in test_thoughts]
                self.output.add_phase_info(ReactPhase.TEST, prefixed_test_thoughts, f"Backend Test Attempt {current_iteration}", data=test_results)
                self.current_thoughts.extend(prefixed_test_thoughts)

                successful_after_test_or_correction, correct_thoughts = await self._correct(test_results, current_iteration)
                prefixed_correct_thoughts = [thoughts_prefix + t for t in correct_thoughts]
                self.output.add_phase_info(ReactPhase.CORRECT, prefixed_correct_thoughts, f"Backend Correction Attempt {current_iteration}", data={"successful_after_correction": successful_after_test_or_correction})
                self.current_thoughts.extend(prefixed_correct_thoughts)

                if successful_after_test_or_correction:
                    code_is_correct = True
                    self.output.final_output = test_results.get("result", "No specific result from backend test.")
                    self.current_thoughts.append("Backend code successfully generated and tested.")
                    await self._send_update({"type": "success", "message": "Backend code validated successfully.", "final_output": self.output.final_output})
                    break 
                elif current_iteration < max_iterations:
                    self.current_thoughts.append(f"Backend Iteration {current_iteration} failed. Proceeding to next correction attempt.")
                    await self._send_update({
                        "type": "info", 
                        "message": f"Backend Test/Correction Iteration {current_iteration} did not result in validated code. Retrying if attempts left."
                    })
                else: 
                    self.current_thoughts.append(f"Backend Iteration {current_iteration} failed. Max iterations reached.")
                    self.output.add_error(f"Failed to correct backend code after {max_iterations} attempts.")
                    await self._send_update({"type": "error", "message": f"Max iterations ({max_iterations}) reached for backend code. Code still not validated."})

            if not code_is_correct:
                final_error_msg = "Agent failed to produce working backend code after maximum iterations."
                self.output.add_error(final_error_msg)
                self.current_thoughts.append(final_error_msg)
                await self._send_update({"type": "error", "message": final_error_msg, "status": "failure"})
        
        await self._send_update({"type": "process_end", "status": "success" if self.output.final_output and not self.output.errors else "failure", "has_frontend_code": bool(self.output.frontend_html or self.output.frontend_js), "has_backend_code": bool(self.output.generated_code)})
        return self.output

# Example usage
async def dummy_callback(update_data: Dict):
    print(f"DUMMY CALLBACK RECEIVED: {update_data.get('type')} - Phase: {update_data.get('phase')} - Iter: {update_data.get('iteration')} - Msg: {update_data.get('message', update_data.get('thought', ''))}")
    if update_data.get('type') == 'frontend_code_bundle':
        print(f"  HTML: {len(update_data.get('html',''))} chars, CSS: {len(update_data.get('css',''))} chars, JS: {len(update_data.get('js',''))} chars")
    if update_data.get('type') == 'code_generated' or update_data.get('type') == 'code_corrected':
        print(f"  Code: {update_data.get('code')[:100]}...")


async def main():
    agent = AutonomousAgent()
    
    # Test frontend generation
    command_frontend = "Create a simple webpage with a button that alerts 'Hello'."
    print(f"\n--- Processing command: {command_frontend} ---")
    result_output_frontend = await agent.process_command(command_frontend, update_callback=dummy_callback)
    print(f"Frontend HTML generated: {result_output_frontend.frontend_html is not None}")
    print(f"Final output: {result_output_frontend.final_output}")
    print(f"Errors: {result_output_frontend.errors}")

    print("\n--- Summary of Phases (Frontend Test) ---")
    for phase_info in result_output_frontend.phases_info:
        print(f"Phase: {phase_info['phase']}, Summary: {phase_info['summary']}")


    # Test backend generation (modify command to not trigger frontend heuristic strongly)
    command_backend = "Generate a python script to calculate factorial and simulate a backend error on first test."
    print(f"\n--- Processing command: {command_backend} ---")
    result_output_backend = await agent.process_command(command_backend, update_callback=dummy_callback)
    print(f"Backend code generated: {result_output_backend.generated_code is not None}")
    print(f"Final output: {result_output_backend.final_output}")
    print(f"Errors: {result_output_backend.errors}")

    print("\n--- Summary of Phases (Backend Test) ---")
    for phase_info in result_output_backend.phases_info:
        print(f"Phase: {phase_info['phase']}, Summary: {phase_info['summary']}")


if __name__ == "__main__":
    asyncio.run(main())
