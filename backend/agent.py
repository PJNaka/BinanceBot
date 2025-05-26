import asyncio
import re 
import json 
from enum import Enum
from typing import List, Dict, Any, Tuple, Callable, Awaitable, Optional

# Import project modules
from . import redis_client 
from . import config 
from .tools import search_tool
from .tools import web_tools

# Attempt to import SDKs
try: from groq import Groq
except ImportError: Groq = None 
try: from openai import OpenAI
except ImportError: OpenAI = None
# try: import google.generativeai as genai
# except ImportError: genai = None

# --- LLMClient Class (as per previous state) ---
class LLMClient:
    def __init__(self, provider_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.provider_name = provider_name; self.api_key = api_key; self.base_url = base_url; self.client = None
        if self.provider_name == 'groq':
            if Groq and api_key and api_key != config.GROQ_API_KEY: self.client = Groq(api_key=self.api_key)
            elif not Groq: print("Error: Groq library not installed.")
            else: print("Warning: Groq API key missing/placeholder.")
        elif self.provider_name == 'openai':
            if OpenAI and api_key and api_key != config.OPENAI_API_KEY: self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            elif not OpenAI: print("Error: OpenAI library not installed.")
            else: print("Warning: OpenAI API key missing/placeholder.")
        # elif self.provider_name == 'gemini': # Conceptual
            # if genai and api_key and api_key != config.GEMINI_API_KEY: 
            #     genai.configure(api_key=self.api_key); self.client = genai.GenerativeModel('gemini-1.5-flash-latest')
            # elif not genai: print("Error: Gemini library not installed.")
            # else: print("Warning: Gemini API key missing/placeholder.")
        print(f"LLMClient for {self.provider_name}. Client {'OK' if self.client else 'NOT OK (or placeholder/conceptual)'}.")

    def _prepare_llm_messages(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None, system_message: Optional[str] = None) -> List[Dict[str,str]]:
        messages = []
        if system_message: messages.append({"role": "system", "content": system_message})
        if context_history:
            for turn in context_history[-6:]: messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def generate_text(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None) -> str:
        if self.provider_name == 'placeholder':
            await asyncio.sleep(0.05) 
            if "search for" in prompt.lower():
                search_term = prompt.lower().split("search for", 1)[-1].strip().replace("?", "")
                return f"Okay, I need to find out about '{search_term}'. [SEARCH_QUERY: {search_term}]"
            if "fetch url" in prompt.lower() or "get content of" in prompt.lower():
                url_match = re.search(r"(https?://[^\s]+)", prompt.lower())
                url_to_fetch = url_match.group(1) if url_match else "https://example.com/placeholder_fetch"
                return f"I need to get the content from '{url_to_fetch}'. [FETCH_URL: {url_to_fetch}]"
            if "what was my first command" in prompt.lower() and context_history:
                 first_user_cmd = next((t['content'] for t in context_history if t['role'] == 'user'), "I don't see one.")
                 return f"History indicates your first command was: '{first_user_cmd}'."
            return f"LLM text response to: {prompt}"
        
        system_msg_tools = "You are a helpful assistant. If you need to search the web, respond with [SEARCH_QUERY: your query here]. If you need to fetch content from a URL, respond with [FETCH_URL: full_url_here]."
        messages = self._prepare_llm_messages(prompt, context_history, system_message=system_msg_tools)

        try:
            if self.provider_name == 'groq' and self.client:
                completion = await asyncio.to_thread(self.client.chat.completions.create, messages=messages, model="llama3-8b-8192", temperature=0.7)
                return completion.choices[0].message.content
            elif self.provider_name == 'openai' and self.client:
                completion = await asyncio.to_thread(self.client.chat.completions.create, messages=messages, model="gpt-4o-mini", temperature=0.7)
                return completion.choices[0].message.content
            # elif self.provider_name == 'gemini' and self.client: # Conceptual
            #     # gemini_messages = adapt_messages_for_gemini(messages)
            #     # response = await asyncio.to_thread(self.client.generate_content, gemini_messages)
            #     # return response.text
            #     return "Gemini text response (simulated)"
            else: return f"Error: LLM provider '{self.provider_name}' client not properly initialized or provider not supported."
        except Exception as e: print(f"{self.provider_name} API error in generate_text: {e}"); return f"Error communicating with {self.provider_name}: {e}"


    async def generate_code(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None) -> str: 
        if self.provider_name == 'placeholder':
            await asyncio.sleep(0.05)
            return f"# LLM generated Python code for: {prompt}\nprint('Hello from generated Python code')"

        system_msg_code = "You are a Python code generation assistant. If information is missing, use [SEARCH_QUERY: query] or [FETCH_URL: url]. Otherwise, generate ONLY Python code. Do not include explanations or markdown like ```python ... ```."
        messages = self._prepare_llm_messages(prompt, context_history, system_message=system_msg_code)
        response_content = ""
        try:
            if self.provider_name == 'groq' and self.client:
                completion = await asyncio.to_thread(self.client.chat.completions.create, messages=messages, model="mixtral-8x7b-32768", temperature=0.2)
                response_content = completion.choices[0].message.content
            elif self.provider_name == 'openai' and self.client:
                completion = await asyncio.to_thread(self.client.chat.completions.create, messages=messages, model="gpt-4o-mini", temperature=0.2)
                response_content = completion.choices[0].message.content
            # elif self.provider_name == 'gemini' and self.client: # Conceptual
            #     # response = await asyncio.to_thread(self.client.generate_content, adapt_messages_for_gemini(messages, system_msg_code))
            #     # response_content = response.text
            #     return "# Gemini Python code (simulated)"
            else: return f"# Error: LLM provider '{self.provider_name}' client not initialized or provider not supported for code."

            if response_content.startswith("```python"): response_content = response_content[len("```python"):].strip()
            elif response_content.startswith("```"): response_content = response_content[len("```"):].strip()
            if response_content.endswith("```"): response_content = response_content[:-len("```")].strip()
            return response_content
        except Exception as e: print(f"{self.provider_name} API error in generate_code: {e}"); return f"# Error with {self.provider_name}: {e}"

    async def generate_frontend_bundle(self, prompt: str, context_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        if self.provider_name == 'placeholder':
            await asyncio.sleep(0.05)
            if any(term in prompt.lower() for term in ["webpage", "html", "frontend"]):
                return {"html": f"<h1>Placeholder: {prompt}</h1>", "css": "body {color: green;}", "js": "console.log('placeholder frontend');"}
            return {"html": "", "css": "", "js": ""}

        system_msg_frontend = "You are a frontend code generation assistant. If information is missing, use [SEARCH_QUERY: query] or [FETCH_URL: url]. Otherwise, generate HTML, CSS, and JavaScript. Respond with a single JSON object with keys 'html', 'css', 'js'. Ensure JSON is well-formed."
        messages = self._prepare_llm_messages(prompt, context_history, system_message=system_msg_frontend)
        response_content = ""
        try:
            if self.provider_name == 'groq' and self.client:
                completion = await asyncio.to_thread(self.client.chat.completions.create, messages=messages, model="llama3-8b-8192")
                response_content = completion.choices[0].message.content
            elif self.provider_name == 'openai' and self.client:
                completion = await asyncio.to_thread(self.client.chat.completions.create, messages=messages, model="gpt-4o-mini", response_format={"type": "json_object"})
                response_content = completion.choices[0].message.content
            # elif self.provider_name == 'gemini' and self.client: # Conceptual
            #     # response = await asyncio.to_thread(self.client.generate_content, adapt_messages_for_gemini(messages, system_msg_frontend))
            #     # response_content = response.text
            #     return {"html": "<!-- Gemini HTML (simulated) -->", "css": "", "js": ""}
            else: return {"html": f"<p>Error: LLM provider '{self.provider_name}' client not initialized or provider not supported for frontend.</p>", "css": "", "js": ""}
            
            json_match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response_content, re.DOTALL)
            json_str = json_match.group(1) if json_match else response_content[response_content.find('{'):response_content.rfind('}')+1]
            try:
                bundle = json.loads(json_str)
                return {"html": bundle.get("html",""), "css": bundle.get("css",""), "js": bundle.get("js","")}
            except json.JSONDecodeError as e:
                print(f"{self.provider_name}: Failed to parse JSON for frontend: {e}\nResponse: {response_content}")
                return {"html": f"<p>Error parsing JSON.</p><pre>{response_content}</pre>", "css": "", "js": ""}
        except Exception as e:
            print(f"{self.provider_name} API error in generate_frontend_bundle: {e}"); return {"html": f"<p>Error with {self.provider_name}: {e}</p>", "css": "", "js": ""}
# --- End LLMClient Class ---

class ReactPhase(Enum):
    REFLECT = "Reflect"; EVALUATE = "Evaluate"; ANALYZE = "Analyze"
    SEARCH = "Search"; FETCH_URL = "FetchURL" 
    CORRECT = "Correct"; TEST = "Test"; FRONTEND_GEN = "FrontendGeneration"

class AgentOutput: # No changes from previous
    def __init__(self):
        self.phases_info: List[Dict[str, Any]] = []; self.generated_code: str | None = None 
        self.test_results: Dict[str, Any] | None = None; self.final_output: Any = None
        self.errors: List[str] = []; self.frontend_html: str | None = None
        self.frontend_css: str | None = None; self.frontend_js: str | None = None
    def set_frontend_content(self, html: str|None=None, css: str|None=None, js: str|None=None):
        if html is not None: self.frontend_html = html; 
        if css is not None: self.frontend_css = css; 
        if js is not None: self.frontend_js = js
    def add_phase_info(self, phase: ReactPhase, thoughts: List[str], summary: str, data: Any = None):
        self.phases_info.append({ "phase": phase.value, "thoughts": thoughts, "summary": summary, "data": data or {}})
    def set_generated_code(self, code: str): self.generated_code = code
    def set_test_results(self, results: Dict[str, Any]): self.test_results = results
    def add_error(self, error_message: str): self.errors.append(error_message)

class AutonomousAgent:
    def __init__(self): 
        api_key=None; base_url=None
        if config.LLM_PROVIDER=="openai": api_key=config.OPENAI_API_KEY; base_url=config.OPENAI_API_BASE_URL 
        elif config.LLM_PROVIDER=="groq": api_key=config.GROQ_API_KEY
        elif config.LLM_PROVIDER=="gemini": api_key=config.GEMINI_API_KEY
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

    def _extract_fetch_url_request(self, text: str) -> Optional[str]:
        match = re.search(r"\[FETCH_URL:\s*(https?://[^\s\]]+)\]", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    async def _perform_search_if_needed(self, llm_output: str, current_phase: ReactPhase) -> Optional[str]:
        search_query = self._extract_search_query(llm_output)
        if search_query:
            self.current_thoughts.append(f"LLM requested search: '{search_query}'.")
            await self._send_update({"type": "agent_action", "action": "web_search", "query": search_query, "phase": current_phase.value})
            results = await search_tool.tavily_search(search_query) # Max 3 results by default in search_tool
            self.current_thoughts.append(f"Search returned {len(results)} results.")
            await self._send_update({"type": "search_results", "results": results, "message": "Web search complete.", "phase": current_phase.value})
            self.output.add_phase_info(ReactPhase.SEARCH, self.current_thoughts[-2:], f"Searched for: '{search_query}'. Found {len(results)} results.", data={"query": search_query, "results": results})
            
            if not results or (len(results)==1 and results[0].get("error")): 
                return "No relevant search results found or search failed." # More informative for LLM
            
            # **Improved Formatting for Search Results (Step 1)**
            formatted_results = "Search Results:\n"
            for i, res in enumerate(results[:3]): # Limit to top 2-3 results
                title = res.get('title', 'N/A')
                url = res.get('url', 'N/A')
                snippet = res.get('content', 'N/A')[:300] # Snippet length
                formatted_results += f"{i+1}. Title: {title}\n   URL: {url}\n   Snippet: {snippet}...\n"
            return formatted_results.strip()
        return None

    async def _perform_url_fetch_if_needed(self, llm_output: str, current_phase: ReactPhase) -> Optional[str]:
        url_to_fetch = self._extract_fetch_url_request(llm_output)
        if url_to_fetch:
            self.current_thoughts.append(f"LLM requested to fetch URL: '{url_to_fetch}'.")
            await self._send_update({"type": "agent_action", "action": "fetch_url", "url": url_to_fetch, "phase": current_phase.value})
            content, error = await web_tools.fetch_and_clean_url(url_to_fetch) # Uses fetch_and_clean_url
            
            if error:
                # ... (error handling as before)
                self.current_thoughts.append(f"Failed to fetch URL: {error}")
                await self._send_update({"type": "url_fetch_result", "url": url_to_fetch, "error": error, "phase": current_phase.value})
                self.output.add_phase_info(ReactPhase.FETCH_URL, self.current_thoughts[-1:], f"Failed to fetch URL: {url_to_fetch}", data={"url": url_to_fetch, "error": error})
                return f"Error fetching URL {url_to_fetch}: {error}" 
            
            self.current_thoughts.append(f"URL content fetched successfully (length: {len(content or '')}).")
            await self._send_update({"type": "url_fetch_result", "url": url_to_fetch, "content_snippet": (content or "")[:500], "phase": current_phase.value})
            self.output.add_phase_info(ReactPhase.FETCH_URL, self.current_thoughts[-1:], f"Fetched URL: {url_to_fetch}", data={"url": url_to_fetch, "content_length": len(content or '')})
            
            # **Improved Formatting for Fetched Content (Step 1)**
            return f"Content from {url_to_fetch}:\n{content[:3000]}..." # Limit content length for prompt
        return None

    async def _process_llm_response_for_tools(self, llm_response: str, current_phase: ReactPhase, original_task_description_for_phase: str) -> Tuple[str, bool]:
        tool_executed = False
        tool_output_for_llm = "" # Stores formatted results from the last tool used in this sequence

        # **Refined Re-Prompt Strategy (Step 2)**
        # The `original_task_description_for_phase` is the key input for this phase (e.g. user command for REFLECT, goal for EVALUATE/ANALYZE)

        # First, check for search query
        formatted_search_results = await self._perform_search_if_needed(llm_response, current_phase)
        if formatted_search_results:
            tool_executed = True
            tool_output_for_llm = formatted_search_results
            
            # Construct refined prompt incorporating search results
            if current_phase == ReactPhase.REFLECT:
                refined_prompt = f"Original user command: '{self.current_command}'.\nWeb search results:\n{tool_output_for_llm}\n\nBased on all this, what is the primary goal?"
            elif current_phase == ReactPhase.EVALUATE:
                refined_prompt = f"Current goal: '{original_task_description_for_phase}'.\nWeb search results:\n{tool_output_for_llm}\n\nConsidering this new information, what is the best approach (e.g., backend, frontend, mixed)?"
            elif current_phase == ReactPhase.ANALYZE:
                refined_prompt = f"Current goal: '{original_task_description_for_phase}'.\nWeb search results:\n{tool_output_for_llm}\n\nWhat are the logical steps to achieve this goal, considering this new information?"
            else: # Default re-prompt if phase not specifically handled (should ideally not happen)
                refined_prompt = f"Based on these search results:\n{tool_output_for_llm}\n\nPlease now respond to the original request which was to address: {original_task_description_for_phase}"
            
            llm_response = await self.llm_client.generate_text(prompt=refined_prompt, context_history=self.conversation_history)
            if self._extract_search_query(llm_response): llm_response = "Search results processed. Continuing with task." 

        # Then, check for URL fetch request (could be in original response or response after search)
        fetched_content_str = await self._perform_url_fetch_if_needed(llm_response, current_phase)
        if fetched_content_str:
            tool_executed = True
            tool_output_for_llm = fetched_content_str # This becomes the latest tool output

            if current_phase == ReactPhase.REFLECT:
                refined_prompt = f"Original user command: '{self.current_command}'.\nContent from URL:\n{tool_output_for_llm}\n\nBased on all this, what is the primary goal?"
            elif current_phase == ReactPhase.EVALUATE:
                refined_prompt = f"Current goal: '{original_task_description_for_phase}'.\nContent from URL:\n{tool_output_for_llm}\n\nConsidering this new information, what is the best approach?"
            elif current_phase == ReactPhase.ANALYZE:
                refined_prompt = f"Current goal: '{original_task_description_for_phase}'.\nContent from URL:\n{tool_output_for_llm}\n\nWhat are the logical steps to achieve this goal, considering this new information?"
            else:
                refined_prompt = f"Based on this fetched content from URL:\n{tool_output_for_llm}\n\nPlease now respond to the original request which was to address: {original_task_description_for_phase}"

            llm_response = await self.llm_client.generate_text(prompt=refined_prompt, context_history=self.conversation_history)
            if self._extract_search_query(llm_response) or self._extract_fetch_url_request(llm_response): llm_response = "Fetched content processed. Continuing with task."
        
        # The final llm_response (after potential tool use and re-prompting) is returned.
        # The tool_output_for_llm (if any tool was used) is also implicitly added to conversation_history
        # when the agent saves context at the end of process_command, by including tool phase summaries.
        return llm_response, tool_executed 

    async def _reflect(self) -> Tuple[str, List[str]]:
        thoughts = ["Starting REFLECT phase.", f"Interpreting user command: '{self.current_command}' considering history."]
        await self._send_update({"type": "thought", "phase": ReactPhase.REFLECT.value, "thought": thoughts[-1]})
        
        # Original task description for REFLECT is the user command itself.
        goal_prompt_for_llm = f"Understand and define the primary goal for the command: '{self.current_command}'. If information is missing or external data is needed, indicate what needs to be searched for using [SEARCH_QUERY: your query here] or fetched using [FETCH_URL: full_url_here]."
        initial_llm_response = await self.llm_client.generate_text(prompt=goal_prompt_for_llm, context_history=self.conversation_history)
        
        defined_goal, _ = await self._process_llm_response_for_tools(initial_llm_response, ReactPhase.REFLECT, self.current_command) # Pass self.current_command as original task
        
        thoughts.append(f"LLM response for goal definition: '{defined_goal}'.")
        await self._send_update({"type": "thought", "phase": ReactPhase.REFLECT.value, "thought": thoughts[-1]})
        thoughts.append("REFLECT phase complete.")
        await self._send_update({"type": "phase_summary", "phase": ReactPhase.REFLECT.value, "summary": f"Goal: {defined_goal}", "thoughts": thoughts})
        return defined_goal, thoughts

    async def _evaluate(self, goal: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        thoughts = ["Starting EVALUATE phase.", f"Goal: '{goal}'. Considering approaches. May use tools."]
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})

        # Original task description for EVALUATE is the defined goal.
        evaluate_prompt_for_llm = f"Goal: '{goal}'. Original command: '{self.current_command}'. Evaluate best approach (backend, frontend, mixed). Use [SEARCH_QUERY: query] or [FETCH_URL: url] if needed."
        initial_llm_response = await self.llm_client.generate_text(prompt=evaluate_prompt_for_llm, context_history=self.conversation_history)
        final_llm_response_for_eval, _ = await self._process_llm_response_for_tools(initial_llm_response, ReactPhase.EVALUATE, goal) # Pass goal as original task for this phase

        is_frontend_likely = any(term in final_llm_response_for_eval.lower() for term in ["frontend", "webpage", "ui"]) or \
                             any(term in self.current_command.lower() for term in ["webpage", "html", "frontend", "display", "ui", "button", "page"])
        approaches_list = [{"name": "Backend Python script"}, {"name": "Frontend HTML/CSS/JS bundle"}]
        selected_approach = approaches_list[1] if is_frontend_likely else approaches_list[0]
        
        thoughts.append(f"LLM eval response: '{final_llm_response_for_eval}'. Selected: {selected_approach['name']}.")
        await self._send_update({"type": "thought", "phase": ReactPhase.EVALUATE.value, "thought": thoughts[-1]})
        await self._send_update({"type": "phase_summary", "phase": ReactPhase.EVALUATE.value, "summary": f"Selected Approach: {selected_approach['name']}", "data": {"selected": selected_approach["name"], "llm_eval_response": final_llm_response_for_eval}, "thoughts": thoughts})
        return [selected_approach], thoughts

    async def _analyze(self, selected_approach: Dict[str, Any], goal: str) -> Tuple[List[str], List[str]]:
        thoughts = ["Starting ANALYZE phase.", f"Approach: '{selected_approach['name']}' for goal: '{goal}'. Defining steps. May use tools."]
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "thought": thoughts[-1]})

        # Original task description for ANALYZE is the goal and chosen approach.
        analyze_prompt_for_llm = f"Approach: '{selected_approach['name']}', Goal: '{goal}', Command: '{self.current_command}'. Define logical steps. Use [SEARCH_QUERY: query] or [FETCH_URL: url] if needed."
        initial_llm_response = await self.llm_client.generate_text(prompt=analyze_prompt_for_llm, context_history=self.conversation_history)
        final_llm_response_for_analyze, tool_used = await self._process_llm_response_for_tools(initial_llm_response, ReactPhase.ANALYZE, f"define steps for goal: {goal} using approach: {selected_approach['name']}")

        steps_from_llm = [step.strip() for step in final_llm_response_for_analyze.split("\n") if step.strip() and not step.strip().lower().startswith("sure") and not step.strip().lower().startswith("okay")]
        if not steps_from_llm: steps_from_llm = [f"LLM response was: {final_llm_response_for_analyze[:100]}..."]
        
        if not steps_from_llm or len(steps_from_llm) < 2 :
            steps = [f"Step derived from LLM (tool_used={tool_used}): {final_llm_response_for_analyze[:150]}..."]
            if "Frontend" in selected_approach['name']: steps.extend(["Define HTML structure.", "Style with CSS.", "Add JS interactivity if complex."])
            else: steps.extend(["Define main Python logic.", "Prepare for execution and testing."])
        else:
            steps = steps_from_llm

        thoughts.append(f"LLM defined steps: {steps} (based on response: '{final_llm_response_for_analyze}').")
        await self._send_update({"type": "thought", "phase": ReactPhase.ANALYZE.value, "thought": thoughts[-1]})
        await self._send_update({"type": "phase_summary", "phase": ReactPhase.ANALYZE.value, "summary": "Defined logical steps.", "data": {"steps": steps, "llm_analyze_response": final_llm_response_for_analyze}, "thoughts": thoughts})
        return steps, thoughts

    async def _generate_frontend_code_bundle(self, analysis_steps: List[str], tool_data_context: Optional[str] = None) -> bool:
        prompt_detail = f"Analysis Steps: {analysis_steps}. Original command: {self.current_command}."
        if tool_data_context: prompt_detail = f"Using information from previous tool use (search/fetch):\n{tool_data_context}\n\n{prompt_detail}"
        # ... (rest of method as before)
        thoughts = [f"Starting Frontend Code Generation. Tool context provided: {tool_data_context is not None}"]
        frontend_bundle = await self.llm_client.generate_frontend_bundle(prompt=prompt_detail, context_history=self.conversation_history)
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
        if tool_data_context: prompt_detail = f"Using information from previous tool use (search/fetch):\n{tool_data_context}\n\n{prompt_detail}"
        # ... (rest of method as before)
        thoughts = [f"Starting Backend Code Generation. Tool context provided: {tool_data_context is not None}"]
        generated_code = await self.llm_client.generate_code(prompt=prompt_detail, context_history=self.conversation_history)
        thoughts.append(f"LLM generated backend code:\n{generated_code}")
        self.output.set_generated_code(generated_code) 
        await self._send_update({"type": "code_generated", "phase": ReactPhase.ANALYZE.value, "sub_phase": "Backend Code Generation", "code": generated_code, "thought": thoughts[-1]})
        thoughts.append("Backend Code Generation complete.")
        return generated_code, thoughts

    async def _test(self, code_to_test: str, iteration: int) -> Tuple[Dict[str, Any], List[str]]: # Unchanged
        thoughts = [f"TEST (Iter {iteration}): Backend code:\n{code_to_test}"]
        await self._send_update({"type": "thought", "phase": ReactPhase.TEST.value, "iteration": iteration, "thought": thoughts[-1]})
        sim_results = {"status": "success", "stdout": "Simulated test success", "stderr": "", "result": "Test passed"}
        if "error" in self.current_command.lower() and "backend test" in self.current_command.lower() and iteration == 1:
            sim_results = {"status": "failure", "stdout": "", "stderr": "Simulated test error", "result": "Test failed"}
        self.output.set_test_results(sim_results)
        await self._send_update({"type": "test_result", "phase": ReactPhase.TEST.value, "iteration": iteration, "results": sim_results, "thought": "Test completed."})
        return sim_results, thoughts

    async def _correct(self, test_results: Dict[str, Any], iteration: int) -> Tuple[bool, List[str]]: # Unchanged
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

        goal, reflect_thoughts = await self._reflect() # Uses _process_llm_response_for_tools
        self.output.add_phase_info(ReactPhase.REFLECT, reflect_thoughts, f"Goal: {goal}"); self.current_thoughts.extend(reflect_thoughts)
        
        approaches, eval_thoughts = await self._evaluate(goal) # Uses _process_llm_response_for_tools
        selected_approach_info = approaches[0]
        self.output.add_phase_info(ReactPhase.EVALUATE, eval_thoughts, f"Approach: {selected_approach_info['name']}", data=approaches); self.current_thoughts.extend(eval_thoughts)

        steps, analyze_thoughts = await self._analyze(selected_approach_info, goal) # Uses _process_llm_response_for_tools
        self.output.add_phase_info(ReactPhase.ANALYZE, analyze_thoughts, "Steps defined", data={"steps": steps}); self.current_thoughts.extend(analyze_thoughts)
        
        tool_data_for_code_gen: Optional[str] = None 
        if self.output.phases_info: # Check if any phases (and thus potential tool uses) have occurred
            # Check the very last phase that might have tool output
            # Note: _process_llm_response_for_tools itself doesn't add to phases_info directly for "Tool Output Used"
            # It's the _perform_search/fetch methods that add SEARCH/FETCH_URL phases.
            for phase_entry in reversed(self.output.phases_info):
                if phase_entry["phase"] == ReactPhase.SEARCH.value:
                    results = phase_entry.get("data", {}).get("results", [])
                    if results and not (len(results)==1 and results[0].get("error")): 
                        # Use the improved formatting for re-prompting
                        tool_data_for_code_gen = "Search Results:\n"
                        for i, res in enumerate(results[:3]): # Consistent with _perform_search_if_needed
                            title = res.get('title', 'N/A'); url = res.get('url', 'N/A'); snippet = res.get('content', 'N/A')[:300]
                            tool_data_for_code_gen += f"{i+1}. Title: {title}\n   URL: {url}\n   Snippet: {snippet}...\n"
                        tool_data_for_code_gen = tool_data_for_code_gen.strip()
                    break # Found the last tool usage
                elif phase_entry["phase"] == ReactPhase.FETCH_URL.value:
                    # For fetched content, the actual content is returned by _perform_url_fetch_if_needed
                    # and used in the re-prompt within _process_llm_response_for_tools.
                    # If we want to pass it *again* to code gen, we need to store it more accessibly
                    # or retrieve it from the conversation_history (if LLM included it).
                    # For now, if FETCH_URL was the last tool phase, we'll assume its output was incorporated
                    # into the LLM's response that led to the 'steps'. A more robust solution might be needed here.
                    # For simplicity, we'll assume the LLM's output (now in 'steps') has summarized or used the fetched content.
                    # If direct fetched content is needed, it must be explicitly passed/stored.
                    # For now, let's try to get it from the data if `_perform_url_fetch_if_needed` stored it.
                    # However, `_perform_url_fetch_if_needed` returns string, not stored in phase_info's data.
                    # The data stored is: data={"url": url_to_fetch, "content_length": len(content or '')} or error.
                    # This means tool_data_for_code_gen will not directly contain fetched content from this logic.
                    # This is a known limitation of the current simplified tool_data_for_code_gen retrieval.
                    pass
                    break # Found the last tool usage
        
        # ... (rest of process_command with code gen, test, correct, save context) ...
        if "Frontend" in selected_approach_info['name']:
            generated = await self._generate_frontend_code_bundle(steps, tool_data_context=tool_data_for_code_gen)
            self.output.final_output = "Frontend bundle generated." if generated else "Frontend generation failed."
        else:
            generated_code, code_gen_thoughts = await self._generate_code_and_prepare_test(steps, tool_data_context=tool_data_for_code_gen)
            self.current_thoughts.extend(code_gen_thoughts)
            self.output.add_phase_info(ReactPhase.ANALYZE, code_gen_thoughts, "Backend Code Gen (post-tool)", data={}) 
            if not generated_code: self.output.add_error("Backend code gen failed."); self.output.final_output = "Backend code gen failed."
            else: 
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

        assistant_summary = {"role": "assistant", "summary": self.output.final_output or "Processing complete.", "code_type": "python" if self.output.generated_code else ("frontend" if self.output.frontend_html else "none"), "errors": bool(self.output.errors)}
        self.conversation_history.append(assistant_summary)
        MAX_HIST = 10; self.conversation_history = self.conversation_history[-(MAX_HIST*2):] if len(self.conversation_history) > MAX_HIST*2 else self.conversation_history
        await redis_client.save_agent_context(user_id, session_id, {"conversation_history": self.conversation_history})
        
        await self._send_update({"type": "process_end", "status": "success" if not self.output.errors else "failure", "final_output": self.output.final_output})
        return self.output

