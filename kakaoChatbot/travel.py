from flask import Flask, request, jsonify, make_response
import pymysql
import sys
import json
import re
import random
import logging

from food_img_url_1 import *

app = Flask(__name__)

# MySQL 데이터베이스 연결 설정
db_config = {
    'host': '3.39.183.190',
    'user': 'root',
    'password': '12345',
    'db': 'chatbot',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor,
    'port': 54329
}


# 사용자가 입력한 정보을 저장할 전역 변수
user_region = None
locationData = None     # 지역
travelData = None       # 여행지
hotelData = None        # 숙소
restaurantData = None   # 맛집

# 인사말
@app.route('/hello', methods=['POST'])
def sayHello():
    body = request.get_json()
    
    logging.debug(f" 채팅 시작 ----------------> {body}")
    
    print(body)

    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": "안녕하세요.(깜찍) 저는 트레봇입니다!!!",
                        "description": "사용자님에게 다양한 여행지를 추천해드려요!!"+'\n\n'
                                        +"국내의 숨겨진 보석 같은 장소부터 유명한 명소까지, 여러분의 여행이 더욱 특별해질 수 있도록 다양한 여행지와 근처의 숙소와 맛집까지 모든것을 소개해 드릴게요. (크크)"
                                        +'\n\n\n' 
                                        +"---------------------------------------"
                                        +"여행하고싶으신 지역을 입력해주세요!(ex 서울, 제주도, 강원도 ...)",
                        "thumbnail": {
                            "imageUrl":"https://proxy.goorm.io/service/6646bcaf7adb2df16bf1ca4d_d1rE3tcRNM4ZEYpKhkY.run.goorm.io/9080/file/load/thumbnail.png?path=d29ya3NwYWNlJTJGY2hhdGJvdF9teXNxbCUyRnRodW1ibmFpbC5wbmc=&docker_id=d1rE3tcRNM4ZEYpKhkY&secure_session_id=CyhztIOMY14xBPdmbGgKsyKarUEvgAfG"
                            
                        }                     
                    }
                }
            ]
        }
    }

    response = make_response(json.dumps(response_body, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# 지역명 정규화 함수
def normalize_region(region_name):
    region_patterns = {
        
        '제주특별자치도': r'제주특별자치도|제주도|제주',
        '강원특별자치도': r'강원특별자치도|강원도|강원',
        '서울특별시': r'서울특별시|서울시|서울',
        '부산광역시': r'부산광역시|부산시|부산',
        '울산광역시': r'울산광역시|울산시|울산',
        '대전광역시': r'대전광역시|대전시|대전',
        '광주광역시': r'광주광역시|광주시|광주',
        '대구광역시': r'대구광역시|대구시|대구',
        '인천광역시': r'인천광역시|인천시|인천',
        '세종특별자치시': r'세종특별자치시|세종시|세종',
        '충청북도': r'충청북도|충북',
        '충청남도': r'충청남도|충남',
        '경상북도': r'경상북도|경북',
        '경상남도': r'경상남도|경남',
        '전라북도': r'전라북도|전북',
        '전라남도': r'전라남도|전남',
        '경기도': r'경기도|경기'
    }
    
    for normalized_name, pattern in region_patterns.items():
        if re.search(pattern, region_name, re.IGNORECASE):
            return normalized_name
    
    return None


logging.basicConfig(level=logging.DEBUG)

@app.route('/travel', methods=['POST'])
def travel():
    global user_region
    global locationData

    user_input = request.get_json()
    utterance = user_input.get('userRequest', {}).get('utterance')
    logging.debug(f" 채팅 시작 ----------------> {utterance}")
    
    if not user_region:
        user_region = normalize_region(utterance)
        logging.debug(f"User Input: {utterance}, Normalized Region: {user_region}")
        
        if user_region is None:
            response_text = "시, 도 명을 잘못 입력하신 것 같아요. 다시 입력해주세요.(눈물)"
        else:
            response_text = f"{user_region}의 여행지를 추천 받고 싶으시군요!\n\n조금 더 구체적으로 추천해드리기위해 시, 군, 구 명을 입력해주세요.(잘자)"
    else:
        user_district = utterance

        normalized_region = normalize_region(user_region)
        logging.debug(f"Normalized Region: {normalized_region}")
        logging.debug(f"User District: {user_district}")

        if normalized_region is None:
            response_text = "시, 도 명을 잘못 입력하신 것 같아요. 다시 입력해주세요.(눈물)"
        else:
            # MySQL 데이터베이스 연결 및 쿼리 실행
            connection = pymysql.connect(**db_config)
            try:
                with connection.cursor() as cursor:
                    sql = """
                    SELECT POI_NM, PROVINCE_NM, COUNTY_NM, LEGAL_DISTRICT_NM, VILLAGE_NM, LNBR_NO, RDNMADR_NM, BULD_NO, LC_LO, LC_LA
                    FROM travel
                    WHERE PROVINCE_NM LIKE %s AND COUNTY_NM = %s
                    """
                    cursor.execute(sql, (f"%{normalized_region}%", user_district))
                    result = cursor.fetchall()

            finally:
                connection.close()

            # logging.debug(f"Filtered Result: {result}")  #  뽑아온 데이터 쿼리 목록

            cards = []
            if not result:
                response_text = f"{user_region} {user_district}의 여행지를 찾을 수 없습니다..(눈물)"
            else:
                places = random.sample(result, min(len(result), 10))  # 최대 10개의 장소 추천
                
                full_region= f"저는 {user_region} {user_district}의 여행지 중 이곳을 추천해 드리고 싶어요!!(최고)(최고)"
                
                locationData= user_region + " "+ user_district
                
                
                for place in places:
                    poi_nm = place['POI_NM']
                    province_nm = place['PROVINCE_NM']
                    county_nm = place['COUNTY_NM']
                    legal_district_nm = place['LEGAL_DISTRICT_NM']
                    village_nm = place['VILLAGE_NM']
                    lnbr_no = place['LNBR_NO']
                    rdnmadr_nm = place['RDNMADR_NM']
                    build_no = place['BULD_NO']
                    lc_lo = place['LC_LO']
                    lc_la = place['LC_LA']

                    description = (
                        f"> 지역명: {province_nm} {county_nm}\n"
                        f"> 법정동명: {legal_district_nm}\n"
                        f"> 읍면동명: {village_nm}\n"
                        f"> 지번: {lnbr_no}\n"
                        f"> 도로명주소: {rdnmadr_nm} {build_no}\n"
                    )

                    card = {
                        "title": poi_nm,
                        "description": description,
                        "buttons": [
                            {
                                "action": "webLink",
                                "label": "여행지 위치 보기",
                                "webLinkUrl": f"https://map.naver.com/p/search/{poi_nm}"
                            }
                        ]
                    }
                    cards.append(card)

                    
                response_body = {
                    "version": "2.0",
                    "template": {
                        "outputs": [
                            {
                                "simpleText": {
                                    "text": full_region
                                }
                            },
                            {
                                "carousel": {
                                    "type": "textCard",
                                    "items": cards
                                }
                            },
                            {
                                "textCard": {
                                    "title": "추천해드린 여행지는 어떠신가요?(꺄아)\n\n",
                                    "description": "> 아래의 버튼을 통해 다음 대화를 이어갈 수 있습니다.",
                                    "buttons": [
                                        {
                                            "action": "message",
                                            "label": "여행지 주변 맛집 추천",
                                            "messageText": "맛집 추천"
                                        },
                                        {
                                            "action": "message",
                                            "label": "여행지 주변 숙소 추천",
                                            "messageText": "숙소 추천"
                                        },
                                        {
                                            "action": "message",
                                            "label": "이제 괜찮아요",
                                            "messageText": "그만하기"
                                        },
                                        {
                                            "action": "message",
                                            "label": "저장 보기",
                                            "messageText": "저장된 여행지역 보기"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
                
                user_region = None
                logging.debug(f"{locationData}")
                
                
                response = make_response(json.dumps(response_body, ensure_ascii=False))
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response

        # user_region = None  # 초기화

    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": response_text
                    }
                }
            ]
        }
    }

    response = make_response(json.dumps(response_body, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# =====================================================================================

# ======================================================================================

@app.route('/bye', methods=['POST'])
def sayEnd():
    
    global user_region
    global locationData
    
    body = request.get_json()
    print(body)

    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [  
                {
                    "basicCard": {
                        "title": "추천해드린 여행지와 맛집 그리고 숙소의 정보는 만족스러우셨나요?(방긋)",
                        "description":"\n\n저는 여행을 떠나고 싶지만 쉽게 목적지를\n정하지 못하는 여러분에게 유용한 정보를 주는 저기어때 봇입니다!!\n\n"
                                        +"앞으로도 궁금한 점이 생기면 언제든지\n저를 찾아주세요.\n행복하고 안전한 여행 되세요!(크크)",
                        "thumbnail": {
                            "imageUrl":"https://proxy.goorm.io/service/6646bcaf7adb2df16bf1ca4d_d1rE3tcRNM4ZEYpKhkY.run.goorm.io/9080/file/load/travel3.png?path=d29ya3NwYWNlJTJGY2hhdGJvdF9teXNxbCUyRnRyYXZlbDMucG5n&docker_id=d1rE3tcRNM4ZEYpKhkY&secure_session_id=CyhztIOMY14xBPdmbGgKsyKarUEvgAfG"
                            
                        }                     
                    }
                }
            ]
        }
    }
    user_region = None
    locationData = None

    response = make_response(json.dumps(response_body, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response
# --------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/api/welcome', methods=['POST'])
def welcome():
    global user_region
    global locationData
    
    # JSON 데이터에서 userRequest.utterance 값을 가져옴
    user_input = request.get_json()
    utterance = user_input.get('userRequest', {}).get('utterance')
    
    
    logging.debug(f"숙소추천 지역 받아옴 : {locationData}")
    
    if locationData:
        # user_region 값을 공백을 기준으로 나눔
        SidoGu = locationData.split()

        if len(SidoGu) >= 2:
            Sido = SidoGu[0]
            Gu = SidoGu[1]
        else:
            Sido = "알 수 없음"
            Gu = "알 수 없음"
        
        # 웰컴 블록 응답
        welcome_response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "어서오세요!(하트뿅) \n여행 추천 챗봇 룸바룸바 봇 입니다.\n\n"
                                    +"여행을 더욱 특별하게 만들어줄\n'룸바룸바'의 특급 숙소 탐험에 오신 것을 환영합니다!(윙크)\n\n이곳에서는 여행의 기쁨과 설렘이 만납니다. 여행의 숨은 보물을 찾아 떠나는 여정, 함께해요!(쑥스)\n\n"
                                    +"'룸바룸바'가 선택한 그 지역의 추천 숙소 10곳을 랜덤으로 소개해줄게요.(컴온)\n"
                                    +"\n좀 더 기분 좋게 여행을 시작해보세요! "
                        }
                    },
                    {
                        "simpleText": {
                            "text": f"{Sido} {Gu} (으)로 가시는군요!\n\n아래의 버튼을 통해 숙소 유형을 선택해주세요."
                        }
                    },
                ],
                "quickReplies": [
                    {
                        "messageText": "호텔",
                        "action": "message",
                        "label": "호텔"
                    },
                    {
                        "messageText": "모텔",
                        "action": "message",
                        "label": "모텔"
                    },
                    {
                        "messageText": "펜션",
                        "action": "message",
                        "label": "펜션"
                    },
                    {
                        "messageText": "게스트하우스",
                        "action": "message",
                        "label": "게스트하우스"
                    }
                ]
            }
        }
    else:
        welcome_response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "유효한 입력이 없습니다."
                        }
                    }
                ]
            }
        }
    
    return jsonify(welcome_response)

