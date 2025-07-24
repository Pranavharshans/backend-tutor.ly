from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import uuid
import os

app = FastAPI()
OUTPUT_DIR = "static"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/render")
async def render(request: Request):
    data = await request.json()
    script = data.get("script")
    if not script:
        return JSONResponse({"error": "No script provided"}, status_code=400)

    # Save script to file
    script_id = str(uuid.uuid4())
    script_path = f"/tmp/{script_id}.py"
    with open(script_path, "w") as f:
        f.write(script)

    # Run Manim
    output_file = f"{script_id}.mp4"
    try:
        subprocess.run([
            "manim", script_path, "VideoScene",
            "-o", output_file, "-qk", "--disable_caching"
        ], check=True)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    # Move video to static dir
    src_path = f"media/videos/{output_file}"
    dst_path = os.path.join(OUTPUT_DIR, output_file)
    if os.path.exists(src_path):
        os.rename(src_path, dst_path)
    else:
        return JSONResponse({"error": "Video not found after rendering"}, status_code=500)

    # Return public URL
    video_url = f"/static/{output_file}"
    return {"videoUrl": video_url}

@app.get("/static/{filename}")
async def get_video(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    return JSONResponse({"error": "File not found"}, status_code=404)