async def dummy_callback(update_data: Dict):
    print(f"DUMMY CALLBACK: {update_data.get('type')} - Phase: {update_data.get('phase')} - Action: {update_data.get('action')} - Query/URL: {update_data.get('query', update_data.get('url','N/A'))} - Msg: {update_data.get('message', update_data.get('thought', ''))[:150]}")

async def main(): # Test function
    await redis_client.init_redis_pool()
    if not redis_client.redis_pool: print("CRITICAL: Redis pool failed."); return
    
    # Ensure config is set to placeholder for this test to control LLMClient behavior for tools
    original_provider = config.LLM_PROVIDER
    config.LLM_PROVIDER = "placeholder"
    agent = AutonomousAgent() 
    
    test_user = "test_tool_refine_user"; test_session = "tool_refine_session_1"
    await redis_client.delete_agent_context(test_user, test_session)

    cmd1 = "search for the best python libraries for web scraping and then fetch content from the homepage of the top one found"
    print(f"\n--- CMD 1: {cmd1} ---"); 
    out1 = await agent.process_command(cmd1, test_user, test_session, dummy_callback)
    print(f"Output 1 Final: {out1.final_output}, Errors: {out1.errors}")
    
    # Check conversation history to see if tool results were incorporated
    # final_context = await redis_client.load_agent_context(test_user, test_session)
    # print("\nFinal Conversation History for CMD1:")
    # if final_context and final_context.get("conversation_history"):
    #     for turn in final_context["conversation_history"]:
    #         print(f"  {turn['role']}: {turn.get('summary', turn.get('content',''))[:200]}")

    cmd2 = "Based on the content from the previous step, write a python script to list all H2 headings."
    print(f"\n--- CMD 2: {cmd2} ---");
    out2 = await agent.process_command(cmd2, test_user, test_session, dummy_callback)
    print(f"Output 2 Final: {out2.final_output}, Errors: {out2.errors}, Generated Code: {out2.generated_code is not None}")
    if out2.generated_code: print(f"Code:\n{out2.generated_code}")


    config.LLM_PROVIDER = original_provider # Restore original provider
    await redis_client.close_redis_pool()

if __name__ == "__main__":
    asyncio.run(main())
