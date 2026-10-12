import re
from models import CreatorProfile, PortfolioItem

class MatchingService:
    DEFAULT_WEIGHTS = {
        'skills': 0.25,
        'portfolio': 0.25,
        'specialization': 0.15,
        'tools': 0.10,
        'format': 0.10,
        'budget': 0.10,
        'availability': 0.05
    }

    @classmethod
    def match_creators_for_brief(cls, brief, creators=None, weights=None, filters=None):
        """
        Ranks creators for a specific creative brief using hybrid explainable matching.
        Returns a list of dicts: [ { 'creator': CreatorProfile, 'score': int, 'breakdown': dict, 'strengths': list, 'cautions': list }, ... ]
        """
        if weights is None:
            weights = cls.DEFAULT_WEIGHTS
        if filters is None:
            filters = {}

        if creators is None:
            creators = CreatorProfile.query.all()

        results = []
        brief_skills = [s.strip().lower() for s in (brief.required_skills or '').split(',') if s.strip()]
        brief_tools = [t.strip().lower() for t in (brief.preferred_ai_tools or '').split(',') if t.strip()]
        brief_category = (brief.content_category or '').strip().lower()
        brief_type = (brief.content_type or '').strip().lower()
        brief_style = (brief.creative_style or '').strip().lower()
        brief_aspect = (brief.aspect_ratio or '').strip().lower()

        for creator in creators:
            # 1. Eligibility Filters
            if filters.get('availability') and creator.availability_status != filters['availability']:
                continue
            if filters.get('verification_only') and creator.verification_status != 'Verified':
                continue
            if filters.get('max_rate') and creator.hourly_rate_min > float(filters['max_rate']):
                continue

            # 2. Factor: Skills Match (25%)
            c_skills = [s.strip().lower() for s in (creator.skills or '').split(',') if s.strip()]
            matched_skills = set(c_skills).intersection(set(brief_skills)) if brief_skills else set(c_skills)
            skills_ratio = len(matched_skills) / len(brief_skills) if brief_skills else 0.8
            skills_score = min(1.0, skills_ratio)

            # 3. Factor: Portfolio Relevance (25%)
            items = creator.portfolio_items.filter_by(is_public=True).all()
            matched_items_count = 0
            has_matching_aspect = False
            for it in items:
                it_text = f"{it.title} {it.description} {it.category} {it.tags}".lower()
                if brief_category in it_text or brief_type in it_text or any(bs in it_text for bs in brief_skills):
                    matched_items_count += 1
                if brief_aspect and brief_aspect.split(' ')[0] in (it.aspect_ratio or '').lower():
                    has_matching_aspect = True
            
            if items:
                portfolio_score = min(1.0, (matched_items_count / min(len(items), 3)) * 0.8 + (0.2 if matched_items_count > 0 else 0.0))
            else:
                portfolio_score = 0.25 # Fair chance for newer creators with zero portfolio uploaded yet

            # 4. Factor: Specialization (15%)
            c_spec = (creator.specialization or '').lower()
            if brief_category in c_spec or brief_type in c_spec or c_spec in brief_type:
                spec_score = 1.0
            elif any(w in c_spec for w in brief_category.split()):
                spec_score = 0.75
            else:
                spec_score = 0.40

            # 5. Factor: AI Tools and Models (10%)
            c_tools = [t.strip().lower() for t in (creator.ai_tools or '').split(',') if t.strip()]
            matched_tools = set(c_tools).intersection(set(brief_tools)) if brief_tools else set(c_tools)
            tools_score = len(matched_tools) / len(brief_tools) if brief_tools else 0.75
            tools_score = min(1.0, tools_score)

            # 6. Factor: Output Format Compatibility (10%)
            format_score = 0.6
            if has_matching_aspect:
                format_score += 0.3
            if brief_type == 'ai video ad' and any(it.media_type == 'video' for it in items):
                format_score += 0.1
            format_score = min(1.0, format_score)

            # 7. Factor: Budget Compatibility (10%)
            b_min = brief.budget_min or 300.0
            b_max = brief.budget_max or 2000.0
            c_min = creator.hourly_rate_min or 250.0
            c_max = creator.hourly_rate_max or 1500.0

            if c_min <= b_max and c_max >= b_min:
                budget_score = 1.0
            elif c_min > b_max:
                diff = c_min - b_max
                budget_score = max(0.2, 1.0 - (diff / b_max))
            else:
                budget_score = 0.85

            # 8. Factor: Availability (5%)
            if creator.availability_status == 'Available':
                avail_score = 1.0
            elif creator.availability_status == 'Busy':
                avail_score = 0.4
            else:
                avail_score = 0.1

            # Total Weighted Score (0 to 100)
            total = (
                skills_score * weights.get('skills', 0.25) +
                portfolio_score * weights.get('portfolio', 0.25) +
                spec_score * weights.get('specialization', 0.15) +
                tools_score * weights.get('tools', 0.10) +
                format_score * weights.get('format', 0.10) +
                budget_score * weights.get('budget', 0.10) +
                avail_score * weights.get('availability', 0.05)
            )
            final_percentage = int(round(total * 100))

            # Explainable Strengths and Cautions
            strengths = []
            cautions = []

            if skills_score >= 0.7:
                strengths.append(f"Strong skill alignment with brief requirements ({', '.join(list(matched_skills)[:3]) or 'Core capabilities'}).")
            else:
                cautions.append("Some required skills are not explicitly listed on creator profile.")

            if matched_items_count > 0:
                strengths.append(f"{matched_items_count} relevant project(s) found in creator's portfolio.")
            elif len(items) == 0:
                cautions.append("No portfolio items uploaded yet. Recommendation includes fair-chance baseline.")
            else:
                cautions.append("Portfolio items differ in theme/category from this campaign brief.")

            if budget_score >= 0.9:
                strengths.append(f"Rates (₹{creator.hourly_rate_min:.0f}-₹{creator.hourly_rate_max:.0f}) fit within campaign budget range.")
            else:
                cautions.append(f"Preferred rates (₹{creator.hourly_rate_min:.0f}+) are slightly higher than brief budget (₹{brief.budget_max:.0f}).")

            if creator.availability_status == 'Available':
                strengths.append("Creator is marked immediately available for collaboration.")
            else:
                cautions.append(f"Creator status is currently '{creator.availability_status}'.")

            if creator.verification_status == 'Verified':
                strengths.append("Creator profile independently verified by Creatora moderation.")

            results.append({
                'creator': creator,
                'score': final_percentage,
                'breakdown': {
                    'skills': int(skills_score * 100),
                    'portfolio': int(portfolio_score * 100),
                    'specialization': int(spec_score * 100),
                    'tools': int(tools_score * 100),
                    'format': int(format_score * 100),
                    'budget': int(budget_score * 100),
                    'availability': int(avail_score * 100)
                },
                'strengths': strengths,
                'cautions': cautions
            })

        # Sort descending by score
        results.sort(key=lambda r: r['score'], reverse=True)
        return results
