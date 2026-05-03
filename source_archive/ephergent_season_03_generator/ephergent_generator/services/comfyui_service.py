import os
import json
import uuid
import time
import random
import logging
import requests
import websocket
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class ComfyUIService:
    """Service for generating images using ComfyUI."""
    
    def __init__(self):
        self.comfyui_url = os.environ.get('COMFYUI_URL', 'http://127.0.0.1:8188')
        self.enabled = os.environ.get('COMFYUI_ENABLED', 'true').lower() == 'true'
        
        # Path to the workflow template
        app_root = Path(__file__).parent.parent
        self.workflow_path = app_root / 'workflows' / 't2i_ephergent_season_03_workflow.json'
        
        # Style constants from reference code
        self.style_prefix = "ArsMJStyle, dnddarkestfantasy, Kenva, fluxlisimo, fluxlisimo_neon, CCM-R-Daal, "
        self.post_style_suffix = """A digitally illustrated drawing in stylized 3D anime manga style with painterly cel-shading and hand-drawn textures, featuring volumetric lighting with soft watercolor-like gradients, dynamic comic book halftone patterns, realistic depth of field and atmospheric perspective, soft ambient occlusion shadows, cinematic rim lighting, subsurface scattering effects, realistic material textures and fabric physics, while maintaining clean manga lineart with NPR non-photorealistic rendering and traditional anime color palettes enhanced by atmospheric haze"""
        # self.post_style_suffix = ""
        logger.info(f"ComfyUI Service initialized - URL: {self.comfyui_url}, Enabled: {self.enabled}")
        
        if not self.workflow_path.exists():
            logger.error(f"ComfyUI workflow template not found: {self.workflow_path}")
            self.enabled = False
    
    def is_available(self) -> bool:
        """Check if ComfyUI is available and enabled."""
        if not self.enabled:
            logger.info("ComfyUI service is disabled")
            return False
            
        try:
            response = requests.get(f"{self.comfyui_url}/system_stats", timeout=5)
            if response.status_code == 200:
                logger.info(f"ComfyUI service is available at {self.comfyui_url}")
                return True
            else:
                logger.warning(f"ComfyUI service returned status {response.status_code} at {self.comfyui_url}")
                return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"ComfyUI service connection failed at {self.comfyui_url} - server may be offline")
            return False
        except requests.exceptions.Timeout:
            logger.warning(f"ComfyUI service timeout at {self.comfyui_url} - server may be overloaded")
            return False
        except Exception as e:
            logger.warning(f"ComfyUI service error at {self.comfyui_url}: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test ComfyUI connection and return detailed status."""
        status = {
            'enabled': self.enabled,
            'url': self.comfyui_url,
            'available': False,
            'error': None,
            'response_time': None
        }
        
        if not self.enabled:
            status['error'] = 'ComfyUI service is disabled'
            return status
            
        try:
            start_time = time.time()
            response = requests.get(f"{self.comfyui_url}/system_stats", timeout=10)
            response_time = time.time() - start_time
            
            status['response_time'] = round(response_time, 3)
            
            if response.status_code == 200:
                status['available'] = True
                logger.info(f"ComfyUI connection test successful - {response_time:.3f}s response time")
            else:
                status['error'] = f"HTTP {response.status_code}"
                logger.warning(f"ComfyUI connection test failed - HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            status['error'] = 'Connection refused - server offline'
            logger.warning(f"ComfyUI connection test failed - connection refused")
        except requests.exceptions.Timeout:
            status['error'] = 'Connection timeout - server overloaded'
            logger.warning(f"ComfyUI connection test failed - timeout")
        except Exception as e:
            status['error'] = str(e)
            logger.warning(f"ComfyUI connection test failed - {e}")
            
        return status
    
    def _open_websocket_connection(self) -> tuple[Optional[websocket.WebSocket], Optional[str]]:
        """Open WebSocket connection to ComfyUI."""
        client_id = str(uuid.uuid4())
        ws_url = f"ws://{self.comfyui_url.replace('http://', '').replace('https://', '')}/ws?clientId={client_id}"
        
        try:
            ws = websocket.create_connection(ws_url, timeout=15)
            logger.info(f"WebSocket connection established: {ws_url}")
            return ws, client_id
        except Exception as e:
            logger.error(f"Failed to connect to ComfyUI WebSocket at {ws_url}: {e}")
            return None, None
    
    def _queue_prompt(self, prompt_workflow: dict, client_id: str) -> Optional[str]:
        """Queue a prompt for generation."""
        payload = {"prompt": prompt_workflow, "client_id": client_id}
        data = json.dumps(payload).encode('utf-8')
        url = f"{self.comfyui_url}/prompt"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            prompt_id = response_data['prompt_id']
            logger.info(f"Queued prompt with ID: {prompt_id}")
            return prompt_id
        except requests.RequestException as e:
            logger.error(f"Failed to queue prompt: {e}")
            return None
    
    def _track_progress(self, prompt_workflow: dict, ws: websocket.WebSocket, prompt_id: str, client_id: str):
        """Track progress of image generation via WebSocket."""
        save_node_ids = {
            nid for nid, node_info in prompt_workflow.items() 
            if node_info.get("class_type", "").startswith("SaveImage")
        }
        
        timeout_start = time.time()
        timeout_duration = 300  # 5 minutes timeout
        
        while time.time() - timeout_start < timeout_duration:
            try:
                ws.settimeout(10)  # Set socket timeout
                out = ws.recv()
                
                if isinstance(out, str):
                    message = json.loads(out)
                    if message.get('type') == 'executed' and message.get('data', {}).get('prompt_id') == prompt_id:
                        node_id = message['data'].get('node')
                        if node_id in save_node_ids:
                            logger.info(f"Save node {node_id} executed. Prompt {prompt_id} complete.")
                            return
                    elif message.get('type') == 'progress':
                        # Log progress updates
                        data = message.get('data', {})
                        value = data.get('value', 0)
                        max_value = data.get('max', 0)
                        if max_value > 0:
                            progress = (value / max_value) * 100
                            logger.info(f"Generation progress: {progress:.1f}%")
                            
            except websocket.WebSocketTimeoutException:
                logger.debug("WebSocket timeout, continuing to wait...")
                continue
            except Exception as e:
                logger.error(f"Error during progress tracking: {e}")
                break
        
        logger.warning(f"Timeout waiting for prompt {prompt_id} completion")
    
    def _get_image(self, filename: str, subfolder: str, folder_type: str) -> Optional[bytes]:
        """Download image from ComfyUI."""
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url = f"{self.comfyui_url}/view?{urlencode(params)}"
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            logger.info(f"Successfully downloaded image '{filename}'")
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to fetch image {filename}: {e}")
            return None
    
    def _get_history(self, prompt_id: str) -> Optional[dict]:
        """Get generation history from ComfyUI."""
        url = f"{self.comfyui_url}/history/{prompt_id}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch history for {prompt_id}: {e}")
            return None
    
    def _get_images_from_history(self, prompt_id: str) -> List[bytes]:
        """Extract image data from generation history."""
        history_data = self._get_history(prompt_id)
        if not history_data or prompt_id not in history_data:
            return []
        
        output_images_data = []
        for node_id, node_output in history_data[prompt_id]['outputs'].items():
            if 'images' in node_output:
                for image_info in node_output['images']:
                    if image_info.get('type') == 'output':
                        image_data = self._get_image(
                            image_info['filename'], 
                            image_info.get('subfolder', ''), 
                            image_info['type']
                        )
                        if image_data:
                            output_images_data.append(image_data)
        
        return output_images_data
    
    def _load_workflow_template(self) -> Optional[Dict]:
        """Load and prepare the workflow template."""
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            logger.info(f"Loaded ComfyUI workflow template: {self.workflow_path}")
            return workflow
        except Exception as e:
            logger.error(f"Error loading workflow template {self.workflow_path}: {e}")
            return None
    
    def _update_prompt_in_workflow(self, workflow: Dict, prompt: str) -> Dict:
        """Update the prompt text in the workflow."""
        try:
            # Find positive prompt node IDs by looking at KSampler connections
            positive_prompt_node_ids = set()
            ksampler_nodes = {
                nid: ndata for nid, ndata in workflow.items() 
                if "KSampler" in ndata.get("class_type", "")
            }
            
            for ksampler_data in ksampler_nodes.values():
                pos_input = ksampler_data.get("inputs", {}).get("positive")
                if isinstance(pos_input, list) and len(pos_input) > 0:
                    positive_prompt_node_ids.add(pos_input[0])
            
            # Update prompt text in positive prompt nodes
            for node_id in positive_prompt_node_ids:
                if node_id in workflow and 'inputs' in workflow[node_id]:
                    # Combine style prefix + prompt + style suffix
                    full_prompt = f"{self.style_prefix}{prompt}, {self.post_style_suffix}"
                    logger.info(f"Setting prompt in node {node_id}: {full_prompt}")
                    workflow[node_id]['inputs']['text'] = full_prompt
                    logger.info(f"Updated prompt in node {node_id}")
            
            # Update random seed for variation
            seed = random.randint(10**14, 10**15 - 1)
            for node_id in ksampler_nodes:
                if 'inputs' in workflow[node_id]:
                    workflow[node_id]['inputs']['seed'] = seed
            
            logger.info(f"Updated workflow with prompt and seed {seed}")
            return workflow
            
        except Exception as e:
            logger.error(f"Error updating workflow prompt: {e}")
            return workflow
    
    def generate_image(self, prompt: str, output_path: Path, width: int = None, height: int = None) -> Optional[Path]:
        """
        Generate an image using ComfyUI.
        
        Args:
            prompt: Text prompt for image generation
            output_path: Where to save the generated image
            width: Optional custom width (defaults to workflow setting)
            height: Optional custom height (defaults to workflow setting)
            
        Returns:
            Path to generated image or None if failed
        """
        if not self.is_available():
            logger.error("ComfyUI service not available")
            return None
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load workflow template
        workflow = self._load_workflow_template()
        if not workflow:
            return None
        
        # Set custom dimensions if provided
        if width and height:
            for node in workflow.values():
                if node.get('class_type', '').startswith('EmptyLatentImage'):
                    node['inputs']['width'] = width
                    node['inputs']['height'] = height
                    logger.info(f"Set custom dimensions: {width}x{height}")
        
        # Update prompt in workflow
        workflow = self._update_prompt_in_workflow(workflow, prompt)
        
        # Open WebSocket connection
        ws, client_id = self._open_websocket_connection()
        if not ws:
            return None
        
        try:
            # Queue the prompt
            prompt_id = self._queue_prompt(workflow, client_id)
            if not prompt_id:
                return None
            
            logger.info(f"Starting image generation (estimated ~200 seconds)...")
            
            # Track progress
            self._track_progress(workflow, ws, prompt_id, client_id)
            
            # Get generated images
            images_data = self._get_images_from_history(prompt_id)
            
            if images_data:
                # Save the first image
                with open(output_path, 'wb') as f:
                    f.write(images_data[0])
                logger.info(f"Image successfully saved to: {output_path}")
                return output_path
            else:
                logger.error(f"No images found in history for prompt ID: {prompt_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            return None
        finally:
            # Clean up WebSocket connection
            try:
                if ws and ws.connected:
                    ws.close()
            except:
                pass
    
    def generate_story_images(self, story_data: Dict[str, Any], images_dir: Path) -> Dict[str, Optional[Path]]:
        """
        Generate all images for a story using ComfyUI.
        
        Args:
            story_data: Story data dictionary
            images_dir: Directory to save images
            
        Returns:
            Dictionary mapping image types to file paths
        """
        story_id = story_data.get('id', 'unknown')
        title = story_data.get('title', 'Untitled Story')
        
        images = {}
        
        try:
            # Check if we have saved prompts to use (from ImageService)
            saved_prompts = story_data.get('image_prompts', {})
            
            if saved_prompts and isinstance(saved_prompts, dict):
                logger.info(f"Using saved image prompts for story {story_id}")
                
                # Generate feature image using saved prompt
                feature_prompt = saved_prompts.get('feature_image_prompt')
                if feature_prompt:
                    feature_filename = f"story_{story_id}_feature.png"
                    feature_path = images_dir / feature_filename
                    
                    logger.info(f"Generating feature image for story {story_id} with saved prompt")
                    images['feature'] = self.generate_image(
                        prompt=feature_prompt,
                        output_path=feature_path,
                        width=1344,  # Wide format from workflow
                        height=768
                    )
                
                # Generate article images using saved prompts
                for section in ['beginning', 'middle', 'end']:
                    prompt_key = f'{section}_image_prompt'
                    if prompt_key in saved_prompts:
                        prompt = saved_prompts[prompt_key]
                        article_filename = f"story_{story_id}_{section}.png"
                        article_path = images_dir / article_filename
                        
                        logger.info(f"Generating {section} image for story {story_id} with saved prompt")
                        images[section] = self.generate_image(
                            prompt=prompt,
                            output_path=article_path,
                            width=1344,
                            height=768
                        )
                        
                        # Add delay between generations to avoid overwhelming ComfyUI
                        if images[section]:
                            time.sleep(5)
                
            else:
                # Fallback to generating prompts if none saved
                logger.warning(f"No saved prompts found for story {story_id}, generating fallback prompts")
                content = story_data.get('content', '')
                
                # Generate feature image (wide format)
                feature_prompt = self._generate_feature_prompt(title, content)
                feature_filename = f"story_{story_id}_feature.png"
                feature_path = images_dir / feature_filename
                
                logger.info(f"Generating feature image for story {story_id}")
                images['feature'] = self.generate_image(
                    prompt=feature_prompt,
                    output_path=feature_path,
                    width=1344,  # Wide format from workflow
                    height=768
                )
                
                # Generate article images
                article_prompts = self._generate_article_prompts(title, content)
                
                for section, prompt in article_prompts.items():
                    article_filename = f"story_{story_id}_{section}.png"
                    article_path = images_dir / article_filename
                    
                    logger.info(f"Generating {section} image for story {story_id}")
                    images[section] = self.generate_image(
                        prompt=prompt,
                        output_path=article_path,
                        width=1344,
                        height=768
                    )
                    
                    # Add delay between generations to avoid overwhelming ComfyUI
                    if images[section]:
                        time.sleep(5)
            
            successful_images = len([p for p in images.values() if p])
            logger.info(f"Generated {successful_images}/{len(images)} images for story {story_id}")
            
        except Exception as e:
            logger.error(f"Error generating story images: {e}")
        
        return images
    
    def _generate_feature_prompt(self, title: str, content: str) -> str:
        """Generate a prompt for the feature image."""
        # Extract key elements from the content
        content_preview = content[:300] if content else ""
        
        # Create cyberpunk-themed feature image prompt
        prompt = f"""
        inspired by the story: {title}.
        Scene elements: {content_preview}
        """
        
        return prompt.strip()
    
    def _generate_article_prompts(self, title: str, content: str) -> Dict[str, str]:
        """Generate prompts for article images."""
        content_preview = content[:500] if content else ""
        
        prompts = {
            'beginning': f"""
            setting up the narrative: {title}. Content: {content_preview}
            """,
            'middle': f"""
            peak moment from: {title}. Content: {content_preview}
            """,
            'end': f"""
            ending of: {title}. Content: {content_preview}
            """
        }
        
        # Clean up prompts
        for key in prompts:
            prompts[key] = " ".join(prompts[key].strip().split())
        
        return prompts
