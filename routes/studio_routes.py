import os
import uuid

from flask import Blueprint, current_app, jsonify, render_template, request, url_for
from flask_login import current_user

from models import db, PortfolioItem
from routes.auth_routes import creator_required
from services import AIService, PortfolioService
from services.video_service import create_motion_video, render_video

studio_bp = Blueprint('studio', __name__)


@studio_bp.route('/creator/studio')
@creator_required
def video_studio():
    return render_template('creator_studio.html')


@studio_bp.route('/creator/studio/storyboard', methods=['POST'])
@creator_required
def storyboard():
    data = request.get_json(silent=True) or {}
    concept = str(data.get('concept', '')).strip()
    if not concept:
        return jsonify(error='Describe the video you want to create.'), 400
    if len(concept) > 1500:
        return jsonify(error='Keep your concept under 1,500 characters.'), 400
    plan = AIService.create_video_storyboard(concept)
    return jsonify(plan=plan, model=current_app.config.get('GROQ_MODEL', 'llama-3.3-70b-versatile'))


@studio_bp.route('/creator/studio/moviepy/create', methods=['POST'])
@creator_required
def moviepy_create():
    data = request.get_json(silent=True) or {}
    prompt = str(request.form.get('prompt', data.get('prompt', ''))).strip()[:1000]
    if not prompt:
        return jsonify(error='Describe the video you want MoviePy to create.'), 400
    job_id = uuid.uuid4().hex
    output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'generated')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{job_id}-motion.mp4')
    image = request.files.get('image')
    image_path = None
    if image and image.filename:
        if not PortfolioService.is_allowed_file(image.filename, PortfolioService.ALLOWED_IMAGE_EXTS):
            return jsonify(error='Choose a PNG, JPG, JPEG, WebP, or GIF image.'), 400
        image_path = os.path.join(output_dir, f'{job_id}-source-image')
        image.save(image_path)
    try:
        create_motion_video(
            output_path,
            prompt=prompt,
            duration=request.form.get('duration', data.get('duration', 10)),
            aspect_ratio=str(request.form.get('aspect_ratio', data.get('aspect_ratio', '16:9'))),
            accent=str(request.form.get('accent', data.get('accent', '#67e8f9'))),
            image_path=image_path,
        )
    except Exception as exc:
        current_app.logger.exception('MoviePy motion-video creation failed')
        return jsonify(error=f'MoviePy could not create this video: {str(exc)[:300]}'), 422
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
    relative = os.path.relpath(output_path, current_app.config['BASE_DIR']).replace(os.sep, '/')
    return jsonify(success=True, video_url='/' + relative)


@studio_bp.route('/creator/studio/moviepy/render', methods=['POST'])
@creator_required
def moviepy_render():
    media = request.files.get('video')
    if not media or not media.filename:
        return jsonify(error='Choose a video clip to edit with MoviePy.'), 400
    if not PortfolioService.is_allowed_file(media.filename, PortfolioService.ALLOWED_VIDEO_EXTS):
        return jsonify(error='Choose an MP4, WebM, or MOV video.'), 400
    output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'generated')
    os.makedirs(output_dir, exist_ok=True)
    job_id = uuid.uuid4().hex
    source_path = os.path.join(output_dir, f'{job_id}-source{os.path.splitext(media.filename)[1].lower()}')
    output_path = os.path.join(output_dir, f'{job_id}-edited.mp4')
    media.save(source_path)
    try:
        render_video(
            source_path, output_path,
            start=request.form.get('start', 0),
            end=request.form.get('end') or None,
            title=request.form.get('title', ''),
            brightness=request.form.get('brightness', 1),
        )
    except Exception as exc:
        current_app.logger.exception('MoviePy render failed')
        return jsonify(error=f'MoviePy could not render this clip: {str(exc)[:300]}'), 422
    finally:
        if os.path.exists(source_path):
            os.remove(source_path)
    relative = os.path.relpath(output_path, current_app.config['BASE_DIR']).replace(os.sep, '/')
    return jsonify(success=True, video_url='/' + relative)


@studio_bp.route('/creator/studio/publish', methods=['POST'])
@creator_required
def publish_video():
    profile = current_user.creator_profile
    if not profile:
        return jsonify(error='Your creator profile is missing. Please contact support.'), 400

    media = request.files.get('video')
    if not media or not media.filename:
        return jsonify(error='Export a video before saving it to your portfolio.'), 400
    if not PortfolioService.is_allowed_file(media.filename, PortfolioService.ALLOWED_VIDEO_EXTS):
        return jsonify(error='Export the video as MP4, WebM, or MOV.'), 400

    title = str(request.form.get('title', '')).strip()[:150]
    if not title:
        return jsonify(error='Add a title for this portfolio video.'), 400

    media_url = PortfolioService.save_uploaded_media(media, subfolder='portfolios')
    if not media_url:
        return jsonify(error='The exported video could not be saved.'), 400

    item = PortfolioItem(
        creator_id=profile.id,
        title=title,
        description=str(request.form.get('description', 'Created in Creatora Video Studio.')).strip()[:2000],
        category='Social Media Content',
        tags='Creator Studio, Motion Graphics, Showcase Video',
        media_type='video',
        media_url=media_url,
        thumbnail_url='',
        ai_tools_used='Creatora Video Studio, Groq AI',
        models_used=current_app.config.get('GROQ_MODEL', 'llama-3.3-70b-versatile'),
        workflow_stages='Groq AI-assisted storyboard; MoviePy motion graphics, editing, and MP4 render',
        output_format=media.filename.rsplit('.', 1)[-1].upper(),
        aspect_ratio=request.form.get('aspect_ratio', '16:9')[:20],
        resolution=request.form.get('resolution', '1280x720')[:30],
        intended_use='Creator showcase video',
        asset_sources='Creator-provided assets and/or original MoviePy motion graphics',
        licensing_declaration='Creator is responsible for rights to uploaded source assets.',
        ownership_declaration='Created by the portfolio owner in Creatora Video Studio.',
        is_public=True,
    )
    db.session.add(item)
    profile.calculate_completeness()
    db.session.commit()
    return jsonify(success=True, url=url_for('creator.view_portfolio_item', item_id=item.id))
