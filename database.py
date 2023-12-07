from datetime import datetime
import pyrebase
import json 

class DBhandler:
    def __init__(self ):
        with open('./authentication/firebase_auth.json') as f:
            config=json.load(f)
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()
        
    def insert_user(self, data, pw):
        user_info = {
            "id": data['id'],
            "pw": pw,
            "email": data['email']
        }
        if self.user_duplicate_check(str(data['id'])):
            self.db.child("user").child(data['id']).set(user_info)
            print(data)
            return True
        else:
            return False
        
    def user_duplicate_check(self, id_string):
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
        
    def find_user(self, id_, pw_):
        users = self.db.child("user").get()
        target_value = []
        for res in users.each():
            value = res.val()

            if value['id'] == id_ and value['pw'] == pw_:
                return True
        return False
    
    def get_user_by_id(self, user_id):
        user = self.db.child("user").child(user_id).get().val()
        return user

    def insert_item(self, name, data, img_path, seller_id, post_date, transaction):
        item_info ={
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
    
    def get_user_by_id(self, user_id):
        user = self.db.child("user").child(user_id).get().val()
        return user
    
    def get_items(self):
        items = self.db.child("item").get().val()
        return items
    
    def get_item_by_name(self, name):
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
            "buyer_id": buyer_id,
            "trans_mode" : trans_mode,  # 결제 정보 (직거래, 경매, 비대면 상자)
            "trans_media" : trans_media,  # 결제 수단 (카카오페이, 직거래, 카드, etc)
            "trans_date": formatted_date  # 추가: 구매하기를 누른 날짜
        }
        #Update item_status into "거래진행중"
        self.db.child("item").child(item_name).update({"item_status": "거래진행중"})

        # 각 상품에 대한 거래 정보를 저장할 때, 상품명을 키로 사용
        self.db.child("trans_info").child(item_name).set(buy_info)
        return True

    def get_trans_info(self, name):
        trans_info = self.db.child("trans_info").child(name).get().val()
        return trans_info
    
    def update_item_status(self, name, status):
        # Update item_status into the specified status ('거래완료', '판매중', 등)
        self.db.child("item").child(name).update({"item_status": status})
        return True

    def get_heart_byname(self, uid, name):
        hearts = self.db.child("heart").child(uid).get()
        target_value = ""
        if hearts.val() == None:
            return target_value
        for res in hearts.each():
            key_value = res.key()
            if key_value == name:
                target_value = res.val()
        return target_value
    
    def update_heart(self, user_id, isHeart, item):
        heart_info = {
            "interested" : isHeart
        }
        self.db.child("heart").child(user_id).child(item).set(heart_info)
        return True
    
    def get_liked_items(self, user_id):
        liked_items = []

        hearts = self.db.child("heart").child(user_id).get()
        if hearts.val() is not None:
            for res in hearts.each():
                key_value = res.key()
                if res.val().get("interested") == "Y":
                    liked_item_details = self.get_item_by_name(key_value)
                    liked_item = {
                        'name': key_value,
                        'details': liked_item_details
                    }
                    liked_items.append(liked_item)

        return liked_items




    def insert_seller_review(self, user_id, item_name, rating, review_content):
        review_info = {
            "rating": rating,
            "review_content": review_content
        }
        self.db.child("seller_reviews").child(item_name).child(user_id).set(review_info)
        return True

    def insert_buyer_review(self, user_id, item_name, rating, review_content):
        review_info = {
            "rating": rating,
            "review_content": review_content
        }
        self.db.child("buyer_reviews").child(item_name).child(user_id).set(review_info)
        return True
    
    def get_seller_reviews(self, name):
        seller_reviews = self.db.child("seller_reviews").child(name).get().val()
        return seller_reviews

    def get_buyer_reviews(self, name):
        buyer_reviews = self.db.child("buyer_reviews").child(name).get().val()
        return buyer_reviews

    def get_seller_reviews_by_user_id(self, user_id):
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
                    
                    review_info = {
                        'name': item_name,
                        'regular_price': item_info.get('regular_price'),
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

                    review_info = {
                        'name': item_name,
                        'regular_price': item_info.get('regular_price'),
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
    
    def get_ing_items(self, user_id, selected_trade):
        ing_items = []
        items = self.db.child("item").get().val()

        for item_name, item_info in items.items():
            trans_info = self.db.child("trans_info").child(item_name).get().val()

            if trans_info and (
                user_id == item_info.get('seller_id') or user_id == trans_info.get('buyer_id')
            ) and item_info.get('item_status') == '거래진행중' and (
                selected_trade is None or trans_info.get('trans_mode') == selected_trade
            ):
                ing_item = {
                    'name': item_name,
                    'img_path': item_info.get('img_path'),
                    'post_date': item_info.get('post_date'),
                    'trans_mode': trans_info.get('trans_mode'),
                }
                ing_items.append(ing_item)

        return ing_items
    

    def get_done_items(self, user_id, selected_trade):
        done_items = []
        items = self.db.child("item").get().val()

        for item_name, item_info in items.items():
            trans_info = self.db.child("trans_info").child(item_name).get().val()

            if trans_info and (
                user_id == item_info.get('seller_id') or user_id == trans_info.get('buyer_id')
            ) and item_info.get('item_status') == '거래완료' and (
                selected_trade is None or trans_info.get('trans_mode') == selected_trade
            ):
                done_item = {
                    'name': item_name,
                    'img_path': item_info.get('img_path'),
                    'post_date': item_info.get('post_date'),
                    'trans_mode': trans_info.get('trans_mode'),
                }
                done_items.append(done_item)

        return done_items  
          
