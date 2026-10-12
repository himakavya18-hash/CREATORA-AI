class LicensingService:
    # Known commercial terms for major generative AI platforms
    TOOL_LICENSING_KNOWLEDGE = {
        'midjourney': {
            'commercial_supported': True,
            'conditions': 'Commercial use permitted on active paid plans (Basic, Standard, Pro, Mega). Free tier does not grant commercial rights.',
            'paid_ads': True
        },
        'runway': {
            'commercial_supported': True,
            'conditions': 'Standard, Pro, and Unlimited plans include full commercial exploitation rights for generated video.',
            'paid_ads': True
        },
        'stable diffusion': {
            'commercial_supported': True,
            'conditions': 'Open-source CreativeML OpenRAIL-M license permits commercial use, provided output does not violate use restrictions.',
            'paid_ads': True
        },
        'elevenlabs': {
            'commercial_supported': True,
            'conditions': 'Requires Creator tier or higher for commercial voiceover monetization & broadcast advertising rights.',
            'paid_ads': True
        },
        'pika': {
            'commercial_supported': True,
            'conditions': 'Commercial rights granted on Pro/Premier plans.',
            'paid_ads': True
        },
        'kling': {
            'commercial_supported': True,
            'conditions': 'Subject to subscription terms; review regional export restrictions for commercial broadcasts.',
            'paid_ads': True
        },
        'flux': {
            'commercial_supported': True,
            'conditions': 'FLUX.1 Pro and Schnell permit commercial usage; FLUX.1 Dev is non-commercial only.',
            'paid_ads': True
        }
    }

    @classmethod
    def check_commercial_compatibility(cls, tools_list, asset_sources='', declaration='', commercial_required=True, paid_ads=True):
        """
        Analyzes tools and declared asset information against commercial-use criteria.
        Returns:
            status: 'Compatible Based on Recorded Information' | 'Review Required' | 'Incompatible With Stated Requirements' | 'Insufficient Information'
            details: list of explanations
            passed_checks: list of verified points
            action_items: list of required next steps
        """
        if not tools_list or len(tools_list) == 0:
            return {
                'status': 'Insufficient Information',
                'status_badge': 'warning',
                'summary': 'No AI tools or generation models have been specified for licensing evaluation.',
                'details': ['Please specify which generative models and post-processing tools were utilized.'],
                'passed_checks': [],
                'action_items': ['Document all base generative models and audio/video synthesizers.'],
                'disclaimer': 'Informational assessment only. Creatora AI does not provide binding legal advice or copyright guarantees.'
            }

        passed_checks = []
        action_items = []
        details = []
        has_review_trigger = False
        has_incompatibility = False

        # 1. Evaluate tools
        for tool_name in tools_list:
            clean_name = tool_name.strip().lower()
            matched_key = None
            for k in cls.TOOL_LICENSING_KNOWLEDGE.keys():
                if k in clean_name:
                    matched_key = k
                    break

            if matched_key:
                info = cls.TOOL_LICENSING_KNOWLEDGE[matched_key]
                passed_checks.append(f"{tool_name.strip()}: {info['conditions']}")
            else:
                has_review_trigger = True
                action_items.append(f"Verify commercial terms for custom/unregistered tool: '{tool_name.strip()}'.")

        # 2. Third-party assets check
        if not asset_sources or len(asset_sources.strip()) < 10:
            has_review_trigger = True
            action_items.append("Third-party asset provenance is missing or vague. Declare stock clips, font licenses, or music.")
        else:
            passed_checks.append(f"Asset sources recorded: '{asset_sources[:60]}...'")

        # 3. Ownership / License declaration check
        if not declaration or len(declaration.strip()) < 5:
            has_review_trigger = True
            action_items.append("Creator licensing declaration statement is incomplete.")
        else:
            passed_checks.append(f"Creator declared rights: '{declaration[:60]}...'")

        # 4. Paid ads consideration
        if paid_ads and any('elevenlabs' in t.lower() for t in tools_list):
            action_items.append("Confirm creator maintains an active ElevenLabs Creator/Pro subscription for paid ad broadcasting.")

        # Determine Final Status
        if has_incompatibility:
            status = 'Incompatible With Stated Requirements'
            badge = 'danger'
            summary = 'One or more components conflict with commercial advertising requirements.'
        elif has_review_trigger:
            status = 'Review Required'
            badge = 'info'
            summary = 'Good foundation, but additional licensing confirmation is required before broadcast.'
        else:
            status = 'Compatible Based on Recorded Information'
            badge = 'success'
            summary = 'All declared tools and assets align with commercial campaign deployment requirements.'

        return {
            'status': status,
            'status_badge': badge,
            'summary': summary,
            'details': details or ['All checked models support commercial distribution under active creator plans.'],
            'passed_checks': passed_checks,
            'action_items': action_items or ['None required. Ready for brand delivery.'],
            'disclaimer': 'Notice: This evaluation provides automated guidance based on user declarations and public model licensing terms. It does not constitute legal counsel or a guarantee of third-party copyright clearance.'
        }
