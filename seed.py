from app import create_app
from models import db, Tag, Club, ClubImage, President, Announcement
from datetime import date

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # 태그 생성
    science_tag = Tag(name='과학')
    art_tag = Tag(name='미술')
    sports_tag = Tag(name='스포츠')
    db.session.add_all([science_tag, art_tag, sports_tag])

    # 동아리 예시
    club1 = Club(
        name='과학탐구부',
        one_liner='과학을 사랑하는 사람들의 모임',
        description='다양한 과학 실험과 프로젝트를 진행합니다.',
        recruit_start=date(2025, 3, 1),
        recruit_end=date(2025, 3, 15),
        interview_datetime='2025-03-17 15:00',
        capacity=20,
        form_link='https://example.com/apply',
        last_year_competition='전국과학경진대회 금상',
        contact='science@example.com',
        logo_filename='placeholder.png'
    )
    club1.tags.append(science_tag)

    club2 = Club(
        name='미술동아리',
        one_liner='창의적인 작품을 함께',
        description='유화, 수채화, 디지털아트 등 다양한 작품을 제작합니다.',
        recruit_start=date(2025, 3, 5),
        recruit_end=date(2025, 3, 20),
        capacity=15,
        contact='art@example.com',
        logo_filename='placeholder.png'
    )
    club2.tags.append(art_tag)

    db.session.add_all([club1, club2])
    db.session.commit()

    # 회장 계정 생성
    pres1 = President(username='science_pres', club_id=club1.id)
    pres1.set_password('pass1234')

    pres2 = President(username='art_pres', club_id=club2.id)
    pres2.set_password('pass1234')

    db.session.add_all([pres1, pres2])
    db.session.commit()

    # 공지 예시
    ann1 = Announcement(club_id=club1.id, title='신입 모집 공지', content='신입 부원을 모집합니다!')
    ann2 = Announcement(club_id=club2.id, title='전시회 안내', content='오는 5월, 학교 갤러리에서 전시회를 엽니다.')
    db.session.add_all([ann1, ann2])
    db.session.commit()

    print('샘플 데이터가 성공적으로 추가되었습니다.')