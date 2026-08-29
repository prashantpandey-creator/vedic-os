"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Send, Server, Loader2, CheckCircle2 } from "lucide-react";

export default function OmniAgent() {
  const [intent, setIntent] = useState("");
  const [logs, setLogs] = useState<{ type: string; msg?: string; action?: string; args?: any }[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isComputing, setIsComputing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const startAgent = () => {
    if (!intent.trim()) return;
    
    setLogs([]);
    setIsComputing(true);
    
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/agent");
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ intent, workspace: "/Users/badenath/projects/local-llm-ui" }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLogs((prev) => [...prev, data]);
      if (data.msg === "✅ Task Complete!") {
        setIsComputing(false);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsComputing(false);
    };
  };

  const stopAgent = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex items-center justify-between border-b border-neutral-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Server className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Vedic Omni-Agent</h1>
              <p className="text-sm text-neutral-400">Decoupled FastAPI Engine (WebSockets)</p>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center space-x-2 ${isConnected ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            <span>{isConnected ? "Engine Connected" : "Engine Offline"}</span>
          </div>
        </header>

        {/* Input Area */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
          <div className="flex space-x-3">
            <input
              type="text"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g., 'Run npm test, find the failing cases, and fix the bugs in core/utils.py'"
              className="flex-1 bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-neutral-100 placeholder:text-neutral-600"
              onKeyDown={(e) => e.key === 'Enter' && startAgent()}
              disabled={isComputing}
            />
            {isComputing ? (
              <button onClick={stopAgent} className="bg-red-500 hover:bg-red-600 text-white px-6 rounded-lg font-medium transition-colors">
                Stop
              </button>
            ) : (
              <button onClick={startAgent} className="bg-blue-600 hover:bg-blue-700 text-white px-6 rounded-lg font-medium flex items-center space-x-2 transition-colors">
                <Send className="w-4 h-4" />
                <span>Launch</span>
              </button>
            )}
          </div>
        </div>

        {/* Streaming Logs */}
        <div className="space-y-4">
          {logs.map((log, i) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={i}
              className={`p-4 rounded-xl border ${
                log.type === "status" ? "bg-neutral-900 border-neutral-800" :
                log.type === "thought" ? "bg-blue-950/20 border-blue-900/50" :
                log.type === "action" ? "bg-purple-950/20 border-purple-900/50" :
                "bg-neutral-950 border-neutral-800 font-mono text-sm"
              }`}
            >
              {log.type === "status" && (
                <div className="flex items-center space-x-2 text-neutral-300">
                  {log.msg?.includes("Complete") ? <CheckCircle2 className="w-4 h-4 text-green-400" /> : <Loader2 className="w-4 h-4 animate-spin text-blue-400" />}
                  <span>{log.msg}</span>
                </div>
              )}
              
              {log.type === "thought" && (
                <div>
                  <div className="text-xs text-blue-400 font-semibold mb-2 uppercase tracking-wider">Agent Reflection</div>
                  <div className="text-neutral-300 leading-relaxed whitespace-pre-wrap">{log.msg}</div>
                </div>
              )}

              {log.type === "action" && (
                <div>
                  <div className="text-xs text-purple-400 font-semibold mb-2 uppercase tracking-wider flex items-center space-x-2">
                    <Terminal className="w-3 h-3" />
                    <span>Executing Tool: {log.action}</span>
                  </div>
                  <pre className="text-neutral-400 bg-neutral-950 p-3 rounded-lg overflow-x-auto">
                    {JSON.stringify(log.args, null, 2)}
                  </pre>
                </div>
              )}

              {log.type === "tool_result" && (
                <div>
                  <div className="text-xs text-neutral-500 font-semibold mb-2 uppercase tracking-wider">Terminal Output</div>
                  <pre className="text-green-400 whitespace-pre-wrap overflow-x-auto">
                    {log.msg}
                  </pre>
                </div>
              )}
            </motion.div>
          ))}
        </div>

      </div>
    </div>
  );
}
