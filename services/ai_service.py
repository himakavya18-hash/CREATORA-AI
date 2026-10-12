import json
import logging
import re
import urllib.request
from flask import current_app

logger = logging.getLogger(__name__)

class AIService:
    @classmethod
    def _call_ollama(cls, prompt_text, system_instruction=""):
        """Calls a locally running Ollama server and returns its response text."""
        try:
            base_url = current_app.config.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
            payload = {
                'model': current_app.config.get('OLLAMA_MODEL', 'gemma3:1b'),
                'stream': False,
                'format': 'json' if 'strict JSON' in system_instruction or 'strict JSON' in prompt_text else None,
                'messages': ([{'role': 'system', 'content': system_instruction}] if system_instruction else []) +
                            [{'role': 'user', 'content': prompt_text}],
            }
            payload = {key: value for key, value in payload.items() if value is not None}
            req = urllib.request.Request(
                f"{base_url}/api/chat", data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode('utf-8'))
            return data.get('message', {}).get('content')
        except Exception as exc:
            logger.warning("Local Ollama request failed: %s", exc)
            return None

    @classmethod
    def chat_support(cls, message, history, role):
        """Answer platform questions for creators and brands with local Ollama."""
        system_prompt = (
            "You are Creatora AI Help, a concise support assistant for creators and brand users. "
            "Help with account setup, creator profiles and portfolios, campaign briefs, applications, "
            "proposals, messaging, projects, and navigating the marketplace. The current user's role "
            f"is {role}. Give clear step-by-step guidance when useful. Do not claim to access or change "
            "their account, payments, or private records. If a question needs an administrator or "
            "account-specific access, say so plainly. Do not invent platform features."
        )
        conversation = []
        for item in history:
            who = 'User' if item['role'] == 'user' else 'Help assistant'
            conversation.append(f"{who}: {item['content']}")
        conversation.append(f"User: {message}")
        return cls._call_ollama('\n'.join(conversation), system_prompt)

    @classmethod
    def create_video_storyboard(cls, concept):
        """Turn a creator's idea into a short storyboard for the browser motion-graphics editor."""
        system_prompt = """You are a motion graphics creative director. Return strict JSON only, with this shape:
{"title":"short title","description":"one sentence","scenes":[
{"headline":"short on-screen text","subheadline":"supporting text","background":"#112233","motif":"circle"},
{"headline":"short on-screen text","subheadline":"supporting text","background":"#112233","motif":"orbit"},
{"headline":"short on-screen text","subheadline":"supporting text","background":"#112233","motif":"burst"}]}
Make it suitable for a polished creator showcase or product video. Keep text concise. Use only hex background colors and the motif names circle, orbit, or burst."""
        response = cls._call_ollama(concept, system_prompt)
        parsed = cls._extract_json(response)
        ai_generated = isinstance(parsed, dict) and isinstance(parsed.get('scenes'), list) and len(parsed['scenes']) > 0
        if not isinstance(parsed, dict):
            parsed = {}

        title = str(parsed.get('title') or concept[:70]).strip()[:100]
        description = str(parsed.get('description') or f"Animated showcase: {title}").strip()[:240]
        raw_scenes = parsed.get('scenes')
        scenes = []
        if isinstance(raw_scenes, list):
            for scene in raw_scenes[:3]:
                if not isinstance(scene, dict):
                    continue
                background = str(scene.get('background', '#111827'))
                if not re.fullmatch(r'#[0-9a-fA-F]{6}', background):
                    background = '#111827'
                motif = scene.get('motif', 'circle')
                if motif not in ('circle', 'orbit', 'burst'):
                    motif = 'circle'
                scenes.append({
                    'headline': str(scene.get('headline') or title)[:70],
                    'subheadline': str(scene.get('subheadline') or description)[:120],
                    'background': background,
                    'motif': motif,
                })

        if not scenes:
            scenes = [
                {'headline': title, 'subheadline': 'A new idea, brought to life.', 'background': '#111827', 'motif': 'circle'},
                {'headline': 'Made to stand out', 'subheadline': description, 'background': '#172554', 'motif': 'orbit'},
                {'headline': 'Create what is next', 'subheadline': 'Designed by you with Creatora Studio.', 'background': '#312e81', 'motif': 'burst'},
            ]
        while len(scenes) < 3:
            scenes.append(scenes[-1])
        return {'title': title, 'description': description, 'scenes': scenes, 'ai_generated': ai_generated}

    @classmethod
    def _extract_json(cls, raw_text):
        """Extracts JSON object from text output."""
        if not raw_text:
            return None
        try:
            # Clean markdown codeblocks
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw_text.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned.strip())
            return json.loads(cleaned)
        except Exception:
            match = re.search(r'(\{[\s\S]*\})', raw_text)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

    # ==========================================
    # 1. AI CAMPAIGN BRIEF GENERATOR
    # ==========================================
    @classmethod
    def generate_campaign_brief(cls, prompt_text):
        """Converts natural language input into a structured creative brief with follow-up suggestions."""
        system_prompt = """You are Creatora AI's Campaign Architect.
Convert the client's concept into a structured JSON campaign brief for AI creators.
Output MUST be strict JSON with the following keys:
{
  "title": string,
  "description": string,
  "product_or_service": string,
  "objective": string (e.g. Brand Awareness, Viral Reach, Product Launch, Conversions),
  "target_audience": string,
  "content_category": string (e.g. Commercial Ads, Tech & SaaS, Beauty & Fashion, Gaming),
  "content_type": string (e.g. AI Video Ad, 3D Product Motion, AI Stills Series, Character Reel),
  "creative_style": string (e.g. Hyper-realistic, Cyberpunk, Cinematic Minimalist, Surrealist Dreamscape),
  "preferred_platform": string (e.g. Instagram Reels, TikTok, YouTube Shorts, Web Commercial),
  "video_duration": string (e.g. 15-30s, 60s, N/A),
  "aspect_ratio": string (e.g. 9:16 (Vertical), 16:9 (Landscape), 1:1 (Square)),
  "resolution": string (e.g. 1080x1920 HD, 4K UHD),
  "deliverables_count": integer (1-10),
  "required_skills": string (comma-separated, e.g. Runway Gen-3, Midjourney, Video Upscaling, Sound Design),
  "preferred_ai_tools": string (comma-separated, e.g. Midjourney v6, Runway Gen-3, ElevenLabs, Magnific AI),
  "suggested_budget_min": number,
  "suggested_budget_max": number,
  "delivery_schedule": string,
  "acceptance_criteria": string,
  "missing_details_note": string,
  "follow_up_questions": [string, string, string]
}
Do not invent guaranteed product claims or non-existent constraints.
"""
        api_response = cls._call_ollama(prompt_text, system_prompt)
        if api_response:
            parsed = cls._extract_json(api_response)
            if parsed and isinstance(parsed, dict) and 'title' in parsed:
                parsed['is_ai_generated'] = True
                return parsed

        # Robust rule-based fallback
        return cls._fallback_campaign_brief(prompt_text)

    @classmethod
    def _fallback_campaign_brief(cls, prompt_text):
        p_lower = prompt_text.lower()
        
        # Detect category and content type
        category = "Commercial Ads"
        content_type = "AI Video Ad"
        style = "Cinematic Hyper-realistic"
        platform = "Instagram Reels & TikTok"
        aspect_ratio = "9:16 (Vertical)"
        duration = "15-30 seconds"
        exchange_rate = current_app.config.get('USD_TO_INR', 96.20)
        b_min = 600.0 * exchange_rate
        b_max = 1800.0 * exchange_rate
        tools = "Runway Gen-3, Midjourney v6, ElevenLabs, Topaz Video AI"
        skills = "Video Generation, AI Inpainting, Upscaling, Sound Design"

        if "fashion" in p_lower or "apparel" in p_lower or "clothing" in p_lower:
            category = "Fashion & Apparel"
            style = "Editorial High-Fashion, Moody Cinematic Lighting"
            platform = "Instagram & YouTube Shorts"
            tools = "Midjourney v6.1, Flux.1 Pro, Runway Gen-3, Magnific AI"
        elif "tech" in p_lower or "software" in p_lower or "saas" in p_lower or "app" in p_lower:
            category = "Tech & Software"
            content_type = "3D Motion Showcase"
            style = "Futuristic Cyber-Tech, Clean Minimal Neon Accents"
            tools = "Midjourney, Blender AI, Kling AI, Runway Gen-3"
            aspect_ratio = "16:9 (Landscape)"
            platform = "Website Commercial & YouTube"
        elif "skincare" in p_lower or "beauty" in p_lower or "cosmetic" in p_lower:
            category = "Beauty & Cosmetics"
            style = "Ethereal Pastel Glow, Organic Fluid Dynamics, Macro Close-ups"
            tools = "Midjourney v6, Runway Gen-3, Luma Dream Machine, Topaz Video AI"
            b_min = 800.0 * exchange_rate
            b_max = 2200.0 * exchange_rate
        elif "game" in p_lower or "gaming" in p_lower:
            category = "Gaming & Entertainment"
            content_type = "Cinematic Game Trailer Teaser"
            style = "Epic Fantasy, Dark Unreal Engine Style Unrealism"
            aspect_ratio = "16:9 (Landscape)"
            tools = "Midjourney, Runway Gen-3, Stable Audio, Kling AI"

        product_name = "Product / Service Concept"
        # Try extracting product name from prompt
        for word in ["for my ", "for our ", "for "]:
            if word in p_lower:
                part = prompt_text[p_lower.find(word) + len(word):].split(' ')[0:4]
                product_name = ' '.join(part).strip('.,! ')
                break

        title = f"{product_name.title()} AI Visual Campaign"
        description = (
            f"High-impact AI-crafted promotional campaign for {product_name}. "
            f"The goal is to create compelling visual narratives showcasing the product's unique value, "
            f"leveraging modern generative video, photorealistic renders, and synchronized audio."
        )

        return {
            "title": title,
            "description": description,
            "product_or_service": product_name.title(),
            "objective": "Brand Awareness & Social Engagement",
            "target_audience": "Digital-native consumers & early adopters aged 18-35",
            "content_category": category,
            "content_type": content_type,
            "creative_style": style,
            "preferred_platform": platform,
            "video_duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": "1080x1920 (Full HD)",
            "deliverables_count": 2,
            "required_skills": skills,
            "preferred_ai_tools": tools,
            "suggested_budget_min": b_min,
            "suggested_budget_max": b_max,
            "delivery_schedule": "Draft styleframes within 3 days; First cut in 5 days; Final delivery in 7 days.",
            "acceptance_criteria": "4K upscaled master, zero temporal morphing glitches on core product, clean sound design.",
            "missing_details_note": "Rule-based synthesis generated. Confirm exact brand guidelines, color palette hex codes, and audio voiceover script.",
            "follow_up_questions": [
                "Do you have existing 3D assets or high-resolution product photography to reference?",
                "What is the exact target call-to-action (CTA) for the campaign outro?",
                "Are there specific actor/avatar voiceover guidelines or preferred regional accents?"
            ],
            "is_ai_generated": False
        }

    # ==========================================
    # 2. AI PROPOSAL GENERATOR
    # ==========================================
    @classmethod
    def generate_creator_proposal(cls, brief_data, creator_profile):
        """Generates a tailored creative proposal for a creator applying to a campaign brief."""
        system_prompt = f"""You are an elite AI creative director helping a creator submit a winning proposal.
Creator Name: {creator_profile.display_name}
Creator Skills: {creator_profile.skills}
Creator Tools: {creator_profile.ai_tools}

Campaign Brief:
Title: {brief_data.get('title')}
Description: {brief_data.get('description')}
Deliverables: {brief_data.get('deliverables_count')}
Style: {brief_data.get('creative_style')}
Budget Range: INR {brief_data.get('budget_min')} - INR {brief_data.get('budget_max')}

Output MUST be strict JSON:
{{
  "understanding_summary": string,
  "creative_approach": string,
  "proposed_workflow": string,
  "deliverables_breakdown": string,
  "timeline_days": integer,
  "proposed_budget": number,
  "clarifying_questions": [string, string],
  "why_choose_me": string
}}
Do NOT invent fake past clients or claims. Be honest and focused on AI production methodology.
"""
        api_response = cls._call_ollama("Generate proposal", system_prompt)
        if api_response:
            parsed = cls._extract_json(api_response)
            if parsed and isinstance(parsed, dict) and 'creative_approach' in parsed:
                return parsed

        # Fallback proposal
        return cls._fallback_creator_proposal(brief_data, creator_profile)

    @classmethod
    def _fallback_creator_proposal(cls, brief_data, creator_profile):
        tools = creator_profile.ai_tools or "Runway Gen-3, Midjourney v6"
        b_min = brief_data.get('budget_min', 50000)
        b_max = brief_data.get('budget_max', 150000)
        recommended_budget = round((b_min * 0.4 + b_max * 0.6) / 500) * 500

        return {
            "understanding_summary": (
                f"I reviewed the brief for '{brief_data.get('title')}' and understand you are seeking a "
                f"{brief_data.get('creative_style', 'high-fidelity')} creative campaign tailored for "
                f"{brief_data.get('preferred_platform', 'digital platforms')}. The goal is to produce engaging visual assets "
                f"that highlight {brief_data.get('product_or_service', 'your brand')} with zero visual artifacting."
            ),
            "creative_approach": (
                f"My approach centers on combining latent image synthesis in Midjourney with temporal consistency in Runway Gen-3. "
                f"I will establish cohesive color grading, realistic lighting bounces, and cinematic motion curves. "
                f"For the visual style, I'll adhere directly to your preference for {brief_data.get('creative_style', 'modern aesthetics')}."
            ),
            "proposed_workflow": (
                f"1. Prompt engineering & styleframe moodboard (Day 1-2)\n"
                f"2. Motion generation & keyframe interpolation using {tools} (Day 3-4)\n"
                f"3. Latent upscaling, color timing & visual FX stabilization (Day 5)\n"
                f"4. Sound design integration & review round (Day 6-7)"
            ),
            "deliverables_breakdown": (
                f"- {brief_data.get('deliverables_count', 1)} Master cut in {brief_data.get('aspect_ratio', '9:16')} format\n"
                f"- High-res export in {brief_data.get('resolution', '1080p')}\n"
                f"- Up to {brief_data.get('review_stages', 2)} rounds of revisions"
            ),
            "timeline_days": 7,
            "proposed_budget": float(recommended_budget),
            "clarifying_questions": [
                "Will brand typography, vector logos, or exact packaging models be provided?",
                "Are there specific sound effects or licensed audio tracks required for the delivery?"
            ],
            "why_choose_me": (
                f"I specialize in {creator_profile.specialization or 'AI visual production'} with expertise in {tools}. "
                f"I maintain a transparent revision process and guarantee prompt turnaround times."
            )
        }

    # ==========================================
    # 3. AI PORTFOLIO ASSISTANT
    # ==========================================
    @classmethod
    def enhance_portfolio_description(cls, title, category, tools, draft_notes):
        """Generates rich descriptions, recommended tags, and pipeline documentation for a portfolio item."""
        prompt = f"""Generate portfolio documentation for an AI artwork/video:
Title: {title}
Category: {category}
Tools: {tools}
Notes: {draft_notes}

Return strict JSON:
{{
  "enhanced_description": string,
  "suggested_tags": string (comma-separated, 4-6 tags),
  "workflow_breakdown": string,
  "missing_details_tips": [string, string],
  "commercial_potential_notes": string
}}
"""
        res = cls._call_ollama(prompt)
        if res:
            parsed = cls._extract_json(res)
            if parsed and 'enhanced_description' in parsed:
                return parsed

        # Fallback
        return {
            "enhanced_description": (
                f"'{title}' is an AI-generated creative project exploring {category.lower()} aesthetics. "
                f"Crafted using an integrated pipeline including {tools}, this work emphasizes photorealistic fidelity, "
                f"balanced composition, and dynamic atmospheric depth."
            ),
            "suggested_tags": f"AI Art, {category}, {tools.split(',')[0] if tools else 'Generative AI'}, Commercial, High Definition",
            "workflow_breakdown": (
                f"Iterative prompt refinement -> Latent diffusion base render -> Regional inpainting -> "
                f"Temporal stabilization & neural upscaling -> Master finishing."
            ),
            "missing_details_tips": [
                "Include the exact aspect ratio (e.g., 9:16 vertical or 16:9 cinematic) to help brands evaluate placement.",
                "Detail whether audio/sound design was AI-generated or custom engineered."
            ],
            "commercial_potential_notes": "Well-suited for paid social campaigns, visual teasers, and high-impact digital out-of-home ads."
        }

    # ==========================================
    # 4. PORTFOLIO COMPLETENESS & SKILL SUGGESTIONS
    # ==========================================
    @classmethod
    def analyze_creator_portfolio(cls, creator_profile, portfolio_items):
        """Reviews creator profile and uploaded work to offer concrete improvement suggestions."""
        item_count = len(portfolio_items)
        tools = creator_profile.get_tools_list()
        
        tips = []
        strengths = []
        
        if item_count == 0:
            tips.append("Upload at least 1-3 flagship portfolio items to activate your marketplace ranking.")
        elif item_count < 3:
            tips.append("Adding 2 more varied projects (e.g. video + high-res stills) increases brand inquiry rates by 70%.")
        else:
            strengths.append(f"Strong portfolio depth with {item_count} documented creative projects.")

        if not any(item.media_type == 'video' for item in portfolio_items):
            tips.append("Over 65% of brand briefs request AI Video. Add a video sample using Runway Gen-3, Luma, or Kling AI.")
        else:
            strengths.append("Verified video generation capability available in portfolio.")

        if creator_profile.verification_status != 'Verified':
            tips.append("Submit your creator verification request to earn the verified badge and boost client trust.")
        else:
            strengths.append("Verified creator status active.")

        if not creator_profile.bio or len(creator_profile.bio) < 50:
            tips.append("Expand your bio with information on your creative philosophy and typical turnaround times.")

        return {
            "completeness_score": creator_profile.calculate_completeness(),
            "strengths": strengths or ["Profile initialized with basic contact information."],
            "recommended_actions": tips or ["Your profile is well-rounded and ready for top-tier brand matching!"],
            "skill_growth_suggestions": [
                "Explore multi-shot video consistency tools like Storyboarder AI and LoRA fine-tuning.",
                "Practice commercial voiceover synthesis pairing with ElevenLabs for full-package commercials."
            ]
        }
