"""
Distributed Swarm Networking Module (v6.0)
P2P inference sharing across local network.
"""

import socket
import asyncio
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

app = FastAPI()

class SwarmRequest(BaseModel):
    messages: List[Dict[str, str]]
    task: str = "chat"
    parameters: Dict = {}

@app.post("/inference")
async def inference_endpoint(request: SwarmRequest):
    """Slave Node inference endpoint"""
    try:
        from local_engine import get_inference
        engine = get_inference()
        if not engine.is_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded on slave node")
        
        result = engine.chat(request.messages)
        return {"response": result, "node": socket.gethostname()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SwarmNode:
    def __init__(self, port=8080):
        self.port = port
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.zeroconf = Zeroconf()
        self.discovered_nodes = {} # {name: ip}

    def start_advertising(self):
        """Broadcast existence to the local network"""
        info = ServiceInfo(
            "_ai-ide._tcp.local.",
            f"{self.hostname}._ai-ide._tcp.local.",
            addresses=[socket.inet_aton(self.ip)],
            port=self.port,
            properties={"node_type": "slave"},
        )
        self.zeroconf.register_service(info)
        print(f"📡 Advertising slave node at {self.ip}:{self.port}")

    def start_discovery(self):
        """Look for other slaves on the network"""
        class DiscoveryListener:
            def __init__(self, parent): self.parent = parent
            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info:
                    self.parent.discovered_nodes[name] = socket.inet_ntoa(info.addresses[0])
            def update_service(self, *args): pass
            def remove_service(self, zc, type_, name):
                if name in self.parent.discovered_nodes: del self.parent.discovered_nodes[name]

        self.browser = ServiceBrowser(self.zeroconf, "_ai-ide._tcp.local.", DiscoveryListener(self))

    def stop(self):
        self.zeroconf.unregister_all_services()
        self.zeroconf.close()
