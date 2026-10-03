import io
import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import modal

# 1. Define the Modal App
app = modal.App("artstyle-backend-fastapi")

# 2. Storage Volume for generated images so the frontend can retrieve them via URL
volume = modal.Volume.from_name("artstyle-images-volume", create_if_missing=True)

# 3. Create the Backend environment (Linux container with dependencies)
def download_models():
    """Cache the SDXL model during the build phase so cold-starts are fast."""
    from diffusers import AutoPipelineForImage2Image
    import torch
    AutoPipelineForImage2Image.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi[standard]", 
        "diffusers", 
        "transformers", 
        "accelerate", 
        "torch", 
        "pillow"
    )
    .run_function(download_models)
)

web_app = FastAPI()

# Important: Allow CORS since the React frontend fetches this from a different domain
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. The GPU Class handles the heavy lifting
@app.cls(image=image, gpu="A10G", timeout=600)
class SDXLModel:
    @modal.enter()
    def load_weights(self):
        from diffusers import AutoPipelineForImage2Image
        import torch
        # Load the pipeline directly into the GPU
        self.pipe = AutoPipelineForImage2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", 
            torch_dtype=torch.float16, 
            variant="fp16"
        )
        self.pipe.to("cuda")

    @modal.method()
    def generate(self, init_image_bytes, prompt, num_inference_steps, guidance_scale):
        from PIL import Image
        import io
        init_image = Image.open(io.BytesIO(init_image_bytes)).convert("RGB")
        # Resize to avoid Out-Of-Memory errors on the GPU
        init_image = init_image.resize((768, 768))

        output_image = self.pipe(
            prompt, 
            image=init_image, 
            num_inference_steps=int(num_inference_steps), 
            guidance_scale=float(guidance_scale),
            strength=0.55 # The secret to impressive style transfer!
        ).images[0]
        
        output_io = io.BytesIO()
        output_image.save(output_io, format="JPEG")
        return output_io.getvalue()

# 5. FastAPI Endpoints
@web_app.post("/generate_with_image")
async def generate_with_image(
    file: UploadFile = File(...),
    artwork_name: str = Form(""),
    artist_name: str = Form(""),
    prompt: str = Form(""),
    negative_prompt: str = Form(""),
    num_inference_steps: str = Form("50"),
    guidance_scale: str = Form("7")
):
    try:
        # Construct the conditioning prompt from frontend data
        conditioning_prompt = f"A high quality digital painting in the exact art style of {artwork_name} by {artist_name}. {prompt}".strip()
        
        image_bytes = await file.read()
        
        # Ship parameters to the GPU function
        sdxl = SDXLModel()
        generated_bytes = sdxl.generate.remote(
            init_image_bytes=image_bytes,
            prompt=conditioning_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale
        )
        
        # Save to the shared Modal Volume
        filename = f"{uuid.uuid4()}.jpg"
        save_path = f"/data/images/{filename}"
        
        os.makedirs("/data/images", exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(generated_bytes)
        volume.commit()  # Synchronize volume state
        
        return {
            "status": "success",
            "image_url_refined": f"/images/{filename}"
        }
    except Exception as e:
        print(f"Error during generation: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@web_app.get("/images/{image_name}")
async def get_image(image_name: str):
    # Reload volume to ensure we have latest files from other containers
    volume.reload()
    file_path = f"/data/images/{image_name}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"message": "Image not found"})

# 6. Bind FastAPI to Modal Apps
@app.function(image=image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_app():
    return web_app
