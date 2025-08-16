import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, Tag, Club, ClubImage, President, Announcement


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return President.query.get(int(user_id))

    # --- 유틸 ---
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    # --- 라우트 ---
    @app.route('/')
    def index():
        tag = request.args.get('tag')
        q = Club.query
        if tag:
            q = q.join(Club.tags).filter(Tag.name == tag)
        clubs = q.order_by(Club.name.asc()).all()
        tags = Tag.query.order_by(Tag.name.asc()).all()
        fav_ids = session.get('favorites', [])
        return render_template('index.html', clubs=clubs, tags=tags, selected_tag=tag, fav_ids=fav_ids)

    @app.route('/club/<int:club_id>')
    def club_detail(club_id):
        club = Club.query.get_or_404(club_id)
        fav_ids = session.get('favorites', [])
        anns = Announcement.query.filter_by(club_id=club.id).order_by(Announcement.created_at.desc()).all()
        return render_template('club_detail.html', club=club, fav_ids=fav_ids, announcements=anns)

    # 관심 동아리 (세션 기반, 최대 3개)
    @app.route('/favorite/<int:club_id>', methods=['POST'])
    def toggle_favorite(club_id):
        _ = Club.query.get_or_404(club_id)
        favs = session.get('favorites', [])
        if club_id in favs:
            favs.remove(club_id)
            flash('관심 동아리에서 제거했습니다.', 'info')
        else:
            if len(favs) >= 3:
                flash('관심 동아리는 최대 3개까지 가능합니다.', 'warning')
                return redirect(request.referrer or url_for('index'))
            favs.append(club_id)
            flash('관심 동아리에 추가했습니다.', 'success')
        session['favorites'] = favs
        session.modified = True
        return redirect(request.referrer or url_for('index'))

    @app.route('/my-favorites')
    def my_favorites():
        favs = session.get('favorites', [])
        clubs = Club.query.filter(Club.id.in_(favs)).all() if favs else []
        return render_template('my_favorites.html', clubs=clubs)

    # 캘린더
    @app.route('/calendar')
    def calendar_view():
        clubs = Club.query.all()
        return render_template('calendar.html', clubs=clubs)

    # 회장 로그인/로그아웃
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = President.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('로그인 성공', 'success')
                return redirect(url_for('dashboard'))
            flash('아이디 또는 비밀번호가 잘못되었습니다.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('로그아웃 되었습니다.', 'info')
        return redirect(url_for('index'))

    # 회장 대시보드
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return redirect(url_for('edit_club', club_id=current_user.club_id)) if current_user.club_id else redirect(url_for('new_club'))

    # 동아리 생성
    @app.route('/clubs/new', methods=['GET', 'POST'])
    @login_required
    def new_club():
        if request.method == 'POST':
            name = request.form.get('name')
            one_liner = request.form.get('one_liner')
            description = request.form.get('description')
            recruit_start = request.form.get('recruit_start')
            recruit_end = request.form.get('recruit_end')
            interview_datetime = request.form.get('interview_datetime')
            capacity = request.form.get('capacity', type=int)
            form_link = request.form.get('form_link')
            last_year_competition = request.form.get('last_year_competition')
            contact = request.form.get('contact')
            tags_raw = request.form.get('tags', '')

            club = Club(
                name=name,
                one_liner=one_liner,
                description=description,
                recruit_start=datetime.fromisoformat(recruit_start).date() if recruit_start else None,
                recruit_end=datetime.fromisoformat(recruit_end).date() if recruit_end else None,
                interview_datetime=interview_datetime,
                capacity=capacity,
                form_link=form_link,
                last_year_competition=last_year_competition,
                contact=contact,
            )

            # 태그 처리
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for tname in tag_names:
                tag = Tag.query.filter_by(name=tname).first()
                if not tag:
                    tag = Tag(name=tname)
                    db.session.add(tag)
                club.tags.append(tag)

            # 로고 업로드
            logo = request.files.get('logo')
            if logo and allowed_file(logo.filename):
                filename = secure_filename(logo.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logo.save(save_path)
                club.logo_filename = filename

            db.session.add(club)
            db.session.commit()

            # 회장-동아리 연결
            current_user.club_id = club.id
            db.session.commit()

            flash('동아리를 생성했습니다.', 'success')
            return redirect(url_for('edit_club', club_id=club.id))
        return render_template('new_club.html')

    # 동아리 수정
    @app.route('/clubs/<int:club_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_club(club_id):
        club = Club.query.get_or_404(club_id)
        if current_user.club_id != club.id:
            flash('해당 동아리를 수정할 권한이 없습니다.', 'danger')
            return redirect(url_for('index'))

        if request.method == 'POST':
            club.name = request.form.get('name')
            club.one_liner = request.form.get('one_liner')
            club.description = request.form.get('description')
            rs = request.form.get('recruit_start')
            re = request.form.get('recruit_end')
            club.recruit_start = datetime.fromisoformat(rs).date() if rs else None
            club.recruit_end = datetime.fromisoformat(re).date() if re else None
            club.interview_datetime = request.form.get('interview_datetime')
            club.capacity = request.form.get('capacity', type=int)
            club.form_link = request.form.get('form_link')
            club.last_year_competition = request.form.get('last_year_competition')
            club.contact = request.form.get('contact')
            club.closed = bool(request.form.get('closed'))

            # 태그 재설정
            club.tags.clear()
            tags_raw = request.form.get('tags', '')
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for tname in tag_names:
                tag = Tag.query.filter_by(name=tname).first()
                if not tag:
                    tag = Tag(name=tname)
                    db.session.add(tag)
                club.tags.append(tag)

            # 로고 교체
            logo = request.files.get('logo')
            if logo and allowed_file(logo.filename):
                filename = secure_filename(logo.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logo.save(save_path)
                club.logo_filename = filename

            # 활동 사진 추가
            for i in range(1, 6):
                f = request.files.get(f'image{i}')
                if f and allowed_file(f.filename):
                    fname = secure_filename(f.filename)
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    db.session.add(ClubImage(filename=fname, club=club))

            db.session.commit()
            flash('수정되었습니다.', 'success')
            return redirect(url_for('edit_club', club_id=club.id))

        # 표시용 태그 CSV
        tags_csv = ', '.join(t.name for t in club.tags)
        return render_template('edit_club.html', club=club, tags_csv=tags_csv)

    # 공지 작성 (관심 동아리 알림용)
    @app.route('/clubs/<int:club_id>/announcements', methods=['POST'])
    @login_required
    def post_announcement(club_id):
        club = Club.query.get_or_404(club_id)
        if current_user.club_id != club.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('index'))
        title = request.form.get('title')
        content = request.form.get('content')
        if not title:
            flash('제목을 입력하세요.', 'warning')
            return redirect(url_for('edit_club', club_id=club.id))
        db.session.add(Announcement(club_id=club.id, title=title, content=content))
        db.session.commit()
        flash('공지를 등록했습니다.', 'success')
        return redirect(url_for('edit_club', club_id=club.id))

    # 업로드 파일 서빙
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # 초기화 명령
    @app.cli.command('init-db')
    def init_db():
        db.create_all()
        print('DB created.')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)