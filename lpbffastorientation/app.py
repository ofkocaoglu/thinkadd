from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import trimesh
import uuid

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory mesh storage (for demo)
meshes = {}

@app.post("/upload_stl")
async def upload_stl(file: UploadFile = File(...)):
    try:
        mesh_data = await file.read()
        import io
        mesh = trimesh.load_mesh(io.BytesIO(mesh_data), file_type='stl')
        mesh_id = str(uuid.uuid4())
        meshes[mesh_id] = mesh
        return {
            "mesh_id": mesh_id,
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist()
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analyze_overhang")
async def analyze_overhang(mesh_id: str, overhang_angle: float):
    mesh = meshes.get(mesh_id)
    if mesh is None:
        return JSONResponse(status_code=404, content={"error": "Mesh not found"})
    # Placeholder: Compute overhangs and supports
    return {"supports": []}

@app.websocket("/ws/optimize_orientation/{mesh_id}")
async def optimize_orientation(websocket: WebSocket, mesh_id: str):
    await websocket.accept()
    mesh = meshes.get(mesh_id)
    if mesh is None:
        await websocket.send_json({"error": "Mesh not found"})
        await websocket.close()
        return
    # Placeholder: Sample orientations, compute support volumes, send updates
    try:
        for i in range(100):
            orientation = np.random.uniform(-180, 180, size=3).tolist()
            support_volume = np.random.uniform(0, 1000)  # Dummy value
            await websocket.send_json({
                "orientation": orientation,
                "support_volume": support_volume,
                "iteration": i + 1
            })
        await websocket.close()
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)