@app.route('/api/reco', methods=['POST'])
def recommend():
    global user_region
    global locationData
    
    user_input = request.get_json()
    button = user_input.get('userRequest', {}).get('utterance')
    
    
    logging.debug(f"숙소 유형 검색 : {locationData}")
    
    if locationData:
        # Global_User_Input 값을 공백을 기준으로 나눔
        SidoGu = locationData.split()

        if len(SidoGu) >= 2:
            Sido = SidoGu[0]
            Gu = SidoGu[1]
        else:
            Sido = "알 수 없음"
            Gu = "알 수 없음"


    # 데이터베이스에서 숙소 목록 조회
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT *
                FROM hotels
                WHERE PROVINCE_NM LIKE %s AND COUNTY_NM = %s AND LC_TY_NM = %s
                """
            cursor.execute(sql, (Sido, Gu, button))
            result = cursor.fetchall()

    finally:
            connection.close()

    if not result:
        return jsonify({"error": "No accommodations found for the given location"}), 404

    # 숙소 목록을 랜덤으로 10개만 선택
    accommodations_sample = random.sample(result, min(len(result), 10))
    
    response_text = f"{locationData}에서\n제가 추천해드릴 숙소들입니다!"

    cards = []

    for place in accommodations_sample:
        num_cd=place['NUM_CD']
        poi_nm = place['LC_NM']
        province_nm = place['PROVINCE_NM']
        county_nm = place['COUNTY_NM']
        legal_district_nm = place['LEGAL_DISTRICT_NM']
        village_nm = place['VILLAGE_NM']
        lc_la = place['LC_LA']
        lc_lo = place['LC_LO']
        lc_ty_nm = place['LC_TY_NM']
        lc_ty_ph = place['LC_TY_PH']

        description = (
            f"> 지역: {province_nm} {county_nm}\n"
            f"> 숙소유형: {lc_ty_nm}\n"

        )

        card = {
            "title": poi_nm,
            "description": description,
            "thumbnail": {
              "imageUrl": lc_ty_ph
            },
            "buttons": [
                {
                    "action": "webLink",
                    "label": "예약하기",
                    "webLinkUrl": f"https://place-site.yanolja.com/places/{num_cd}"
                }
            ]
        }
        if not lc_ty_nm:
                response_text = f"{locationData} 의 숙소가 없습니다."
        cards.append(card)

    # 응답 템플릿 구성
    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": response_text
                    }
                },
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": cards
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "숙소 추천",
                    "action": "message",
                    "label": "다시 추천 받기"
                },
                {
                    "messageText": "맛집 추천",
                    "action": "message",
                    "label": "맛집 추천 받기"
                },
                {
                    "messageText": "채팅 종료",
                    "action": "message",
                    "label": "검색 종료"
                }
            ]
        }
    }
    logging.debug(f"저장된 전역 변수 ---------->> {user_region} {locationData}")
    user_region = None
    # locationData = None

    logging.debug(f"삭제된 전역 변수 ---------->> {user_region} {locationData}")
    return jsonify(response_body)


# -------------------------------------------맛집 ----------------------------------------------------------------------

# 인트로
@app.route('/api/intro', methods=['POST'])
def bot_intro():
    global user_region 
    global locationData
    
    logging.debug(f"맛집 인트로 시작")
    
    user_input = request.get_json()
    greeting = user_input.get('userRequest',{}).get('utterance')
    
    
    response_body= {
        "version": "2.0",
                    "template": {
                        "outputs": [
                            {
                                'basicCard':
                                {
                                    "title": "안녕하세요! 맛있는 여행을 책임질 딜리봇이에요!!(방긋)",
                                    "description": "여행 중 최고의 맛집을 찾아드릴 딜리봇입니다."+'\n\n' 
                                                    +"저는 여러분이 어디를 여행하시든, 여행을 더욱 맛있고 기억에 남게 만들어 드릴 수 있습니다.(야옹)"+'\n\n'
                                                    +"어디 계시든, 최적의 맛집을 안내해드립니다. 여행과 미식의 즐거움을 함께 만끽해볼까요?(해)(음표)",
                                    "thumbnail": {
                                        "imageUrl": "https://img.freepik.com/premium-vector/top-view-bowl-japanese-ramen-noodles-with-shrimps_132937-187.jpg?w=996"
                                        },
                                    "buttons": [
                                        {
                                            "action": "message",
                                            "label": "지역 맛집 추천받기",
                                            "messageText":"지역 맛집 추천해줘"   
                                                                          
                                        },
                                        {
                                            "action": "message",
                                            "label": "메뉴로 맛집 검색하기",
                                            "messageText":"메뉴로 맛집 검색해줘"
                                        },
                                        {
                                            "action": "message",
                                            "label": "이제 괜찮아요",
                                            "messageText":"그만하기"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                   }

    response = make_response(json.dumps(response_body, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# 2-1. 지역으로 바로 검색
@app.route('/api/instant', methods=['POST'])
def instant():
    global user_region 
    global locationData
    
    logging.debug("====================맛집 - 지역 필터링 시작==========================")
    
    logging.debug(f"지역 맛집 주소 검색 : {locationData}")
    
    user_input = request.get_json()
    button = user_input.get('userRequest', {}).get('utterance')

    #전역변수 받기
    if locationData :
        SidoGu = locationData.split()

        if len(SidoGu) >= 2:
            Sido = SidoGu[0]
            Gu = SidoGu[1]

        else:
            Sido = "알 수 없음"
            Gu = "알 수 없음"

    # 데이터베이스에서 숙소 목록 조회
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT *
                FROM restaurant
                WHERE PROVINCE_NM LIKE %s AND COUNTY_NM = %s
                """
            cursor.execute(sql, (Sido, Gu))
            result = cursor.fetchall()

    finally:
            connection.close()

    if not result:
        return jsonify({"error": "No restaurant found for the given location"}), 404
    rand_place = random.sample(result, min(len(result), 10))


