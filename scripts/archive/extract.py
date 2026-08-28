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
                    prior_context = "\n".join(["Phase {}: {}".format(i+1, s) for i, s in enumerate(st.session_state.phase_summaries)])
                    messages[0]["content"] += "\n\nPRIOR PHASE SUMMARIES (your own earlier work):\n" + prior_context
                    
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
                    st.rerun()
                
            st.write(f"🦅 **[STEP {st.session_state.omni_step}/{st.session_state.max_steps}]** Thinking...")
            step_container = st.container()
            step_placeholder = step_container.empty()
            
            raw_response = generate_next_thought(coder_model, st.session_state.omni_messages, step_placeholder)
            st.session_state.omni_messages.append({"role": "assistant", "content": raw_response})
            action_data = parse_action(raw_response)
            
