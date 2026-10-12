import os
os.environ['DISABLE_SQLALCHEMY_CEXT'] = '1'

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from models import (
    db, User, CreatorProfile, BrandProfile, PortfolioItem, PortfolioTool,
    CreativeBrief, BriefRequirement, Application, Project, ProjectMilestone,
    RevisionRecord, Message, Notification, VerificationRecord, AuditLog
)

def seed_database(app=None):
    """Populates the database with realistic demo accounts and marketplace data."""
    if app is None:
        from app import create_app
        app = create_app()

    with app.app_context():
        print("[*] Starting database seeding...")
        db.create_all()

        # Avoid duplicate seeding if users already exist
        if User.query.filter_by(email='admin@creatora.ai').first():
            print("Database already contains seed data. Skipping.")
            return

        # 1. ADMIN USER
        admin = User(
            email='admin@creatora.ai',
            role='admin',
            is_active=True,
            is_verified=True,
            avatar_url='https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80'
        )
        admin.set_password('AdminPass123!')
        db.session.add(admin)

        # 2. BRAND USERS & PROFILES
        b1_user = User(
            email='contact@auraglow.com',
            role='brand',
            is_active=True,
            is_verified=True,
            avatar_url='https://images.unsplash.com/photo-1556740758-90de374c12ad?auto=format&fit=crop&w=300&q=80'
        )
        b1_user.set_password('BrandPass123!')
        db.session.add(b1_user)
        db.session.flush()

        brand1 = BrandProfile(
            user_id=b1_user.id,
            company_name='Aura Glow Skincare',
            logo_url='https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=300&q=80',
            industry='Beauty & Cosmetics',
            description='Next-generation clean biotech skincare designed for modern radiant hydration.',
            website='https://auraglowskincare.example.com',
            contact_email='press@auraglow.com',
            target_audience='Gen-Z and millennial skincare enthusiasts aged 20-35.',
            preferred_formats='Vertical Video (9:16), 4K Macro Stills, Ethereal Slow-Motion',
            brand_style='Soft pearlescent lighting, pastel organic gradients, fluid water dynamics.'
        )
        db.session.add(brand1)

        b2_user = User(
            email='partnerships@novatech.io',
            role='brand',
            is_active=True,
            is_verified=True,
            avatar_url='https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=300&q=80'
        )
        b2_user.set_password('BrandPass123!')
        db.session.add(b2_user)
        db.session.flush()

        brand2 = BrandProfile(
            user_id=b2_user.id,
            company_name='NovaTech Hardware',
            logo_url='https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=300&q=80',
            industry='Consumer Electronics & SaaS',
            description='Creators of the world\'s first neural haptic wearable interface.',
            website='https://novatech.example.com',
            contact_email='commercials@novatech.io',
            target_audience='Tech enthusiasts, programmers, digital nomads, early adopters.',
            preferred_formats='16:9 4K Cinematic, 9:16 Tech Reels, Holographic Visuals',
            brand_style='Minimalist dark cyber, matte titanium textures, vibrant cyan laser accents.'
        )
        db.session.add(brand2)

        # 3. CREATOR USERS & PROFILES
        # Creator 1: Elena Rostova (Verified, Pro)
        c1_user = User(
            email='elena.ai@creatora.ai',
            role='creator',
            is_active=True,
            is_verified=True,
            avatar_url='https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80'
        )
        c1_user.set_password('CreatorPass123!')
        db.session.add(c1_user)
        db.session.flush()

        creator1 = CreatorProfile(
            user_id=c1_user.id,
            display_name='Elena Rostova',
            headline='Senior AI Commercial Director & Neural Cinematographer',
            bio='5+ years experience in high-end brand advertising. Specializing in Runway Gen-3, Midjourney v6, and temporal visual stabilization for luxury cosmetics and commercial spots.',
            skills='Runway Gen-3, Midjourney v6, Video Upscaling, Sound Design, Color Grading, Latent Inpainting',
            specialization='Commercial Ads',
            experience_level='Expert',
            ai_tools='Runway Gen-3, Midjourney v6, ElevenLabs, Topaz Video AI, Magnific AI',
            content_categories='Beauty & Cosmetics, Luxury Goods, Commercial Ads',
            project_types='Short-form Video, Master Commercial Stills, Product Reveal Teaser',
            availability_status='Available',
            hourly_rate_min=76960.0,
            hourly_rate_max=240500.0,
            preferred_rate_unit='per project',
            languages='English, French',
            portfolio_completeness=95,
            verification_status='Verified',
            location='London, UK / Remote',
            website='https://elenarostova.ai'
        )
        db.session.add(creator1)
        db.session.flush()

        # Creator 2: Marcus Vance (3D Motion & Cyberpunk)
        c2_user = User(
            email='marcus.render@creatora.ai',
            role='creator',
            is_active=True,
            is_verified=True,
            avatar_url='https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80'
        )
        c2_user.set_password('CreatorPass123!')
        db.session.add(c2_user)
        db.session.flush()

        creator2 = CreatorProfile(
            user_id=c2_user.id,
            display_name='Marcus Vance',
            headline='Generative 3D Artist & Cyberpunk Worldbuilder',
            bio='Pioneering hybrid pipelines uniting Blender 3D geometry with Kling AI and Flux.1 generative texturing for sci-fi and tech hardware campaigns.',
            skills='Kling AI, Flux.1 Pro, Blender AI, Stable Diffusion, Neural NeRF',
            specialization='3D Motion Showcase',
            experience_level='Expert',
            ai_tools='Kling 1.5, Flux.1 Pro, Blender AI, Magnific, DaVinci Resolve',
            content_categories='Tech & Software, Gaming & Entertainment, Cyberpunk',
            project_types='3D Product Motion, Cyberpunk Trailers, Virtual World Assets',
            availability_status='Available',
            hourly_rate_min=57720.0,
            hourly_rate_max=173160.0,
            preferred_rate_unit='per project',
            languages='English, German',
            portfolio_completeness=90,
            verification_status='Verified',
            location='Berlin, Germany / Remote',
            website='https://marcusvance.art'
        )
        db.session.add(creator2)
        db.session.flush()

        # Creator 3: Chloe Dubois (Fashion & Avatars - Pending verification)
        c3_user = User(
            email='chloe.synth@creatora.ai',
            role='creator',
            is_active=True,
            is_verified=False,
            avatar_url='https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=300&q=80'
        )
        c3_user.set_password('CreatorPass123!')
        db.session.add(c3_user)
        db.session.flush()

        creator3 = CreatorProfile(
            user_id=c3_user.id,
            display_name='Chloe Dubois',
            headline='Haute Couture & Synthetic Fashion Stylist',
            bio='Creating avant-garde digital fashion runway series and photorealistic AI model looks for digital magazines and modern apparel houses.',
            skills='Midjourney v6, Photoshop AI, LoRA Fine-Tuning, Digital Fashion Styling',
            specialization='Fashion & Apparel',
            experience_level='Intermediate',
            ai_tools='Midjourney v6, Stable Diffusion XL, Magnific AI, Clo3D',
            content_categories='Fashion & Apparel, Luxury Editorial, Social Media',
            project_types='Editorial Stills, Lookbook Creation, Virtual Mannequins',
            availability_status='Available',
            hourly_rate_min=38480.0,
            hourly_rate_max=115440.0,
            preferred_rate_unit='per project',
            languages='English, French',
            portfolio_completeness=85,
            verification_status='Pending Review',
            location='Paris, France / Remote'
        )
        db.session.add(creator3)
        db.session.flush()

        # 4. PORTFOLIO ITEMS
        p1 = PortfolioItem(
            creator_id=creator1.id,
            title='Hydra-Luxe Radiant Droplet Commercial',
            description='A high-speed macro commercial sequence highlighting serum absorption into crystalline bio-membranes. Synchronized atmospheric sound design.',
            category='Beauty & Cosmetics',
            tags='Cosmetics, Macro Video, Serum, Radiant Skin, Luxury, Runway Gen-3',
            media_type='video',
            media_url='https://assets.mixkit.co/videos/preview/mixkit-waterfall-in-forest-2213-large.mp4',
            thumbnail_url='https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1000&q=80',
            ai_tools_used='Runway Gen-3, Midjourney v6, Topaz Video AI',
            models_used='Runway Gen-3 Alpha, Midjourney v6.1',
            workflow_stages='Prompt -> Frame Interpolation -> 4K Neural Upscale -> Audio Sync',
            output_format='MP4 (4K 60fps)',
            aspect_ratio='9:16 (Vertical)',
            resolution='2160x3840 (4K)',
            intended_use='Instagram Reels & TikTok Commercial',
            asset_sources='Original generative output with commercial license',
            licensing_declaration='Full Commercial Exploitation via Paid Runway Enterprise',
            ownership_declaration='Authored and curated by Elena Rostova',
            is_featured=True,
            is_public=True
        )

        p2 = PortfolioItem(
            creator_id=creator1.id,
            title='Luminary Gold Haute Parfumerie Campaign',
            description='Cinematic luxury perfume showcase featuring molten gold particles settling over frosted crystalline flacon.',
            category='Commercial Ads',
            tags='Perfume, Luxury, Gold, Cinematic Lighting, Midjourney',
            media_type='image',
            media_url='https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=1000&q=80',
            thumbnail_url='https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=1000&q=80',
            ai_tools_used='Midjourney v6, Photoshop Generative Fill, Magnific AI',
            models_used='Midjourney v6',
            workflow_stages='Multi-prompt exploration -> Latent inpainting -> 8K Magnific upscale',
            output_format='PNG (Lossless 8K)',
            aspect_ratio='16:9 (Landscape)',
            resolution='7680x4320 (8K)',
            intended_use='Billboard & Luxury Web Showcase',
            asset_sources='Synthesized entirely in Midjourney paid plan',
            licensing_declaration='Commercial Rights Held by Creator',
            ownership_declaration='Original AI visual composition',
            is_featured=True,
            is_public=True
        )

        p3 = PortfolioItem(
            creator_id=creator2.id,
            title='Quantum Titanium Haptic Interface Reveal',
            description='Exploded-view mechanical animation of a titanium smartwatch with glowing holographic HUD telemetry.',
            category='Tech & Software',
            tags='Wearables, Cyberpunk, 3D Render, Hologram, Kling AI, Blender',
            media_type='image',
            media_url='https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1000&q=80',
            thumbnail_url='https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1000&q=80',
            ai_tools_used='Blender AI, Kling 1.5, Magnific AI',
            models_used='Kling 1.5 Pro, Flux.1',
            workflow_stages='CAD topology -> Diffusion texturing -> Neural ray-tracing',
            output_format='PNG (4K)',
            aspect_ratio='16:9 (Landscape)',
            resolution='3840x2160 (4K)',
            intended_use='Keynote Launch & Digital Ad Campaign',
            asset_sources='Synthetic 3D asset with open permissive license',
            licensing_declaration='Full Commercial Exploitation Authorized',
            ownership_declaration='Modeled and textured by Marcus Vance',
            is_featured=True,
            is_public=True
        )

        p4 = PortfolioItem(
            creator_id=creator3.id,
            title='Neo-Silk Chromatic Haute Couture Lookbook',
            description='Surrealist liquid-metallic gown in dynamic motion along a minimalist mirrored Parisian colonnade.',
            category='Fashion & Apparel',
            tags='Fashion, Haute Couture, Editorial, Fluid Silk, Metallic, Midjourney',
            media_type='image',
            media_url='https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1000&q=80',
            thumbnail_url='https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1000&q=80',
            ai_tools_used='Midjourney v6, Magnific AI',
            models_used='Midjourney v6.1',
            workflow_stages='Prompt engineering -> Texture upscaling -> Color grading',
            output_format='PNG',
            aspect_ratio='4:5 (Portrait)',
            resolution='3000x3750',
            intended_use='Social Lookbook & Digital Magazine Editorial',
            asset_sources='Original generative output',
            licensing_declaration='Commercial rights compliant with platform terms',
            ownership_declaration='Concept & Styling by Chloe Dubois',
            is_featured=True,
            is_public=True
        )
        db.session.add_all([p1, p2, p3, p4])
        db.session.flush()

        # Tools in pipeline
        pt1 = PortfolioTool(portfolio_item_id=p1.id, tool_name='Runway Gen-3', role_in_pipeline='Base Video Motion Synthesis', prompt_notes='Seed 42918, Motion Brush 6')
        pt2 = PortfolioTool(portfolio_item_id=p1.id, tool_name='Topaz Video AI', role_in_pipeline='4K Neural Upscale & 60fps Interpolation', prompt_notes='Proteus model v4')
        db.session.add_all([pt1, pt2])

        # 5. CREATIVE BRIEFS
        b1 = CreativeBrief(
            brand_id=brand1.id,
            title='Aura Glow Hydra-Luxe Serum Video Ad',
            description='We are launching our breakthrough Hydra-Luxe Bio-Serum. We need an awe-inspiring, 15-30s vertical video ad that showcases the serum\'s macro fluid texture, radiant moisture effect, and a clean minimalist bottle hero shot.',
            product_or_service='Hydra-Luxe Bio-Serum',
            objective='Brand Awareness & High-Conversion Paid Social',
            target_audience='Millennials and Gen Z skincare lovers looking for clean hydration (18-35).',
            content_category='Beauty & Cosmetics',
            content_type='AI Video Ad',
            creative_style='Ethereal Macro-Fluid, Soft Pearlescent Glow, High-Speed Slow Motion',
            preferred_platform='Instagram Reels & TikTok',
            video_duration='15-30 seconds',
            aspect_ratio='9:16 (Vertical)',
            resolution='1080x1920 (Full HD)',
            deliverables_count=2,
            required_skills='Runway Gen-3, Midjourney v6, Video Upscaling, Sound Design',
            preferred_ai_tools='Runway Gen-3, Midjourney v6, ElevenLabs, Topaz Video AI',
            budget_min=76960.0,
            budget_max=173160.0,
            currency='INR',
            deadline=datetime.utcnow() + timedelta(days=14),
            delivery_schedule='Draft styleframes in 3 days; First cut in 7 days; Final delivery in 12 days.',
            commercial_use_required=True,
            usage_duration='12 Months Worldwide Digital Rights (Organic & Paid)',
            permitted_platforms='Instagram, TikTok, YouTube Shorts, Meta Ads',
            acceptance_criteria='4K deliverable, realistic fluid dynamics, zero anatomical or artifact distortion, clean sound design.',
            review_stages=2,
            status='Published'
        )

        b2 = CreativeBrief(
            brand_id=brand2.id,
            title='NovaTech Quantum Watch Holographic Reveal',
            description='Looking for a cutting-edge 3D motion teaser video for the NovaTech Quantum Smartwatch. The video should reveal the aerospace titanium casing and a floating glowing UI holographic interface.',
            product_or_service='Quantum Smartwatch',
            objective='Product Launch & Tech Keynote',
            target_audience='Tech early adopters, executives, and programmers.',
            content_category='Tech & Software',
            content_type='3D Motion Showcase',
            creative_style='Futuristic Cyber-Tech, Titanium & Matte Black, Electric Cyan Glow',
            preferred_platform='Website Header & YouTube Shorts',
            video_duration='30 seconds',
            aspect_ratio='16:9 (Landscape)',
            resolution='3840x2160 (4K UHD)',
            deliverables_count=1,
            required_skills='Kling AI, Blender AI, 3D Motion, Sound Synthesis',
            preferred_ai_tools='Kling 1.5, Flux.1 Pro, Blender AI, Magnific',
            budget_min=115440.0,
            budget_max=240500.0,
            currency='INR',
            deadline=datetime.utcnow() + timedelta(days=20),
            delivery_schedule='Styleframes in 4 days; Rough 3D cut in 10 days; Master in 18 days.',
            commercial_use_required=True,
            usage_duration='Perpetual Global Digital Rights',
            permitted_platforms='Web, YouTube, Social, Trade Show Displays',
            acceptance_criteria='True 4K UHD, smooth camera orbits, realistic metal reflection maps.',
            review_stages=3,
            status='Published'
        )
        db.session.add_all([b1, b2])
        db.session.flush()

        # 6. APPLICATIONS & COLLABORATION WORKSPACE
        app1 = Application(
            brief_id=b1.id,
            creator_id=creator1.id,
            proposal_text=(
                "Hello Aura Glow team! I would love to direct the Hydra-Luxe campaign. "
                "I recently produced similar macro-droplet work using Runway Gen-3 with custom latent upscaling in Topaz. "
                "I will ensure the fluid physics feel natural, creamy, and deeply moisturizing, with synchronized ambient audio."
            ),
            proposed_budget=144300.0,
            estimated_delivery_days=10,
            status='Accepted',
            is_invitation=False
        )
        db.session.add(app1)
        db.session.flush()

        # Create active Project for Elena and Aura Glow
        proj1 = Project(
            brief_id=b1.id,
            brand_id=brand1.id,
            creator_id=creator1.id,
            agreed_budget=144300.0,
            currency='INR',
            agreed_deadline=datetime.utcnow() + timedelta(days=10),
            status='In Progress'
        )
        db.session.add(proj1)
        db.session.flush()

        # Milestones
        m1 = ProjectMilestone(project_id=proj1.id, title='Moodboard & Styleframes', description='3 styleframes showcasing pearlescent lighting and macro serum viscosity.', due_date=datetime.utcnow() + timedelta(days=3), status='Approved', order_index=1)
        m2 = ProjectMilestone(project_id=proj1.id, title='First Draft Video Cut', description='15s vertical draft with camera moves and placeholder sound FX.', due_date=datetime.utcnow() + timedelta(days=6), status='Submitted', order_index=2)
        m3 = ProjectMilestone(project_id=proj1.id, title='Final Master 4K Delivery', description='Upscaled master deliverable with commercial license documentation.', due_date=datetime.utcnow() + timedelta(days=10), status='Pending', order_index=3)
        db.session.add_all([m1, m2, m3])
        db.session.flush()

        # Initial revision
        rev1 = RevisionRecord(
            project_id=proj1.id,
            milestone_id=m2.id,
            version_number=1,
            requested_by_user_id=c1_user.id,
            revision_notes='Here is Draft Cut v1! Generated with Runway Gen-3 and synchronized with subtle chime audio.',
            draft_url='https://assets.mixkit.co/videos/preview/mixkit-waterfall-in-forest-2213-large.mp4',
            draft_type='video',
            status='Pending Review'
        )
        db.session.add(rev1)

        # In-project message
        msg1 = Message(
            sender_id=b1_user.id,
            receiver_id=c1_user.id,
            project_id=proj1.id,
            content="Elena, we are thrilled to collaborate with you! The initial styleframes look stunning."
        )
        msg2 = Message(
            sender_id=c1_user.id,
            receiver_id=b1_user.id,
            project_id=proj1.id,
            content="Thank you! I've uploaded Draft Cut v1 to the workspace. Looking forward to your thoughts!"
        )
        db.session.add_all([msg1, msg2])

        # Application 2 (Marcus for NovaTech - Shortlisted)
        app2 = Application(
            brief_id=b2.id,
            creator_id=creator2.id,
            proposal_text="I specialize in cyberpunk hardware reveals and have pre-trained LoRA models for brushed titanium shaders. Excited to deliver a high-energy trailer.",
            proposed_budget=173160.0,
            estimated_delivery_days=12,
            status='Shortlisted',
            is_invitation=False
        )
        db.session.add(app2)

        # 7. VERIFICATION RECORD for Chloe (Pending Review for Admin demo)
        vr1 = VerificationRecord(
            creator_id=creator3.id,
            status='Pending Review',
            portfolio_evidence_links='https://instagram.com/chloesynth_art, https://artstation.com/chloe_ai',
            tools_workflow_info='Full prompt engineering workflow utilizing Midjourney v6 paid plan and ComfyUI LoRA fine-tuning for garment textures.',
            past_references='Digital lookbook for Vogue France synthetic creative spotlight.',
            supporting_documents='Commercial subscription invoices attached for Midjourney and Magnific.'
        )
        db.session.add(vr1)

        # 8. AUDIT LOGS
        log1 = AuditLog(user_id=admin.id, action='SYSTEM_INITIALIZED', resource_type='Platform', details='Creatora AI marketplace seeded with demo accounts.')
        db.session.add(log1)

        # Notifications
        notif1 = Notification(
            user_id=c1_user.id,
            title='Welcome to Creatora AI!',
            message='Your verified creator profile is now live. Explore briefs or apply for featured campaigns.',
            link='/creator/dashboard',
            notification_type='system'
        )
        notif2 = Notification(
            user_id=b1_user.id,
            title='New Proposal Received',
            message="Elena Rostova submitted a proposal for 'Aura Glow Hydra-Luxe Serum Video Ad'.",
            link=f'/briefs/{b1.id}',
            notification_type='application'
        )
        db.session.add_all([notif1, notif2])

        db.commit = db.session.commit
        db.session.commit()
        print("[+] Seed completed successfully!")
        print("   Demo Accounts:")
        print("   - Admin:   admin@creatora.ai / AdminPass123!")
        print("   - Brand:   contact@auraglow.com / BrandPass123!")
        print("   - Creator: elena.ai@creatora.ai / CreatorPass123!")

if __name__ == '__main__':
    seed_database()
