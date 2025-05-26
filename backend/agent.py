import asyncio
import re # For parsing search/fetch queries
from enum import Enum
from typing import List, Dict, Any, Tuple, Callable, Awaitable, Optional

# Import project modules
from . import redis_client 
from . import config 
from .tools import search_tool
from .tools import web_tools # Import the web tools module

# --- LLMClient (as defined in previous step, with search & fetch query simulation) ---
class LLMClient:
    def __init__(self, provider_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.provider_name = provider_name; self.api_key = api_key; self.base_url = base_url; self.client = None
        print(f"LLMClient initialized with provider: {self.provider_name}")

    def _prepare_llm_messages(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None, for_code_gen: bool = False) -> List[Dict[str,str]]:
        messages = []
        if context_history:
            for turn in context_history[-6:]: messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": f"{'Generate code for: ' if for_code_gen else ''}{prompt}"})
        return messages

    async def generate_text(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None) -> str:
        if self.provider_name == 'placeholder':
            await asyncio.sleep(0.1) 
            if "search for" in prompt.lower():
                search_term = prompt.lower().split("search for", 1)[-1].strip().replace("?", "")
                return f"Okay, I need to find out about '{search_term}'. [SEARCH_QUERY: {search_term}]"
            if "fetch url" in prompt.lower() or "get content of" in prompt.lower(): # Simulate LLM deciding to fetch URL
                # Try to extract a URL using a simple regex, fallback to a default if not found
                url_match = re.search(r"(https?://[^\s]+)", prompt.lower())
                url_to_fetch = url_match.group(1) if url_match else "https://example.com/placeholder"
                return f"I need to get the content from '{url_to_fetch}'. [FETCH_URL: {url_to_fetch}]"
            if "what was my first command" in prompt.lower() and context_history:
                 first_user_command = next((turn['content'] for turn in context_history if turn['role'] == 'user'), "I don't see a first command.")
                 return f"Based on my history, your first command was: '{first_user_command}'."
            return f"LLM text response to: {prompt}"
        else: return f"Error: LLM provider '{self.provider_name}' not implemented for text generation."

    async def generate_code(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None) -> str: 
        if self.provider_name == 'placeholder':
            await asyncio.sleep(0.1)
            # LLM might decide to search or fetch URL before generating code.
            # e.g., "[SEARCH_QUERY: weather API]" or "[FETCH_URL: http://example.com/api_docs]"
            return f"# LLM generated Python code for: {prompt}\nprint('Hello from generated Python code')"
        else: return f"# Error: LLM provider '{self.provider_name}' not implemented."

    async def generate_frontend_bundle(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        if self.provider_name == 'placeholder':
            await asyncio.sleep(0.1)
            # LLM might search/fetch before generating frontend.
            # e.g., "[FETCH_URL: https://example.com/branding_guide]" for styles
            trigger_keywords = ["webpage", "html", "frontend", "button", "display", "ui", "page"]
            if any(term in prompt.lower() for term in trigger_keywords):
                return {"html": f"<h1>Generated Webpage for: {prompt}</h1><button>Test</button>", "css": "body {font-family: sans-serif;}", "js": "console.log('Loaded');"}
            return {"html": "", "css": "", "js": ""}
        else: return {"html": "<p>Error: LLM provider not implemented.</p>", "css": "", "js": ""}
# --- End LLMClient ---

class ReactPhase(Enum):
    REFLECT = "Reflect"; EVALUATE = "Evaluate"; ANALYZE = "Analyze"
    SEARCH = "Search"; FETCH_URL = "FetchURL" # Added FETCH_URL
    CORRECT = "Correct"; TEST = "Test"; FRONTEND_GEN = "FrontendGeneration"

class AgentOutput:
    # ... (AgentOutput class definition - no changes from previous step) ...
    def __init__(self):
        self.phases_info: List[Dict[str, Any]] = []; self.generated_code: str | None = None 
        self.test_results: Dict[str, Any] | None = None; self.final_output: Any = None
        self.errors: List[str] = []; self.frontend_html: str | None = None
        self.frontend_css: str | None = None; self.frontend_js: str | None = None
    def set_frontend_content(self, html: str|None=None, css: str|None=None, js: str|None=None):
        if html is not None: self.frontend_html = html
        if css is not None: self.frontend_css = css
        if js is not None: self.frontend_js = js
    def add_phase_info(self, phase: ReactPhase, thoughts: List[str], summary: str, data: Any = None):
        self.phases_info.append({ "phase": phase.value, "thoughts": thoughts, "summary": summary, "data": data or {}})
    def set_generated_code(self, code: str): self.generated_code = code
    def set_test_results(self, results: Dict[str, Any]): self.test_results = results
    def add_error(self, error_message: str): self.errors.append(error_message)

class AutonomousAgent:
    def __init__(self): # LLMClient initialized based on config
        api_key=None; base_url=None
        if config.LLM_PROVIDER=="openai": api_key=config.OPENAI_API_KEY
        elif config.LLM_PROVIDER=="groq": api_key=config.GROQ_API_KEY
        self.llm_client=LLMClient(provider_name=config.LLM_PROVIDER,api_key=api_key,base_url=base_url)
        self.current_command: str = ""; self.output = AgentOutput(); self.current_thoughts: List[str] = []
        self.update_callback: Callable[[Dict], Awaitable[None]]|None = None
        self.current_user_id: Any=None; self.current_session_id: Any=None
        self.conversation_history: List[Dict[str,str]] = []

    async def _send_update(self, update_data: Dict):
        if self.update_callback: await self.update_callback(update_data)

    def _extract_search_query(self, text: str) -> Optional[str]:
        match = re.search(r"\[SEARCH_QUERY:\s*(.*?)\]", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_fetch_url_request(self, text: str) -> Optional[str]: # New method
        match = re.search(r"\[FETCH_URL:\s*(https?://[^\s\]]+)\]", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    async def _perform_search_if_needed(self, llm_output: str, current_phase: ReactPhase) -> Optional[str]:
        search_query = self._extract_search_query(llm_output)
        if search_query:
            self.current_thoughts.append(f"LLM requested search: '{search_query}'.")
            await self._send_update({"type": "agent_action", "action": "web_search", "query": search_query, "phase": current_phase.value})
            results = await search_tool.tavily_search(search_query)
            self.current_thoughts.append(f"Search returned {len(results)} results.")
            await self._send_update({"type": "search_results", "results": results, "message": "Web search complete.", "phase": current_phase.value})
            self.output.add_phase_info(ReactPhase.SEARCH, self.current_thoughts[-2:], f"Searched for: '{search_query}'. Found {len(results)} results.", data={"query": search_query, "results": results})
            if not results or (len(results)==1 and results[0].get("error")): return "No search results or search failed."
            return "\n\n".join([f"Title: {r.get('title','N/A')}\nURL: {r.get('url','N/A')}\nSnippet: {r.get('content','N/A')[:300]}..." for r in results])
        return None

    async def _perform_url_fetch_if_needed(self, llm_output: str, current_phase: ReactPhase) -> Optional[str]: # New method
        url_to_fetch = self._extract_fetch_url_request(llm_output)
        if url_to_fetch:
            self.current_thoughts.append(f"LLM requested to fetch URL: '{url_to_fetch}'.")
            await self._send_update({"type": "agent_action", "action": "fetch_url", "url": url_to_fetch, "phase": current_phase.value})
            
            content, error = await web_tools.fetch_and_clean_url(url_to_fetch)
            
            if error:
                self.current_thoughts.append(f"Failed to fetch URL: {error}")
                await self._send_update({"type": "url_fetch_result", "url": url_to_fetch, "error": error, "phase": current_phase.value})
                self.output.add_phase_info(ReactPhase.FETCH_URL, self.current_thoughts[-1:], f"Failed to fetch URL: {url_to_fetch}", data={"url": url_to_fetch, "error": error})
                return f"Error fetching URL {url_to_fetch}: {error}" # Return error message to LLM
            
            self.current_thoughts.append(f"URL content fetched successfully (length: {len(content or '')}).")
            await self._send_update({"type": "url_fetch_result", "url": url_to_fetch, "content_snippet": (content or "")[:500], "phase": current_phase.value}) # Send snippet
            self.output.add_phase_info(ReactPhase.FETCH_URL, self.current_thoughts[-1:], f"Fetched URL: {url_to_fetch}", data={"url": url_to_fetch, "content_length": len(content or '')})
            return content # Return fetched content to LLM
        return None

    async def _process_llm_response_for_tools(self, llm_response: str, current_phase: ReactPhase, original_prompt_for_llm: str) -> Tuple[str, bool]:
        """Processes LLM response, checks for tool usage (search/fetch), executes tools, and re-prompts if needed."""
        tool_executed = False
        
        # Check for search query first
        search_results_str = await self._perform_search_if_needed(llm_response, current_phase)
        if search_results_str:
            tool_executed = True
            # Re-prompt LLM with search results
            refined_prompt = f"Based on these search results:\n{search_results_str}\n\nPlease now respond to the original request: {original_prompt_for_llm}"
            llm_response = await self.llm_client.generate_text(prompt=refined_prompt, context_history=self.conversation_history)
            # After getting results from search and re-prompting, check if the new response *also* wants to fetch a URL
            # (but avoid immediate re-searching)
            if self._extract_search_query(llm_response):
                 llm_response = "Tool results processed. Continuing with original task." # Simplified, prevent immediate re-search

        # Check for URL fetch request (could be in original response or response after search)
        fetched_content_str = await self._perform_url_fetch_if_needed(llm_response, current_phase)
        if fetched_content_str:
            tool_executed = True
            # Re-prompt LLM with fetched content
            refined_prompt = f"Based on this fetched content from URL:\n{fetched_content_str[:2000]}...\n\nPlease now respond to the original request: {original_prompt_for_llm}" # Limit fetched content length in prompt
            llm_response = await self.llm_client.generate_text(prompt=refined_prompt, context_history=self.conversation_history)
            # Final check to prevent immediate re-tooling from this response
            if self._extract_search_query(llm_response) or self._extract_fetch_url_request(llm_response):
                 llm_response = "Tool results processed. Continuing with original task."
        
        return llm_response, tool_executed

    async def _reflect(self) -> Tuple[str, List[str]]:
        thoughts = ["Starting REFLECT phase.", f"Interpreting user command: '{self.current_command}' considering history."]
        await self._send_update({"type": "thought", "phase": ReactPhase.REFLECT.value, "thought": thoughts[-1]})
        
        goal_prompt = f"Understand and define the primary goal for the command: '{self.current_command}'. If information is missing or external data is needed, indicate what needs to be searched for using [SEARCH_QUERY: your query here] or fetched using [FETCH_URL: full_url_here]."
        llm_response = await self.llm_client.generate_text(prompt=goal_prompt, context_history=self.conversation_history)
        
        final_llm_response_for_goal, _ = await self._process_llm_response_for_tools(llm_response, ReactPhase.REFLECT, goal_prompt)
        defined_goal = final_llm_response_for_goal
        
        thoughts.append(f"LLM response for goal definition: '{defined_goal}'.")
        await self._send_update({"type": "thought", "phase": ReactPhase.REFLECT.value, "thought": thoughts[-1]})
        thoughts.append("REFLECT phase complete.")
        await self._send_update({"type": "phase_summary", "phase": ReactPhase.REFLECT.value, "summary": f"Goal: {defined_goal}", "thoughts": thoughts})
        return defined_goal, thoughts

    async def _evaluate(self, goal: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        thoughts = ["Starting EVALUATE phase.", f"Goal: '{goal}'. Considering approaches. May use tools."]
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})

        evaluate_prompt = f"Goal: '{goal}'. Original command: '{self.current_command}'. Evaluate best approach (backend, frontend, mixed). Use [SEARCH_QUERY: query] or [FETCH_URL: url] if needed."
        llm_response = await self.llm_client.generate_text(prompt=evaluate_prompt, context_history=self.conversation_history)
        final_llm_response_for_eval, _ = await self._process_llm_response_for_tools(llm_response, ReactPhase.EVALUATE, evaluate_prompt)

        is_frontend_likely = any(term in final_llm_response_for_eval.lower() for term in ["frontend", "webpage", "ui"]) or \
                             any(term in self.current_command.lower() for term in ["webpage", "html", "frontend", "display", "ui", "button", "page"])
        approaches_list = [{"name": "Backend Python script"}, {"name": "Frontend HTML/CSS/JS bundle"}]
        selected_approach = approaches_list[1] if is_frontend_likely else approaches_list[0]
        
        thoughts.append(f"LLM eval response: '{final_llm_response_for_eval}'. Selected: {selected_approach['name']}.")
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})
        # ... (rest of EVALUATE phase summary)
        await self._send_update({"type": "phase_summary", "phase": ReactPhase.EVALUATE.value, "summary": f"Selected Approach: {selected_approach['name']}", "data": {"selected": selected_approach["name"], "llm_eval_response": final_llm_response_for_eval}, "thoughts": thoughts})
        return [selected_approach], thoughts


    async def _analyze(self, selected_approach: Dict[str, Any], goal: str) -> Tuple[List[str], List[str]]:
        thoughts = ["Starting ANALYZE phase.", f"Approach: '{selected_approach['name']}' for goal: '{goal}'. Defining steps. May use tools."]
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "thought": thoughts[-1]})

        analyze_prompt = f"Approach: '{selected_approach['name']}', Goal: '{goal}', Command: '{self.current_command}'. Define logical steps. Use [SEARCH_QUERY: query] or [FETCH_URL: url] if needed."
        llm_response = await self.llm_client.generate_text(prompt=analyze_prompt, context_history=self.conversation_history)
        final_llm_response_for_analyze, tool_used = await self._process_llm_response_for_tools(llm_response, ReactPhase.ANALYZE, analyze_prompt)
        
        # If a tool was used, the last item in conversation_history might be the tool's output.
        # The LLM response (final_llm_response_for_analyze) is based on that.
        steps = [f"Step derived from LLM (tool_used={tool_used}): {final_llm_response_for_analyze[:150]}..."]
        if "Frontend" in selected_approach['name']: steps.extend(["Define HTML.", "Style CSS.", "JS interactivity."])
        else: steps.extend(["Define Python logic.", "Prep for test."])

        thoughts.append(f"LLM defined steps: {steps} (based on response: '{final_llm_response_for_analyze}').")
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "thought": thoughts[-1]})
        # ... (rest of ANALYZE phase summary)
        await self._send_update({"type": "phase_summary", "phase": ReactPhase.ANALYZE.value, "summary": "Defined logical steps.", "data": {"steps": steps, "llm_analyze_response": final_llm_response_for_analyze}, "thoughts": thoughts})
        return steps, thoughts

    # Methods _generate_frontend_code_bundle, _generate_code_and_prepare_test
    # now accept `tool_data_context: Optional[str] = None`
    async def _generate_frontend_code_bundle(self, analysis_steps: List[str], tool_data_context: Optional[str] = None) -> bool:
        prompt_detail = f"Analysis Steps: {analysis_steps}. Original command: {self.current_command}."
        if tool_data_context: prompt_detail = f"Using information:\n{tool_data_context}\n\n{prompt_detail}"
        # ... (rest of method, calling self.llm_client.generate_frontend_bundle with this prompt and history)
        thoughts = [f"Starting Frontend Code Generation. Tool context provided: {tool_data_context is not None}"]
        frontend_bundle = await self.llm_client.generate_frontend_bundle(prompt=prompt_detail, context_history=self.conversation_history)
        # ... (same as before)
        if frontend_bundle and (frontend_bundle.get("html") or frontend_bundle.get("js")):
            self.output.set_frontend_content(html=frontend_bundle.get("html"), css=frontend_bundle.get("css"), js=frontend_bundle.get("js"))
            thoughts.append(f"LLM generated frontend bundle. HTML: {len(self.output.frontend_html or '')}c, CSS: {len(self.output.frontend_css or '')}c, JS: {len(self.output.frontend_js or '')}c.")
            await self._send_update({"type": "frontend_code_bundle", "phase": ReactPhase.FRONTEND_GEN.value, "html": self.output.frontend_html, "css": self.output.frontend_css, "js": self.output.frontend_js, "thought": thoughts[-1], "message": "Frontend bundle generated."})
            self.output.add_phase_info(ReactPhase.FRONTEND_GEN, thoughts, "Frontend bundle generated.", data={"html_len": len(self.output.frontend_html or '')})
            return True
        else:
            thoughts.append("LLM failed to generate meaningful frontend bundle.")
            await self._send_update({"type": "error", "phase": ReactPhase.FRONTEND_GEN.value, "message": "Failed to generate frontend bundle.", "thought": thoughts[-1]})
            self.output.add_error("Failed to generate frontend bundle."); self.output.add_phase_info(ReactPhase.FRONTEND_GEN, thoughts, "Frontend bundle generation failed.")
            return False


    async def _generate_code_and_prepare_test(self, analysis_steps: List[str], tool_data_context: Optional[str] = None) -> Tuple[str | None, List[str]]:
        prompt_detail = f"Analysis Steps: {analysis_steps}. Original command: {self.current_command}."
        if tool_data_context: prompt_detail = f"Using information:\n{tool_data_context}\n\n{prompt_detail}"
        # ... (rest of method, calling self.llm_client.generate_code with this prompt and history)
        thoughts = [f"Starting Backend Code Generation. Tool context provided: {tool_data_context is not None}"]
        generated_code = await self.llm_client.generate_code(prompt=prompt_detail, context_history=self.conversation_history)
        thoughts.append(f"LLM generated backend code:\n{generated_code}")
        self.output.set_generated_code(generated_code) 
        await self._send_update({"type": "code_generated", "phase": ReactPhase.ANALYZE.value, "sub_phase": "Backend Code Generation", "code": generated_code, "thought": thoughts[-1]})
        thoughts.append("Backend Code Generation complete.")
        return generated_code, thoughts

    # _test and _correct methods remain unchanged for this subtask.
    async def _test(self, code_to_test: str, iteration: int) -> Tuple[Dict[str, Any], List[str]]:
        thoughts = [f"TEST (Iter {iteration}): Backend code:\n{code_to_test}"]
        await self._send_update({"type": "thought", "phase": ReactPhase.TEST.value, "iteration": iteration, "thought": thoughts[-1]})
        sim_results = {"status": "success", "stdout": "Simulated test success", "stderr": "", "result": "Test passed"}
        if "error" in self.current_command.lower() and "backend test" in self.current_command.lower() and iteration == 1:
            sim_results = {"status": "failure", "stdout": "", "stderr": "Simulated test error", "result": "Test failed"}
        self.output.set_test_results(sim_results)
        await self._send_update({"type": "test_result", "phase": ReactPhase.TEST.value, "iteration": iteration, "results": sim_results, "thought": "Test completed."})
        return sim_results, thoughts

    async def _correct(self, test_results: Dict[str, Any], iteration: int) -> Tuple[bool, List[str]]:
        thoughts = [f"CORRECT (Iter {iteration}): Analyzing test results: {test_results.get('status')}"]
        needs_correction = test_results.get("status") != "success"
        if needs_correction:
            error_msg = test_results.get("stderr", "Unknown error")
            thoughts.append(f"Error detected: {error_msg}. Attempting correction.")
            correction_prompt = f"Code produced error: {error_msg}. Original command: '{self.current_command}'. Code:\n{self.output.generated_code}\nCorrected code:"
            corrected_code = await self.llm_client.generate_code(prompt=correction_prompt, context_history=self.conversation_history)
            self.output.set_generated_code(corrected_code)
            thoughts.append(f"LLM generated corrected code:\n{corrected_code}")
            await self._send_update({"type": "code_corrected", "phase": ReactPhase.CORRECT.value, "iteration": iteration, "new_code": corrected_code})
        else: thoughts.append("No correction needed.")
        return not needs_correction, thoughts
        
    async def process_command(self, user_command: str, user_id: Any, session_id: Any, update_callback: Callable[[Dict], Awaitable[None]] | None = None) -> AgentOutput:
        self.current_command = user_command; self.output = AgentOutput(); self.current_thoughts = []
        self.update_callback = update_callback; self.current_user_id = user_id; self.current_session_id = session_id
        
        loaded_context = await redis_client.load_agent_context(user_id, session_id)
        self.conversation_history = loaded_context.get("conversation_history", []) if loaded_context else []
        await self._send_update({"type": "info", "message": f"Loaded {len(self.conversation_history)} history turns."})
        
        self.conversation_history.append({"role": "user", "content": self.current_command})
        await self._send_update({"type": "process_start", "command": user_command})

        goal, reflect_thoughts = await self._reflect()
        self.output.add_phase_info(ReactPhase.REFLECT, reflect_thoughts, f"Goal: {goal}"); self.current_thoughts.extend(reflect_thoughts)
        
        approaches, eval_thoughts = await self._evaluate(goal)
        selected_approach_info = approaches[0]
        self.output.add_phase_info(ReactPhase.EVALUATE, eval_thoughts, f"Approach: {selected_approach_info['name']}", data=approaches); self.current_thoughts.extend(eval_thoughts)

        steps, analyze_thoughts = await self._analyze(selected_approach_info, goal)
        self.output.add_phase_info(ReactPhase.ANALYZE, analyze_thoughts, "Steps defined", data={"steps": steps}); self.current_thoughts.extend(analyze_thoughts)
        
        # Capture output from the last tool used (search or fetch) if any, to pass to code generation
        tool_data_for_code_gen: Optional[str] = None
        if self.output.phases_info:
            last_phase_entry = self.output.phases_info[-1]
            if last_phase_entry["phase"] == ReactPhase.SEARCH.value:
                results = last_phase_entry.get("data", {}).get("results", [])
                if results and not (len(results)==1 and results[0].get("error")): 
                    tool_data_for_code_gen = "\n\n".join([f"Title: {r.get('title','N/A')}\nURL: {r.get('url','N/A')}\nSnippet: {r.get('content','N/A')[:300]}..." for r in results])
            elif last_phase_entry["phase"] == ReactPhase.FETCH_URL.value:
                # Assuming the 'data' for FETCH_URL stores the fetched content directly or under a 'content' key
                # And that _perform_url_fetch_if_needed returns the content string
                # The current _perform_url_fetch_if_needed returns the content directly, which is then used to re-prompt.
                # The data stored in add_phase_info for FETCH_URL is {"url": url, "content_length": len(content or '')}
                # For now, we'll assume the LLM incorporated it into its last response used for 'steps'.
                # A more direct way: if _analyze used a tool, its direct output could be captured here.
                # For simplicity, we'll rely on the LLM's final response in 'steps' having incorporated tool data.
                # This means tool_data_for_code_gen will primarily be from the last explicit tool action if it was the *very last* thing.
                # A better approach: _process_llm_response_for_tools could return the tool output string if a tool was used.
                pass # Relies on LLM incorporating fetched data into its 'steps' generation

        if "Frontend" in selected_approach_info['name']:
            generated = await self._generate_frontend_code_bundle(steps, tool_data_context=tool_data_for_code_gen)
            self.output.final_output = "Frontend bundle generated." if generated else "Frontend generation failed."
        else:
            generated_code, code_gen_thoughts = await self._generate_code_and_prepare_test(steps, tool_data_context=tool_data_for_code_gen)
            self.current_thoughts.extend(code_gen_thoughts)
            self.output.add_phase_info(ReactPhase.ANALYZE, code_gen_thoughts, "Backend Code Gen (post-tool)", data={})
            if not generated_code: self.output.add_error("Backend code gen failed."); self.output.final_output = "Backend code gen failed."
            else: # Test/Correct loop for backend code
                # ... (test/correct loop as before) ...
                max_iterations = 3; current_iteration = 0; code_is_correct = False
                while current_iteration < max_iterations and not code_is_correct:
                    current_iteration += 1
                    test_results, test_thoughts = await self._test(self.output.generated_code, current_iteration)
                    self.output.add_phase_info(ReactPhase.TEST, test_thoughts, f"Backend Test Iter {current_iteration}", data=test_results)
                    successful_after_test_or_correction, correct_thoughts = await self._correct(test_results, current_iteration)
                    self.output.add_phase_info(ReactPhase.CORRECT, correct_thoughts, f"Backend Correct Iter {current_iteration}", data={"successful": successful_after_test_or_correction})
                    if successful_after_test_or_correction:
                        code_is_correct = True; self.output.final_output = test_results.get("result", "Backend code tested.")
                        break
                if not code_is_correct: self.output.add_error("Backend code validation failed."); self.output.final_output = "Backend code validation failed."

        # Save context
        assistant_summary = {"role": "assistant", "summary": self.output.final_output or "Processing complete.", "code_type": "python" if self.output.generated_code else ("frontend" if self.output.frontend_html else "none"), "errors": bool(self.output.errors)}
        self.conversation_history.append(assistant_summary)
        MAX_HIST = 10; self.conversation_history = self.conversation_history[-(MAX_HIST*2):] if len(self.conversation_history) > MAX_HIST*2 else self.conversation_history
        await redis_client.save_agent_context(user_id, session_id, {"conversation_history": self.conversation_history})
        
        await self._send_update({"type": "process_end", "status": "success" if not self.output.errors else "failure", "final_output": self.output.final_output})
        return self.output