# 응답 생성
    cards = []
    for place in rand_place:
        poi_nm = place['POI_NM']
        lc_nm = place['LC_NM']
        province_nm = place['PROVINCE_NM']
        country_nm = place['COUNTY_NM']
        info_2 = place['INFO_2']

        # 메뉴별이미지 출력
        if lc_nm == '한식':
            thumb = random.choice(kor_food_url)
        elif lc_nm == '일식':
            thumb = random.choice(ja_food_url)
        elif lc_nm == '양식':
            thumb = random.choice(west_food_url)
        elif lc_nm == '카페':
            thumb = random.choice(cafe_food_url)
        elif lc_nm == '바/술집':
            thumb = random.choice(bar_food_url)
        elif lc_nm == '기타':
            thumb = random.choice(else_food_url)
        elif lc_nm == '패스트푸드':
            thumb = random.choice(fast_food_url)
        elif lc_nm == '중식':
            thumb = random.choice(chi_food_url)
        
        
        description = (          
            f"위치: {info_2}\n"
            f"메뉴: {lc_nm}\n"            
            )
        card = {
                        "title": poi_nm,
                        "description": description,
                        "thumbnail":{
                          "imageUrl": thumb
                        },
                        "buttons": [
                            {
                                "action": "webLink",
                                "label": "검색",
                                "webLinkUrl": f"https://map.naver.com/p/search/{locationData} {poi_nm}"
                            }
                        ]
                    }
        cards.append(card)
        
    response_body = {
    "version": "2.0",
    "template": {
      "outputs": [
         {
            "simpleText": {
                "text": f"{locationData}의\n주변 맛집 리스트입니다!(방긋)"
            }
         },
         {
            "carousel": {
                "type": "basicCard",
                "items": cards
            }
          }
       ],
      "quickReplies": [
                {
                    "action": "message",
                    "label": "다른 맛집 추천받기",
                    "messageText": "지역 맛집 추천해줘"
                },
                {
                    "messageText": "숙소 추천",
                    "action": "message",
                    "label": "숙소 추천받기"
                },
                {
                    "messageText": "채팅 종료",
                    "action": "message",
                    "label": "이제 괜찮아요"
                }
            ]
     }
    }
    return response_body

