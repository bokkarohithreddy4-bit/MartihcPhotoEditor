import os
import uuid
import base64
from typing import Optional
from io import BytesIO
import modal
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
app = modal.App("sdxl-text2img-api2")
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
image_volume = modal.Volume.from_name("sdxl-images", create_if_missing=True)
db_vol = modal.Volume.from_name("database_style_transfer", create_if_missing=False)
MOUNT_PATH = "/data"
DB_VOL_MOUNT = "/mnt/db_volume"     
DB_TOPFOLDER_NAME = "database_style_transfer"

PERSONAS_DIR_IN_IMAGE = None
ARTWORK_KNOWLEDGE_DIR = None
ICONO_WORK_KNOWLEDGE_DIR = None

def resolve_db_paths():
    """
    Resolve personas, art_work_knowledge, iconography_work_knowledge directories
    inside the mounted db volume. Accepts either 'personas' or 'persona'.
    Returns tuple (PERSONAS_DIR, ARTWORK_KNOWLEDGE_DIR, ICONO_WORK_KNOWLEDGE_DIR).
    """
    base = os.path.join(DB_VOL_MOUNT, DB_TOPFOLDER_NAME)
    if not os.path.exists(base):
        raise RuntimeError(
            f"Expected top-level folder not found inside mounted volume: {base}. "
            "Make sure your volume contains the `database_style_transfer` folder."
        )

    personas_candidate = os.path.join(base, "personas")
    personas_candidate_alt = os.path.join(base, "persona")
    if os.path.exists(personas_candidate):
        PERSONAS_DIR = personas_candidate
    elif os.path.exists(personas_candidate_alt):
        PERSONAS_DIR = personas_candidate_alt
    else:
        PERSONAS_DIR = personas_candidate

    ARTWORK_KNOWLEDGE_DIR = os.path.join(base, "art_work_knowledge")
    ICONO_WORK_KNOWLEDGE_DIR = os.path.join(base, "iconography_work_knowledge")

    return PERSONAS_DIR, ARTWORK_KNOWLEDGE_DIR, ICONO_WORK_KNOWLEDGE_DIR


def write_to_file(path: str, text: str):
    """Helper to write text to a file, creating dirs if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def encode_image(image_path: str) -> str:
    """Encode an image file as base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def encode_image_to_markdown(path: str) -> str:
    """
    Return markdown string embedding the image as base64.
    Resizes image to max 512px to prevent token/exchange issues.
    """
    with Image.open(path) as img:
        img.thumbnail((512, 512))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"![image](data:image/png;base64,{b64})"

sdxl_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "torch",
        "diffusers",
        "transformers",
        "fastapi[standard]",
        "uvicorn",
        "Pillow",
        "openai",
        "ag2[openai]",
    )
    # NOTE:
)
class GenerateRequest(BaseModel):
    artwork_name: str
    artist_name: str  
    prompt: Optional[str] = None  
    negative_prompt: Optional[str] = None
    num_inference_steps: int = 50
    guidance_scale: float = 7.0