# ... (main_test and dummy_callback for testing) ...
async def dummy_callback(update_data: Dict):
    print(f"DUMMY CALLBACK: {update_data.get('type')} - Phase: {update_data.get('phase')} - Action: {update_data.get('action')} - Query/URL: {update_data.get('query', update_data.get('url','N/A'))} - Msg: {update_data.get('message', update_data.get('thought', ''))[:150]}")

async def main():
    await redis_client.init_redis_pool()
    if not redis_client.redis_pool: print("CRITICAL: Redis pool failed."); return
    agent = AutonomousAgent()
    test_user = "test_fetch_user"; test_session = "fetch_session_1"
    await redis_client.delete_agent_context(test_user, test_session)

    cmd1 = "fetch url https://example.com and tell me its main heading" # Test fetch
    print(f"\n--- CMD 1: {cmd1} ---"); out1 = await agent.process_command(cmd1, test_user, test_session, dummy_callback)
    print(f"Output 1 Final: {out1.final_output}, Errors: {out1.errors}")
    
    cmd2 = "based on the content of that example page, create a short poem" # Test context after fetch
    print(f"\n--- CMD 2: {cmd2} ---"); out2 = await agent.process_command(cmd2, test_user, test_session, dummy_callback)
    print(f"Output 2 Final: {out2.final_output}, Errors: {out2.errors}")

    cmd3 = "now search for python's official website and then fetch its content" # Test search then fetch
    print(f"\n--- CMD 3: {cmd3} ---"); out3 = await agent.process_command(cmd3, test_user, test_session, dummy_callback)
    print(f"Output 3 Final: {out3.final_output}, Errors: {out3.errors}")

    await redis_client.close_redis_pool()

if __name__ == "__main__":
    asyncio.run(main())