# ======================================================================================================
@app.route('/detail', methods=['POST'])
def test_detail():
    global user_region 
    global locationData
    
    user_input = request.get_json()
    button = user_input.get('userRequest', {}).get('utterance')
    
    logging.debug(user_input)
    
    logging.debug("====================맛집 - 메뉴 필터링 시작==========================")
    
    logging.debug(f"매뉴 검색 주소 : {locationData}")
    
    # 전역변수 받기
    if locationData:
        SidoGu = locationData.split()

        if len(SidoGu) >= 2:
            Sido = SidoGu[0]
            Gu = SidoGu[1]
        
        else:
            Sido = "알 수 없음"
            Gu = "알 수 없음"
    

    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT *
                FROM restaurant
                WHERE PROVINCE_NM LIKE %s AND COUNTY_NM = %s
                """
            cursor.execute(sql, (Sido, Gu))
            result = cursor.fetchall()

    finally:
            connection.close()
    if not result:
        return jsonify({"error": "No restaurant found for the given location"}), 404
    rand_place = random.sample(result, min(len(result), 10))
    
    response_body = {
        "version": "2.0",
        "template": {
             "outputs": [
                {
                  "simpleText": {
                    "text": "아래의 버튼 중 골라주세요.",
                   }
                },
              ],
              "quickReplies": [
                {
                    "messageText": "한식",
                    "action": "message",
                    "label": "한식"
                },
                {
                    "messageText": "중식",
                    "action": "message",
                    "label": "중식"
                },
                {
                    "messageText": "양식",
                    "action": "message",
                    "label": "양식"
                },
                {
                    "messageText": "일식",
                    "action": "message",
                    "label": "일식"
                },
                {
                    "messageText": "카페",
                    "action": "message",
                    "label": "카페"
                },
                {
                    "messageText": "패스트푸드",
                    "action": "message",
                    "label": "패스트푸드"
                },
                {
                    "messageText": "바/술집",
                    "action": "message",
                    "label": "바/술집"
                },
                {
                    "messageText": "기타",
                    "action": "message",
                    "label": "기타"
                } 
                 
            ]
           }
        }

    return response_body
    
# ======================================================================================================

# 2-2. 메뉴 상세 검색
@app.route('/api/detail', methods=['POST'])
def detail():
    global user_region 
    global locationData
    
    logging.debug("====================맛집 - 메뉴 필터링 시작==========================")
    
    logging.debug(f"매뉴 검색 주소 : {locationData}")

    # 전역변수 받기
    if locationData:
        SidoGu = locationData.split()

        if len(SidoGu) >= 2:
            Sido = SidoGu[0]
            Gu = SidoGu[1]
        
        else:
            Sido = "알 수 없음"
            Gu = "알 수 없음"
    
    
    user_input = request.get_json()
    menu = user_input.get('userRequest', {}).get('utterance')
    #debug
    logging.debug(menu)
    
    
    # 데이터베이스에서 맛집 목록 조회
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT POI_NM, LC_NM, INFO_2 
                FROM restaurant
                WHERE PROVINCE_NM LIKE %s AND COUNTY_NM = %s AND LC_NM = %s
                """
            cursor.execute(sql, (Sido, Gu, menu))
            result = cursor.fetchall()

    finally:
            connection.close()
            
    # logging.debug(f"Filtered Result: {result}")

    if not result:
        return jsonify({"error": "No restaurant found for the given location"}), 404
    rand_place = random.sample(result, min(len(result), 10))
    
    # 파라미터
    parameters = [Sido, Gu, menu]

    logging.debug(f"파라미터 ========{parameters}")
    
    # 응답 생성
    cards = []
    for place in rand_place:
        poi_nm = place['POI_NM']
        lc_nm = place['LC_NM']
        info_2 = place['INFO_2']

        # 메뉴별이미지 출력
        if lc_nm == '한식':
            thumb = random.choice(kor_food_url)
        elif lc_nm == '일식':
            thumb = random.choice(ja_food_url)
        elif lc_nm == '양식':
            thumb = random.choice(west_food_url)
        elif lc_nm == '카페':
            thumb = random.choice(cafe_food_url)
        elif lc_nm == '바/술집':
            thumb = random.choice(bar_food_url)
        elif lc_nm == '기타':
            thumb = random.choice(else_food_url)
        elif lc_nm == '패스트푸드':
            thumb = random.choice(fast_food_url)
        elif lc_nm == '중식':
            thumb = random.choice(chi_food_url)
            
        logging.debug(poi_nm)
        
        description = (
            f"위치: {info_2}\n"
            f"메뉴: {lc_nm}\n"
            )

        card = {
            "title": poi_nm,
            "description": description,
            "thumbnail": {
                "imageUrl": thumb
            },
            "buttons": [
                    {
                        "action": "webLink",
                        "label": "검색",
                        "webLinkUrl": f"https://map.naver.com/p/search/{poi_nm}"
                    }
                ]
            }
        cards.append(card)

        response_body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                      "textCard": {
                          
                          "title": f"{menu}을 선택하셨군요!",
                          "description": "이런 곳은 어떤가요?"
                       }
                    },
                    {
                      "carousel": {
                          "type": "basicCard",
                          "items": cards
                       }
                    }
                ],
                "quickReplies": [
                    {
                        "messageText": menu,
                        "action": "message",
                        "label": "다른 맛집 추천받기"
                    },
                    {
                        "messageText": "숙소 추천",
                        "action": "message",
                        "label": "숙소 추천"
                    },
                    {
                        "messageText": "그만하기",
                        "action": "message",
                        "label": "이제 괜찮아요"
                    }
                ]
               }
        }

    return response_body

@app.route('/SaveData', methods=['POST'])
def save_data():
    global locationData
    global travelData
    global hotelData
    global restaurantData
    
    
    
            
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