@app.function(
    image=sdxl_image,
    gpu="H100",
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        MOUNT_PATH: image_volume,
        DB_VOL_MOUNT: db_vol,
    },
    timeout=20,
    allow_concurrent_inputs=60,
    secrets=[modal.Secret.from_name("openrouter-secret")],
)
@modal.asgi_app()
def fastapi_app():
    """
    SDXL text2img server with multi-agent refinement.

    Behavior: if an uploaded image is provided via /generate_with_image, the service
    will use that uploaded image as the "first image" for art & iconography analysis
    (and for the Socratic loop) — the SDXL first-generation is skipped. The rest of the
    pipeline is unchanged.
    """
    import torch
    from diffusers import DiffusionPipeline
    from openai import OpenAI
    from autogen import AssistantAgent

    global PERSONAS_DIR_IN_IMAGE, ARTWORK_KNOWLEDGE_DIR, ICONO_WORK_KNOWLEDGE_DIR

    api = FastAPI(title="SDXL Persona Text2Img + Multi-Agent Refinement")

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    os.makedirs(MOUNT_PATH, exist_ok=True)
    api.mount("/images", StaticFiles(directory=MOUNT_PATH), name="images")
    MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

    print(f"Loading SDXL pipeline: {MODEL_ID}")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipe = DiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    pipe.to(device)
    print("SDXL pipeline loaded and ready on", device)
    try:
        PERSONAS_DIR_IN_IMAGE, ARTWORK_KNOWLEDGE_DIR, ICONO_WORK_KNOWLEDGE_DIR = resolve_db_paths()
        print("Resolved DB dirs:", PERSONAS_DIR_IN_IMAGE, ARTWORK_KNOWLEDGE_DIR, ICONO_WORK_KNOWLEDGE_DIR)
    except Exception as e:
        print("Database volume structure problem (during startup resolve):", e)
        raise
    print("VERIFYING COPIED / MOUNTED DIRECTORIES...")

    def list_dir(label, path):
        print(f"\n--- {label}: {path} ---")
        if not os.path.exists(path):
            print("DOES NOT EXIST")
            return
        any_items = False
        for root, dirs, files in os.walk(path):
            any_items = True
            print(f"[DIR] {root}")
            for d in sorted(dirs):
                print(f"  - (folder) {d}")
            for f in sorted(files):
                print(f"  - (file)   {f}")
        if not any_items:
            print(" EXISTS BUT IS EMPTY")

    list_dir("Personas", PERSONAS_DIR_IN_IMAGE)
    list_dir("Art Work Knowledge", ARTWORK_KNOWLEDGE_DIR)
    list_dir("Iconography Knowledge", ICONO_WORK_KNOWLEDGE_DIR)

    print("DIRECTORY VERIFICATION COMPLETE\n")
    try:
        _ = pipe(
            prompt="warmup prompt, ignore this",
            num_inference_steps=1,
            guidance_scale=1.0,
        ).images
        print("SDXL warmup done.")
    except Exception as e:
        print(f"SDXL warmup failed (continuing): {e}")
    api_key = (
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("openrouter_api_key")
    )
    print("API key loaded?", bool(api_key))

    if not api_key:
        print("Env keys at startup:", list(os.environ.keys()))
        raise RuntimeError(
            "No OpenRouter API key found. Make sure Modal secret 'openrouter-secret' "
            "contains either OPENROUTER_API_KEY or openrouter_api_key."
        )
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://modal-sdxl-app",
            "X-Title": "sdxl-text2img-api2",
        },
    )
    @api.get("/")
    async def root():
        return {
            "status": "ok",
            "service": "SDXL Text2Img with Personas + Multi-Agent Refinement",
            "model": MODEL_ID,
            "device": device,
        }

    @api.post("/generate")
    async def generate(req: GenerateRequest):
        return await _shared_generate_flow(
            client=client,
            pipe=pipe,
            req_data={
                "artwork_name": req.artwork_name,
                "artist_name": req.artist_name,
                "prompt": req.prompt,
                "negative_prompt": req.negative_prompt,
                "num_inference_steps": req.num_inference_steps,
                "guidance_scale": req.guidance_scale,
                "uploaded_image_path": None,
            },
        )
    @api.post("/generate_with_image")
    async def generate_with_image(
        artwork_name: str = Form(...),
        artist_name: str = Form(...),
        prompt: Optional[str] = Form(None),
        negative_prompt: Optional[str] = Form(None),
        num_inference_steps: int = Form(50),
        guidance_scale: float = Form(7.0),
        file: Optional[UploadFile] = File(None),
    ):
        uploaded_image_path = None
        if file is not None:
            filename = f"uploaded_{uuid.uuid4().hex}_{file.filename}"
            uploaded_image_path = os.path.join(MOUNT_PATH, filename)
            with open(uploaded_image_path, "wb") as out_f:
                out_f.write(await file.read())
            print(f"Saved uploaded image to: {uploaded_image_path}")

        return await _shared_generate_flow(
            client=client,
            pipe=pipe,
            req_data={
                "artwork_name": artwork_name,
                "artist_name": artist_name,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "uploaded_image_path": uploaded_image_path,
            },
        )

    async def _shared_generate_flow(client, pipe, req_data):
        """
        Shared logic for JSON and form endpoints.

        CHANGE: If uploaded_image_path is provided, skip first SDXL generation and
        use uploaded image as the first image (for analysis + Socratic loop).
        """
        artwork_name = req_data["artwork_name"]
        artist_name = req_data["artist_name"]
        prompt_param = req_data.get("prompt")
        negative_prompt = req_data.get("negative_prompt")
        num_inference_steps = req_data.get("num_inference_steps")
        guidance_scale = req_data.get("guidance_scale")
        uploaded_image_path = req_data.get("uploaded_image_path")
        if not artwork_name or not artwork_name.strip():
            raise HTTPException(400, "artwork_name cannot be empty")
        if not artist_name or not artist_name.strip():
            raise HTTPException(400, "artist_name cannot be empty")
        prompt_og = None
        if uploaded_image_path:
            try:
                image_data_url_for_caption = f"data:image/png;base64,{encode_image(uploaded_image_path)}"
                caption_resp = client.responses.create(
                    model="google/gemma-3-27b-it",
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_image", "image_url": image_data_url_for_caption},
                                {
                                    "type": "input_text",
                                    "text": (
                                        "Provide a single concise caption (one short sentence) that describes the image "
                                        "and is suitable as a seed prompt for SDXL generation. Keep it under 20 words."
                                    ),
                                },
                            ],
                        }
                    ],
                )
                caption = caption_resp.output_text.strip()
                prompt_og = caption
                print(f"Caption from OpenAI: {caption}")
            except Exception as e:
                print(f"Error obtaining caption from OpenAI: {e}")
                if prompt_param and prompt_param.strip():
                    prompt_og = prompt_param.strip()
                else:
                    raise HTTPException(500, f"Failed to caption uploaded image: {e}")
        else:
            # No uploaded image: require prompt
            if not prompt_param or not prompt_param.strip():
                raise HTTPException(400, "prompt cannot be empty when no image is uploaded")
            prompt_og = prompt_param.strip()

        artist_normalized = artist_name.strip().lower()

        # persona path: resolved from DB volume
        persona_path = os.path.join(PERSONAS_DIR_IN_IMAGE, f"{artist_normalized}_persona.txt")
        if not os.path.exists(persona_path):
            raise HTTPException(400, f"Persona file not found for artist '{artist_normalized}'. Expected: {persona_path}")
        with open(persona_path, "r", encoding="utf-8") as f:
            persona = f.read().strip()

        # Load art and iconography knowledge
        artwork_file = os.path.join(ARTWORK_KNOWLEDGE_DIR, f"{artwork_name}.txt")
        if not os.path.exists(artwork_file):
            raise HTTPException(400, f"art_work_knowledge file missing for artwork '{artwork_name}'. Expected: {artwork_file}")
        with open(artwork_file, "r", encoding="utf-8") as f:
            art_work_knowledge = f.read().strip()

        icono_file = os.path.join(ICONO_WORK_KNOWLEDGE_DIR, f"{artwork_name}.txt")
        if not os.path.exists(icono_file):
            raise HTTPException(400, f"iconography_work_knowledge file missing for artwork '{artwork_name}'. Expected: {icono_file}")
        with open(icono_file, "r", encoding="utf-8") as f:
            iconographic_work_knowledge = f.read().strip()

        print(f"\nUsing persona from: {persona_path}\nartwork_name = {artwork_name!r}, prompt_og = {prompt_og!r}, artist = {artist_normalized!r}")

        try:
            response = client.responses.create(
                model="openai/gpt-oss-120b",
                input=[
                    {
                        "role": "system",
                        "content": (
                            f"{persona}. You are writing the prompt for SDXL, "
                            "a new canvas for you. Use your artistry to explain everything "
                            "in 70 tokens only. Include the color palette details and explain "
                            "how each object in the prompt should be drawn."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Transform this {prompt_og} based on how you would have drawn "
                            "this in that era."
                        ),
                    },
                ],
            )
            prompt_final = response.output_text
        except Exception as e:
            print(f"Error in OpenAI prompt generator: {e}")
            raise HTTPException(500, f"Failed to generate SDXL prompt: {e}")

        print(f"\nprompt_final from OpenAI:\n{prompt_final}\n")
        prompts_dir = os.path.join(MOUNT_PATH, "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        prompt_file_path = os.path.join(prompts_dir, f"prompt_final_{uuid.uuid4().hex}.txt")
        write_to_file(prompt_file_path, prompt_final)
        print(f"Saved prompt_final to: {prompt_file_path}")
        if uploaded_image_path:
            image1_path = uploaded_image_path
            image1_url = f"/images/{os.path.basename(image1_path)}"
            try:
                img1 = Image.open(image1_path).convert("RGBA")
            except Exception:
                img1 = Image.open(image1_path)
            print(f"Using uploaded image as FIRST image for analysis: {image1_path}")
            base64_image = encode_image(image1_path)
            image_data_url = f"data:image/png;base64,{base64_image}"
        else:
            print(f"Generating FIRST image with SDXL for: {prompt_final!r}")
            try:
                images = pipe(
                    prompt=prompt_final,
                    negative_prompt=negative_prompt,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                ).images
            except Exception as e:
                print(f"Error during SDXL generation (first image): {e}")
                raise HTTPException(500, f"Generation failed: {e}")

            img1 = images[0]
            image1_filename = f"{uuid.uuid4().hex}.png"
            image1_path = os.path.join(MOUNT_PATH, image1_filename)
            img1.save(image1_path)
            print(f"Saved FIRST generated image to: {image1_path}")

            image1_url = f"/images/{image1_filename}"
            base64_image = encode_image(image1_path)
            image_data_url = f"data:image/png;base64,{base64_image}"

        analysis_dir = os.path.join(MOUNT_PATH, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)


        art_analysis_prompt = '''
> Perform a formal analysis of the given artwork using the specialized vocabulary of art history. Follow the structure below:
>
Each item is phrased as a direct instruction for an image-generation model such as SDXL.

* No metaphors or flowery language.
* Use simple, literal terms the model can parse unambiguously.
* Focus on explicit, transferable details so the same structure can be applied to *any* subject-matter.

--- 

### Form

Describe the exact shapes and their dimensionality.

* List every major shape (e.g. “sphere”, “cube”, “cone”, “irregular organic blob”).
* State whether each shape is 2-D outline or 3-D volume.
* Note edge quality: sharp straight edge, softly rounded, or jagged.
* Indicate solidity: opaque, translucent, or transparent.

> **Example output**
> “Central object: single cylinder, fully three-dimensional, opaque. Two thin 2-D rectangles behind it, edges sharp. One small irregular organic blob in front.”

--- 

### Composition

Explain the placement of shapes inside the frame.

* Specify layout type: symmetrical, asymmetrical, radial, diagonal grid, free-form.
* Identify primary focal point and its exact position (e.g. “center-left at 40 % width, 50 % height”).
* Mention balance method: equal weight left/right, heavier top, etc.
* Describe any directional flow for the viewer’s eye (e.g. “Z-shaped reading path from top-left to bottom-right”).
* Note negative space areas and their approximate size or percentage.

--- 

### Material

State the physical or digital medium and its surface qualities.

* Medium examples: oil paint on canvas, matte plastic, brushed steel, digital brush, voxel render.
* Surface feel: smooth, grainy, reflective, matte, semi-gloss.
* Mention visible artefacts (brushstrokes, noise, pixelation) if present.

--- 

### Technique

Describe *how* the medium is applied.

* Application style: thin single coat, thick impasto, layered glazing, flat vector fill, parametric 3-D modeling.
* Precision level: highly precise / loose gestural / procedurally generated.
* Any special process: airbrush gradient, particle simulation, Boolean subtraction, mesh sculpting.

--- 
###Color: Analyze the artwork’s color in detail do not miss a single detail. Do not use metaphor use the name of the colour. Explain which colour is used in which part of the painting explicitly mention the colour and part used and why and don't just provide the list of colours .
### Line

Catalog the line work.

* Line types: continuous, dashed, dotted, calligraphic, scribble.
* Weight: hairline (<1 px), medium (3-5 px), heavy (>8 px).
* Function: outline contour, internal detail, motion guide, texture hatch.
* Direction: vertical, horizontal, 45° diagonal, curved S-curve, concentric circles.

--- 

### Perspective

Describe depth-creation method.

* Perspective type: one-point, two-point, isometric, atmospheric fade, orthographic.
* Vanishing-point location(s) in frame coordinates if relevant.
* Degree of foreshortening on key objects (e.g. “front wheel shortened to 60 % true length”).
* Horizon line height as a percentage of frame height.

--- 

### Space

Explain spatial feel.

* Depth range: flat (0 cm), shallow (<20 cm impression), moderate (~1 m impression), deep (>5 m impression).
* Spatial continuity: uninterrupted, segmented panels, collage overlap.
* Viewer position: eye-level, bird’s-eye (top-down), worm’s-eye (low).

--- 

### Proportion

Define size ratios between parts.

* Give numeric or percentage ratios where possible (e.g. “head = 1 : 4 of full figure height”).
* Indicate naturalistic, idealized (Golden Ratio, canonical canon-of-eighths), or intentionally exaggerated.

--- 

### Scale

State the artwork’s physical size *and* internal scale cues.

* Overall canvas size (e.g. “70 cm × 100 cm”).
* Relative scale of main subject to canvas (e.g. “subject fills 80 % height”).
* Monumental (viewer dwarfed), human-scale, or miniature (fits in hand).

--- 

### Texture

Describe surface feel, real or implied.

* Real texture: raised paint 2 mm thick, coarse canvas weave visible.
* Implied texture: smooth glass rendered with specular highlight, rough bark via high-frequency bump.
* Specify pattern size (e.g. “grain 4 px period”).
* Link texture to purpose if needed (e.g. “rough texture used to signify aged surface").

--- 

Use these clear, literal directives together with your detailed Color section; SDXL will then have all the explicit parameters it needs to replicate the structure and style when swapping in any new subject.
'''
        try:
            art_response = client.responses.create(
                model="google/gemma-3-27b-it",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": art_analysis_prompt},
                            {"type": "input_image", "image_url": image_data_url},
                        ],
                    }
                ],
            )
            reflect_art_knowledge = art_response.output_text
        except Exception as e:
            print(f"Error in art analysis agent: {e}")
            reflect_art_knowledge = f"ERROR: {e}"

        reflect_art_path = os.path.join(analysis_dir, f"reflect_art_knowledge_{uuid.uuid4().hex}.txt")
        write_to_file(reflect_art_path, reflect_art_knowledge)
        print(f"saved reflect_art_knowledge to: {reflect_art_path}")

        object_analysis_prompt = '''
>Look at the image carefully.

Analyze each object in the image using iconographic principles to extract reusable symbolic logic and design attributes.

For each object, explain:

Object Identity

What is the object called?

What is its historical, religious, or cultural significance?

Visual Construction

Describe form (shape, posture, position).

Describe material, texture, and style (e.g., sculptural, painted, digital, abstract, naturalistic).

Color & Light

What color(s) are used and why?

How does light or shadow reinforce the object's meaning?

Symbolic Meaning

What concept or narrative does the object express?

Is it universally symbolic or culturally specific?

Functional Role in Composition

Is it a central motif or supportive detail?

What emotional or spiritual response does it aim to provoke?


Then, for the entire scene, perform an anomaly check:

Are there any logical inconsistencies like shadows pointing wrong way, objects floating, incorrect anatomy, mismatched lighting

Are there semantic errors like banana used as a phone, fire under water, inconsistent architecture

Are there stylistic or compositional flaws like incorrect perspective, broken symmetry, missing parts)

Format your response clearly:

Object List (with properties)
Detected Issues / Inconsistencies

Overall Scene Assessment
'''
        try:
            obj_response = client.responses.create(
                model="google/gemma-3-27b-it",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": object_analysis_prompt},
                            {"type": "input_image", "image_url": image_data_url},
                        ],
                    }
                ],
            )
            reflect_object_knowledge = obj_response.output_text
        except Exception as e:
            print(f"Error in object analysis agent: {e}")
            reflect_object_knowledge = f"ERROR: {e}"

        reflect_object_path = os.path.join(analysis_dir, f"reflect_object_knowledge_{uuid.uuid4().hex}.txt")
        write_to_file(reflect_object_path, reflect_object_knowledge)
        print(f"Saved reflect_object_knowledge to: {reflect_object_path}")
        img_md = encode_image_to_markdown(image1_path)
        config_list = [
            {"model": "openai/gpt-oss-120b", "api_key": api_key},
            {"model": "openai/gpt-oss-120b", "api_key": api_key},
        ]

        start_prompt = f'''


Instructions:

Using {art_work_knowledge} and {reflect_art_knowledge} find out what is wrong with {prompt_final} on style level. Start by listing the deviation between two and reason why you think there is deviation.
Using {iconographic_work_knowledge} and {reflect_object_knowledge} find out what is wrong with {prompt_final} on composition level.Start by listing the deviation between two and reason why you think there is deviation. Find out similar objects in {prompt_final} and your {artwork_name}.
- Based on deviation that you havee identified ask question whose answer will fix the deviation ask one question at a time. Ask it based on your persona in first person
- After receiving the response think of a question whose answer will help you correct the artwork. You don't have to accept the first answer. You should think about the answer and can ask follow up question
- Think yourself as a teacher, question should be such that it is refrenced form {artwork_name} {art_work_knowledge} {iconographic_work_knowledge}
- Ask why SDXLAgent might have created that certain formal component the way they did. Stop SDXLAgent from asking questions ask him only to reply.
- Then, follow up with a question that probes how the object could be reworked to conform with the iconographic or symbolic standard of "{artwork_name}".
- Each question must be Socratic and cover both form and meaning.
- Make sure same colors are dominant in both final prompt as {artwork_name}
- Make sure objects look similar in both

Ask one question at a time. Wait for SDXLAgent's answer before continuing.
Do not summarize, skip steps, or make corrections yourself.

Once enough answers are collected, revise {prompt_final} only if there are meaningful deviations from the artistic and symbolic logic of "{artwork_name}".

Finally, generate a refined prompt should be less than 70 tokens this is very important that realigns the visual and symbolic structure with "{artwork_name}".
Briefly explain how each SDXLAgent response contributed to the refined version.'''

        sdxl_agent = AssistantAgent(
            name="SDXLAgent",
            llm_config={"config_list": config_list, "cache_seed": 1},
            system_message=(
                f'''You are Visionary-SDXL, an AI image generator that can see images and explain your artwork. Always look
                for embedded image passed by LeonardoAgent. By looking at the image, this formal analysis:
                {reflect_art_knowledge}
                and this iconographic analysis:
                {reflect_object_knowledge}
                you need to answer the questions asked by LeonardoAgent about why you created what you created.
                You cannot ask questions. Talk in first person and do not ask questions.'''
            ),
        )

        artist_label = artist_normalized.capitalize()
        leonardo_agent = AssistantAgent(
            name="LeonardoAgent",
            llm_config={"config_list": config_list, "cache_seed": 1},
            system_message=(
                f'''{persona}. You are {artist_label}, reflecting on modern attempts to capture your style. Speak in the
                first person, expressing your artistic philosophy and preferences. When analyzing an artwork, discuss the brushwork,
                color harmony, treatment of light, atmosphere, and emotional resonance. Critique with honesty and insight, noting
                where the work aligns with or diverges from your ideals. Ask questions and offer your perspective as the artist.
                Remain true to your persona throughout.'''
            ),
        )
        chat_result = sdxl_agent.initiate_chat(
            leonardo_agent,
            message=start_prompt,
            summary_method="reflection_with_llm",
            max_turns=10,
            cache_seed=1,
        )
        chat_history_path = os.path.join(analysis_dir, f"chat_history_{uuid.uuid4().hex}.txt")
        try:
            import pprint
            with open(chat_history_path, "w", encoding="utf-8") as f:
                pprint.pprint(chat_result.chat_history, stream=f)
            print(f"💾 Saved chat history to: {chat_history_path}")
        except Exception as e:
            print(f"Failed to save chat history: {e}")
        try:
            extract_resp = client.responses.create(
                model="openai/gpt-oss-120b",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"Extract only the final refined SDXL prompt (under 70 tokens) from this conversation:\n\n{chat_result}",
                            },
                        ],
                    }
                ],
            )
            reflected_prompt = extract_resp.output_text.strip()
        except Exception as e:
            print(f"Error extracting reflected_prompt: {e}")
            reflected_prompt = prompt_final 


        reflected_prompt_dir = os.path.join(MOUNT_PATH, "reflected_prompts")
        os.makedirs(reflected_prompt_dir, exist_ok=True)

        reflected_prompt_path = os.path.join(reflected_prompt_dir, f"reflected_prompt_{uuid.uuid4().hex}.txt")
        write_to_file(reflected_prompt_path, reflected_prompt)
        print(f"Saved reflected_prompt to: {reflected_prompt_path}")
        print(f"\nreflected_prompt:\n{reflected_prompt}\n")
        print(f"Generating SECOND image with SDXL for reflected_prompt.")
        try:
            images2 = pipe(
                prompt=reflected_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
            ).images
        except Exception as e:
            print(f"Error during SDXL generation (second image): {e}")
            images2 = [img1]

        img2 = images2[0]
        image2_filename = f"{uuid.uuid4().hex}_refined.png"
        image2_path = os.path.join(MOUNT_PATH, image2_filename)
        img2.save(image2_path)
        print(f"Saved SECOND (refined) generated image to: {image2_path}")

        image2_url = f"/images/{image2_filename}"
        image_volume.commit()

        return {
            "status": "success",
            "artist": artist_normalized,
            "artwork_name": artwork_name,
            "original_prompt": prompt_og,
            "sdxl_prompt_initial": prompt_final,
            "reflected_prompt": reflected_prompt,
            "image_url_initial": image1_url,
            "image_url_refined": image2_url,
            "prompt_file_path": prompt_file_path,
            "reflect_art_file_path": reflect_art_path,
            "reflect_object_file_path": reflect_object_path,
            "chat_history_file_path": chat_history_path,
            "reflected_prompt_file_path": reflected_prompt_path,
        }

    return api
