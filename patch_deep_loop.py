import sys
import re

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Initialize total_steps
if "st.session_state.total_steps = 1" not in content:
    content = content.replace("st.session_state.omni_step = 1", "st.session_state.omni_step = 1\\n        st.session_state.total_steps = 1")
    # Also in the "Resume Previous Session" block
    content = content.replace("st.session_state.omni_step = existing_cp.get(\"step\", 1)", "st.session_state.omni_step = existing_cp.get(\"step\", 1)\\n                    st.session_state.total_steps = existing_cp.get(\"total_steps\", existing_cp.get(\"step\", 1))")

# 2. Increment total_steps everywhere omni_step is incremented
content = content.replace("st.session_state.omni_step += 1", "st.session_state.omni_step += 1\\n                st.session_state.total_steps += 1")
# We might have introduced duplicates if we run it twice, but let's assume one run.

# 3. Replace the GENERATING check block
old_gen_block = """        # Handle current state
        if st.session_state.omni_state == "GENERATING":
            if st.session_state.omni_step > st.session_state.max_steps:
                current_phase = st.session_state.get("phase", 1)
                
                if st.session_state.max_steps >= 999:
                    # LONG-RUNNING MODE: Phase transition instead of termination
                    phase_summary = build_phase_summary(st.session_state.omni_log)
                    if "phase_summaries" not in st.session_state:
                        st.session_state.phase_summaries = []
                    st.session_state.phase_summaries.append(phase_summary)
                    
                    # Save checkpoint before phase transition
                    save_checkpoint(workspace_dir, dict(st.session_state))
                    
                    # Re-ingest codebase with fresh eyes (files may have changed!)
                    st.info("♻️ Phase {} complete. Re-ingesting codebase for Phase {}...".format(current_phase, current_phase + 1))
                    status_box = st.empty()
                    messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)
                    
                    # Inject prior phase summaries into the new system prompt
                    prior_context = "\\n".join(["Phase {}: {}".format(i+1, s) for i, s in enumerate(st.session_state.phase_summaries)])
                    messages[0]["content"] += "\\n\\nPRIOR PHASE SUMMARIES (your own earlier work):\\n" + prior_context
                    
                    st.session_state.omni_messages = messages
                    st.session_state.omni_log = [{
                        "step": 0,
                        "type": "blueprint",
                        "blueprint": blueprint
                    }]
                    st.session_state.omni_step = 1
                    st.session_state.action_history = []
                    st.session_state.phase = current_phase + 1
                    st.session_state.max_steps = 999  # keep going
                    st.info("♻️ Phase {} -> Phase {}. Fresh context window, persistent memory.".format(current_phase, current_phase + 1))
                    st.rerun()
                else:
                    # Normal mode: terminate
                    save_checkpoint(workspace_dir, dict(st.session_state))
                    st.error("Max steps reached. Session checkpointed.")
                    st.session_state.omni_state = "DONE"
                    st.rerun()"""

new_gen_block = """        # Handle current state
        if st.session_state.omni_state == "GENERATING":
            # 1. Absolute Termination Guard
            if st.session_state.total_steps > st.session_state.max_steps:
                save_checkpoint(workspace_dir, dict(st.session_state))
                st.error(f"Max total steps ({st.session_state.max_steps}) reached across all phases.")
                st.session_state.omni_state = "DONE"
                st.rerun()
                
            # 2. Context Window Overflow Guard (Phase Transition)
            # A typical local model context window (8k) overflows around 10-15 deep tool steps.
            # We flush at 10 steps to guarantee stability.
            if st.session_state.omni_step > 10:
                current_phase = st.session_state.get("phase", 1)
                
                phase_summary = build_phase_summary(st.session_state.omni_log)
                if "phase_summaries" not in st.session_state:
                    st.session_state.phase_summaries = []
                st.session_state.phase_summaries.append(phase_summary)
                
                # Save checkpoint before phase transition
                save_checkpoint(workspace_dir, dict(st.session_state))
                
                st.info(f"♻️ Context window nearing capacity (10 steps). Compressing Phase {current_phase} and re-ingesting codebase...")
                status_box = st.empty()
                messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)
                
                # Inject compressed memory of all prior phases
                prior_context = "\\n".join([f"Phase {i+1}: {s}" for i, s in enumerate(st.session_state.phase_summaries)])
                messages[0]["content"] += "\\n\\nPRIOR PHASE SUMMARIES (your own earlier work):\\n" + prior_context
                
                st.session_state.omni_messages = messages
                st.session_state.omni_log = [{
                    "step": 0,
                    "type": "blueprint",
                    "blueprint": blueprint
                }]
                st.session_state.omni_step = 1
                st.session_state.action_history = []
                st.session_state.phase = current_phase + 1
                st.info(f"♻️ Phase {current_phase} -> Phase {current_phase + 1}. Context flushed. Memory preserved.")
                st.rerun()"""

if old_gen_block in content:
    content = content.replace(old_gen_block, new_gen_block)
    with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
        f.write(content)
    print("Deep iterations patched.")
else:
    print("Could not find the block to replace!")
