from datetime import datetime
import pyrebase
import json 

class DBhandler:
    def __init__(self ):
        with open('./authentication/firebase_auth.json') as f:
            config=json.load(f)
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()
        
    def insert_user(self, data, pw):                                        #사용자를 추가하는 함수
        user_info = {                                                       #user_info에 저장할 내용
            "id": data['id'],                                                   #사용자 id
            "pw": pw,                                                           #사용자 pw
            "email": data['email']                                              #사용자 이메일
        }
        if self.user_duplicate_check(str(data['id'])):                      # 추가하려는 아이디가 이미 존재하는 아이디일 경우 
            self.db.child("user").child(data['id']).set(user_info)
            print(data)
            return True
        else:                                                       
            return False
        
    def user_duplicate_check(self, id_string):                              #이미 존재하는 아이디인지 확인(아이디 중복체크)
        users = self.db.child("user").get()

        print("users###", users.val())
        if str(users.val()) == "None": #first registration
            return True
        else:
            for res in users.each():
                value = res.val()

                if value['id'] == id_string:
                    return False
            return True
        
    def find_user(self, id_, pw_):                                          #DB에서 등록되어있는 사용자인지 찾기
        users = self.db.child("user").get()
        target_value = []
        for res in users.each():
            value = res.val()

            if value['id'] == id_ and value['pw'] == pw_:
                return True
        return False

    # 상품 결제할 때 db에 등록
    def insert_item(self, name, data, img_path, seller_id, post_date, transaction):
        item_info ={
            "item_name" : name,
            "product_description": data['product_description'],
            "img_path": img_path,
            "price": data['price'],
            "seller_id": seller_id,
            "post_date": post_date,
            "transaction": transaction,
            "item_status": "available"                      #setting the initial status into 'avilable'
        }
        self.db.child("item").child(name).set(item_info)
        return True
    
    def get_user_by_id(self, user_id):                                          #아이디를 통해서 사용자 찾기
        user = self.db.child("user").child(user_id).get().val()
        return user

    # item 네임으로 db 받아오기
    def get_items(self):
        items = self.db.child("item").get().val()
        return items

    # 아이템 리스템에 필요한 정보 저장 후 넘겨주기 => 상품전체조회페이지에서 사용
    def get_items_to_list(self):
        all_items = self.db.child("item").get().val()
        items = []
        
        for item_name, item_info in all_items.items():
            new_items_info = {
                'name': item_name,
                'post_date': item_info.get('post_date'),
                'trans_mode': item_info.get('transaction'),
                'img_path': item_info.get('img_path'),
                'price': item_info.get('price'),
                'item_status': item_info.get('item_status')
            }
            items.append(new_items_info)

        return items
    
    def get_available_items(self):                                              #상품상태가 'available' 인 상품들 딕셔너리 형태로 받아오기
        items = self.db.child("item").get().val()
        available_items = {key: value for key, value in items.items() if value.get('item_status') == 'available'}
        return available_items
    
    def get_item_by_name(self, name):                                           #아이템 정보를 상품이름을 통해서 받아오기
        items = self.db.child("item").get()
        target_value=""
        print("###########",name)
        for res in items.each():
            key_value = res.key()
            if key_value == name:
                target_value=res.val()
        return target_value
    
    def get_items_bycategory(self, cate):
        items = self.db.child("item").get()
        target_value=[]
        target_key=[]
        for res in items.each():
            value = res.val()
            key_value = res.key()
            if value['item_status'] == cate:
                target_value.append(value)
                target_key.append(key_value)
        print("######target_value",target_value)
        new_dict={}
        for k,v in zip(target_key,target_value):
            new_dict[k]=v
        return new_dict
        
    def reg_buy(self, buyer_id, trans_mode, trans_media, item_name):
        #get current date
        current_date = datetime.now().date()
        # Format the date as a string
        formatted_date = current_date.isoformat()

        buy_info = {
            "buyer_id": buyer_id,       #구매자 아이디
            "trans_mode" : trans_mode,  # 결제 정보 (직거래, 경매, 비대면 상자)
            "trans_media" : trans_media,  # 결제 수단 (카카오페이, 직거래, 카드, etc)
            "trans_date": formatted_date  # 추가: 구매하기를 누른 날짜
        }
        #Update item_status into "거래진행중"
        self.db.child("item").child(item_name).update({"item_status": "거래진행중"})
        # 결제일 추가
        self.db.child("item").child(item_name).child("trans_date").set(formatted_date)

        # 각 상품에 대한 거래 정보를 저장할 때, 상품명을 키로 사용
        self.db.child("trans_info").child(item_name).set(buy_info)
        return True

    def get_trans_info(self, name):                                             #상품이름을 통해서 거래방식 가져오기
        trans_info = self.db.child("trans_info").child(name).get().val()
        return trans_info
    
    def update_item_status(self, name, status):
        # Update item_status into the specified status ('거래완료', '판매중', 등)
        self.db.child("item").child(name).update({"item_status": status})
        return True

    def get_heart_byname(self, uid, name):
        hearts = self.db.child("heart").child(uid).get()    # 사용자의 UID 및 항목 이름(name)을 기반으로 데이터베이스에서 관련 'heart' 정보를 가져옴
        target_value = ""
        if hearts.val() == None:    # 'heart' 정보가 없으면 빈 문자열을 반환함
            return target_value
        for res in hearts.each():   # 모든 'heart' 정보를 반복하면서 주어진 이름(name)에 해당하는 값을 찾음
            key_value = res.key()
            if key_value == name:
                target_value = res.val()
        return target_value     # 찾은 값을 반환

    def update_heart(self, user_id, isHeart, item):
        heart_info = {      # 사용자 ID, 관심 여부(isHeart), 항목(item)을 기반으로 'heart' 정보를 업데이트
            "interested": isHeart
        }
        self.db.child("heart").child(user_id).child(item).set(heart_info)
        return True     # 업데이트 성공을 나타내기 위해 True를 반환

    def get_liked_items(self, user_id):
        liked_items = []        # 사용자 ID를 기반으로 좋아하는 항목들의 세부 정보를 가져오는 함수
        hearts = self.db.child("heart").child(user_id).get()    # 사용자의 'heart' 정보를 가져옴
        if hearts.val() is not None:        # 'heart' 정보가 있을 경우 해당 정보를 반복하면서 좋아하는 항목을 찾음
            for res in hearts.each():
                key_value = res.key()
                if res.val().get("interested") == "Y":      # 'interested' 값이 'Y'인 경우 해당 항목을 세부 정보와 함께 저장
                    liked_item_details = self.get_item_by_name(key_value)
                    liked_item = {
                        'name': key_value,
                        'details': liked_item_details
                    }
                    liked_items.append(liked_item)
        return liked_items      # 좋아하는 항목들의 리스트를 반환



    def get_ing_items_by_user_id(self, user_id):
        # 모든 거래 및 상품 정보를 가져옴
        all_transactions = self.db.child("trans_info").get().val()
        all_items = self.db.child("item").get().val()

        # 거래 진행 중인 상품 정보를 저장할 리스트 초기화
        ing_items = []

        # 모든 상품에 대해 반복
        for item_name, item_info in all_items.items():
            # 상품의 거래 정보를 가져옴
            trans_info = all_transactions.get(item_name, {})
            buyer_id = trans_info.get('buyer_id')

            # 판매자이거나 구매자이며 거래 상태가 '거래진행중'인 경우
            if item_info['seller_id'] == user_id or (buyer_id and buyer_id == user_id and item_info['item_status'] == '거래진행중'):
                if item_info['item_status'] == '거래진행중':
                    # 거래 진행 중인 상품 정보를 딕셔너리로 생성하여 리스트에 추가
                    ing_items_info = {
                        'name': item_name,
                        'trans_date': trans_info.get('trans_date'),
                        'trans_mode': trans_info.get('trans_mode'),
                        'img_path': item_info.get('img_path'),
                        'price': item_info.get('price')
                    }
                    ing_items.append(ing_items_info)

        # 최종적으로 거래 진행 중인 상품 정보 리스트를 반환
        return ing_items



    def insert_seller_review(self, user_id, item_name, rating, review_content):
        # 판매자 리뷰 정보 생성
        review_info = {
            "rating": rating,
            "review_content": review_content
        }

        # 판매자 리뷰를 데이터베이스에 추가
        self.db.child("seller_reviews").child(item_name).child(user_id).set(review_info)
        return True

    def insert_buyer_review(self, user_id, item_name, rating, review_content):
        # 구매자 리뷰 정보 생성
        review_info = {
            "rating": rating,
            "review_content": review_content
        }

        # 구매자 리뷰를 데이터베이스에 추가
        self.db.child("buyer_reviews").child(item_name).child(user_id).set(review_info)
        return True
    
    def get_seller_reviews(self, name):
        # 판매자 리뷰를 이름을 통해 가져옴
        seller_reviews = self.db.child("seller_reviews").child(name).get().val()
        return seller_reviews

    def get_buyer_reviews(self, name):
        # 구매자 리뷰를 이름을 통해 가져옴
        buyer_reviews = self.db.child("buyer_reviews").child(name).get().val()
        return buyer_reviews

    def get_seller_reviews_by_user_id(self, user_id):
        # 판매자로서의 사용자 ID에 대한 리뷰 정보를 가져옴
        seller_reviews = self.db.child("seller_reviews").get().val()

        if seller_reviews is not None:
            user_reviews = []
            for item_name, reviews in seller_reviews.items():
                item_info = self.get_item_by_name(item_name)
                trans_info = self.get_trans_info(item_name)
                
                if user_id in reviews:
                    if user_id == item_info.get('seller_id'):
                        trader_id = trans_info.get('buyer_id')
                        role = 'seller'
                    else:
                        trader_id = item_info.get('seller_id')
                        role = 'buyer'
                    
                    # 사용자 리뷰 정보를 생성하여 리스트에 추가
                    review_info = {
                        'name': item_name,
                        'price': item_info.get('price'),
                        'img_path' : item_info.get('img_path'),
                        'seller_id': item_info.get('seller_id'),
                        'trader_id': trader_id,
                        'role': role,
                        **reviews[user_id]
                    }
                    user_reviews.append(review_info)

        else:
            user_reviews = []

        return user_reviews

    def get_buyer_reviews_by_user_id(self, user_id):
        # 구매자로서의 사용자 ID에 대한 리뷰 정보를 가져옴
        buyer_reviews = self.db.child("buyer_reviews").get().val()

        if buyer_reviews is not None:
            user_reviews = []
            for item_name, reviews in buyer_reviews.items():
                item_info = self.get_item_by_name(item_name)
                trans_info = self.get_trans_info(item_name)

                if user_id in reviews:
                    if user_id == item_info.get('seller_id'):
                        trader_id = trans_info.get('buyer_id')
                        role = 'seller'
                    else:
                        trader_id = item_info.get('seller_id')
                        role = 'buyer'

                    # 사용자 리뷰 정보를 생성하여 리스트에 추가
                    review_info = {
                        'name': item_name,
                        'price': item_info.get('price'),
                        'img_path' : item_info.get('img_path'),
                        'seller_id': item_info.get('seller_id'),
                        'trader_id': trader_id,
                        'role': role,
                        'buyer_id': trans_info.get('buyer_id'),
                        **reviews[user_id]
                    }
                    user_reviews.append(review_info)

        else:
            user_reviews = []

        return user_reviews
    
    def get_ing_items_by_user_id(self, user_id):
        # 거래 진행 중인 상품 정보를 가져옴
        all_transactions = self.db.child("trans_info").get().val()
        all_items = self.db.child("item").get().val()

        ing_items = []

        for item_name, item_info in all_items.items():
            trans_info = all_transactions.get(item_name, {})
            buyer_id = trans_info.get('buyer_id')

            # 판매자이거나 구매자이며 거래 상태가 '거래진행중'인 경우
            if item_info['seller_id'] == user_id or (buyer_id and buyer_id == user_id and item_info['item_status'] == '거래진행중'):
                if item_info['item_status'] == '거래진행중':
                    # 거래 진행 중인 상품 정보를 리스트에 추가
                    ing_items_info = {
                        'name': item_name,
                        'trans_date': trans_info.get('trans_date'),
                        'trans_mode': trans_info.get('trans_mode'),
                        'img_path': item_info.get('img_path'),
                        'price': item_info.get('price')
                    }
                    ing_items.append(ing_items_info)

        return ing_items
    
    def get_done_items_by_user_id(self, user_id):
        # 거래 완료된 상품 정보를 가져옴
        all_transactions = self.db.child("trans_info").get().val()
        all_items = self.db.child("item").get().val()

        done_items = []

        for item_name, item_info in all_items.items():
            trans_info = all_transactions.get(item_name, {})
            buyer_id = trans_info.get('buyer_id')

            # 판매자이거나 구매자이며 거래 상태가 '거래완료'인 경우
            if item_info['seller_id'] == user_id or (buyer_id and buyer_id == user_id and item_info['item_status'] == '거래완료'):
                if item_info['item_status'] == '거래완료':
                    # 거래 완료된 상품 정보를 리스트에 추가
                    done_items_info = {
                        'name': item_name,
                        'trans_date': trans_info.get('trans_date'),
                        'trans_mode': trans_info.get('trans_mode'),
                        'img_path': item_info.get('img_path'),
                        'price': item_info.get('price')
                    }
                    done_items.append(done_items_info)

        return done_items

    
    def submit_comment(self, comment, item):
        if type(comment) == str:        # 입력된 comment가 문자열인 경우에도 리스트로 변환하여 처리함
            comment = [comment]
        comment_info = {    # comment 정보를 딕셔너리로 준비
            "comment": comment
        }
        self.db.child("comment_info").child(item).push(comment_info)    # 데이터베이스의 "comment_info" 노드 하위에 지정된 항목(item)에 comment 정보를 추가함        
        return True     # 성공적인 comment 제출을 나타내기 위해 True를 반환

    def get_comments(self, item):
        comments = self.db.child("comment_info").child(item).get().val()    # 데이터베이스에서 지정된 항목(item) 하위의 "comment_info" 노드에서 comment를 검색함
        return [value for value in comments.values()] if comments else []   # comment가 존재하면 해당 값을 리스트로 반환하고, 그렇지 않으면 빈 리스트를 반환함

    def submit_comment_purchased(self, comment, item):
        comment_info_purchased = {      # 구매된 comment 정보를 딕셔너리로 준비
            "comment": comment
        }        
        self.db.child("comment_info_purchased").child(item).push(comment_info_purchased)    # 데이터베이스의 "comment_info_purchased" 노드 하위에 지정된 항목(item)에 구매된 comment 정보를 추가함        
        return True     # 성공적인 구매된 comment 제출을 나타내기 위해 True를 반환함


    def count_sold_and_bought_items(self, user_id):
        # 데이터베이스에서 모든 거래와 상품 정보를 가져옴.
        all_transactions = self.db.child("trans_info").get().val()
        all_items = self.db.child("item").get().val()

        # 거래 정보가 없으면 빈 딕셔너리로 초기화함.
        if all_transactions is None:
            all_transactions = {}

        # 판매 및 구매 횟수 초기화
        sold_count = 0
        bought_count = 0

        # 모든 상품에 대해 반복
        for item_name, item_info in all_items.items():
            # 상품의 판매자 ID 및 해당 상품의 거래 정보 가져옴
            seller_id = item_info.get('seller_id')
            trans_info = all_transactions.get(item_name, {})
            buyer_id = trans_info.get('buyer_id')

            # 판매자가 주어진 사용자이고 거래 상태가 '거래완료'인 경우 sold_count 증가
            if seller_id == user_id and item_info['item_status'] == '거래완료':
                sold_count += 1
            # 구매자가 주어진 사용자이고 거래 상태가 '거래완료'인 경우 bought_count 증가
            elif buyer_id == user_id and item_info['item_status'] == '거래완료':
                bought_count += 1

        # 최종적으로 판매 및 구매 횟수 반환
        return sold_count, bought_count