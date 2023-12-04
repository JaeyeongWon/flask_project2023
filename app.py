from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from database import DBhandler
import hashlib
import sys
from datetime import datetime

application = Flask(__name__)
application.config["SECRET_KEY"] = "helloosp"
DB = DBhandler()

@application.route("/", methods=['GET', 'POST'])
def hello():
    return render_template("home.html")

@application.route('/login')
def login():
    return render_template("login.html")

@application.route("/login_confirm", methods=['POST'])
def login_user():
    id_=request.form['id']
    pw=request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    if DB.find_user(id_,pw_hash):
        session['id']=id_
        return render_template('home.html')                #이부분 나중에 view_list로 수정필요
    else:
        flash("Wrong ID or PW!")
        return render_template("login.html")
def find_user(self, id_, pw_):
    users = self.db.child("user").get()
    target_value=[]
    for res in users.each():
        value = res.val()

        if value['id'] == id_ and value['pw'] == pw_:
            return True
    return False

@application.route("/logout")
def logout_user():
    session.clear()
    return render_template('home.html')                    #이부분 나중에 view_list로 수정필요

@application.route("/signup")
def signUp():
    return render_template("signUp.html")

@application.route("/signup_post", methods=['POST'])
def register_user():
    data=request.form
    pw=data.get('pw')
    print("Password:", pw)
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    if DB.insert_user(data, pw_hash):
        return render_template("login.html")
    else:
        flash("user id already exist!")
        return render_template("signUp.html")

@application.route('/myPage')
def myPage():
    user_id = session.get('id')
    user = DB.get_user_by_id(user_id)  # DB에서 사용자 정보를 가져오는 함수
    
    if user:
        # 해당 사용자의 리뷰 정보 가져오기
        buyer_reviews = DB.get_buyer_reviews_by_user_id(user_id)
        
        # 리뷰 정보에서 평점만 추출하여 숫자로 변환하여 리스트로 저장
        ratings = [float(review['rating']) for review in buyer_reviews if 'rating' in review]
        
        # 리뷰가 있는 경우에만 평균 계산
        average_rating = sum(ratings) / len(ratings) if ratings else 0
    else:
        average_rating = 0

    return render_template('myPage.html', average_rating=average_rating, session=session)


@application.route("/productList")
def productList():
    return render_template("productList.html")

@application.route('/reg_items')
def reg_items():
    post_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seller_id = session.get('id') 
    return render_template('reg_items.html', seller_id=seller_id, post_date=post_date)

@application.route("/submit_item_post", methods=['POST'])
def reg_item_submit_post():
    post_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if 'id' in session:
        seller_id = session['id']
    else:
        flash("로그인 해야 이용 가능한 기능입니다!")
        return redirect(url_for('login'))    
    
    image_file = request.files["file"]
    image_file.save("static/img/{}".format(image_file.filename))
    data = request.form.to_dict()
    trade_type = data.get('trade_type')

    if trade_type == 'auction':
        end_date = data.get('end_date')
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        data['regular_price'] = None
    else:
        regular_price = data.get('regular_price')
        data['end_date'] = None
        data['min_price'] = None
        data['max_price'] = None

    # 'transaction' 필드를 항상 리스트로 처리
    data['transaction'] = request.form.getlist('transaction')

    data['trade_type'] = trade_type
    data['post_date'] = post_date
    data['seller_id'] = seller_id
    
    DB.insert_item(data['name'], data, image_file.filename, data['trade_type'], data['end_date'], data['min_price'], data['max_price'], seller_id, post_date, data['transaction'])
    return render_template("productSubmitResult.html", data=data, img_path="static/img/{}".format(image_file.filename), transaction_list=data['transaction'])

@application.route("/list")
def view_list():
    page = request.args.get("page", 0, type=int)
    per_page=6
    per_row=3
    row_count=int(per_page/per_row)
    start_idx=per_page*page
    end_idx=per_page*(page+1)
    data = DB.get_items()
    item_counts = len(data)
    data = dict(list(data.items())[start_idx:end_idx])
    tot_count = len(data)
    for i in range(row_count):
        if (i == row_count-1) and (tot_count%per_row != 0):
            locals()['data_{}'.format(i)] = dict(list(data.items())[i*per_row:])
        else: 
            locals()['data_{}'.format(i)] = dict(list(data.items())[i*per_row:(i+1)*per_row])
    return render_template("all_items.html", datas=data.items(), row1=locals()['data_0'].items(), row2=locals()['data_1'].items(), limit=per_page, page=page, page_count=int((item_counts/per_page)+1), total=item_counts)

@application.route("/view_detail/<name>/")
def view_item_detail(name):
    data = DB.get_item_by_name(str(name))
    if data['trade_type'] == 'regular':
        return render_template("detail_general.html", name=name, data=data, transaction_list=data['transaction'])
    else:
        return render_template("detail_auction.html", name=name, data=data, transaction_list=data['transaction'])

# 상품 결제 페이지로 넘어감 -> 해결!
@application.route("/purchase_item/<name>/")
def purchase_item(name):
    data=DB.get_item_by_name(str(name))
    return render_template("purchasePage.html", name=name, data=data, transaction_list=data['transaction'])


# '결제하기' 버튼 누르면 결제 정보가 DB로 넘어가고 '거래진행중' 버튼 보이는 detail_purchased 페이지로 넘어감 -- 이게 안됨ㅠ
@application.route('/reg_buy/<string:name>', methods=['POST'])
def reg_buy(name):
    buyer_id = session.get('id') 
        
    trans_mode = request.form['transMode']
    trans_media = request.form['transMedia']

    data = DB.get_item_by_name(name)  

    DB.reg_buy(buyer_id, trans_mode, trans_media, name)

    # 구매 완료 페이지로 이동
    return render_template("detail_purchased.html", name=name, data=data)


@application.route("/detail_purchased/<name>/")
def detail_purchased(name):
    data=DB.get_item_by_name(str(name))
    return render_template("detail_purchased.html", name=name, data=data)



@application.route("/complete_transaction/<name>/", methods=['POST'])
def complete_transaction(name):
    # 상품의 거래 상태를 '거래완료'로 변경
    DB.update_item_status(name, '거래완료')
    return redirect(url_for('review_detail', name=name))



@application.route("/show_heart/<name>/", methods=['GET'])
def show_heart(name):
    my_heart = DB.get_heart_byname(session['id'], name)
    return jsonify({'my_heart': my_heart})

@application.route("/like/<name>/", methods=['POST'])
def like(name):
    my_heart = DB.update_heart(session['id'], 'Y', name)
    return jsonify({'msg': '좋아요 완료!'})

@application.route("/unlike/<name>/", methods=['POST'])
def unlike(name):
    my_heart = DB.update_heart(session['id'], 'N', name)
    return jsonify({'msg': '좋아요 취소 완료!'})


@application.route("/myLikes")
def my_likes():
    if 'id' not in session:
        flash("로그인이 필요한 서비스입니다.")
        return redirect(url_for('login'))

    user_id = session['id']
    liked_items = DB.get_liked_items(user_id)
    
    return render_template("myLikes.html", liked_items=liked_items)



@application.route("/submit_review", methods=['POST'])
def submit_review():
    if 'id' not in session:
        flash("로그인이 필요한 서비스입니다.")
        return redirect(url_for('login'))

    user_id = session['id']
    item_name = request.args.get('name')
    role = request.args.get('role')

    rating = request.form.get('rating')
    review_content = request.form.get('review')

    if role == 'seller':
        DB.insert_seller_review(user_id, item_name, rating, review_content)
    else:
        DB.insert_buyer_review(user_id, item_name, rating, review_content)

    flash("리뷰가 성공적으로 등록되었습니다.")
    return redirect(url_for('view_list'))

@application.route("/reviewDetail/<name>/")
def review_detail(name):
    item_data = DB.get_item_by_name(name)
    trans_info_data = DB.get_trans_info(name)
    seller_review = DB.get_seller_reviews(name)
    buyer_review = DB.get_buyer_reviews(name)

    user_id = session.get('id') 

    if user_id == item_data['seller_id']:
        trader_id = trans_info_data['buyer_id']
        role = 'seller'
    else:
        trader_id = item_data['seller_id']
        role = 'buyer'

    return render_template("reviewDetail.html", trader_id=trader_id, seller_id=item_data['seller_id'], buyer_id=trans_info_data['buyer_id'], img_path=item_data['img_path'], name=name, regular_price=item_data['regular_price'], user_id=user_id, seller_reviews=seller_review, buyer_reviews=buyer_review)

@application.route("/reviewRegister/<name>")
def review_register(name):
    item_data = DB.get_item_by_name(name)
    trans_info_data = DB.get_trans_info(name)
    
    user_id = session.get('id') 

    if user_id == item_data['seller_id']:
        trader_id = trans_info_data['buyer_id']
        role = 'seller'
    else:
        trader_id = item_data['seller_id']
        role = 'buyer'

    return render_template("reviewRegister.html", name=name, trader_id=trader_id, seller_id=item_data['seller_id'], buyer_id=trans_info_data['buyer_id'], img_path=item_data['img_path'], regular_price=item_data['regular_price'], user_id=user_id)

@application.route("/myReview/<user_id>")
def my_review(user_id):
    if 'id' not in session:
        flash("로그인이 필요한 서비스입니다.")
        return redirect(url_for('login'))

    seller_reviews = DB.get_seller_reviews_by_user_id(user_id)
    buyer_reviews = DB.get_buyer_reviews_by_user_id(user_id)
    user_reviews = seller_reviews + buyer_reviews

    page = request.args.get("page", 0, type=int)
    per_page = 3

    start_idx = per_page * page
    end_idx = per_page * (page + 1)

    data = user_reviews[start_idx:end_idx]
    tot_count = len(user_reviews)

    return render_template(
        "myReview.html",
        datas=data,
        limit=per_page,
        page=page,
        page_count=int((tot_count / per_page) + 1),
        total=tot_count,
        user_id=user_id 
    )

@application.route('/myPageIng')
def myPageIng():

    return render_template('myPageIng.html')

@application.route('/update_data', methods=['POST'])
def update_data():
    data = request.get_json()

    user_id = session.get('id')
    selected_trade = data.get('selected_trade')
    
    # DBhandler 클래스의 인스턴스 생성
    db_handler = DBhandler()
    ing_items = db_handler.get_ing_items(user_id, selected_trade)

    return jsonify({'ing_items': ing_items})

@application.route('/myPageDone')
def myPageDone():
    return render_template('myPageDone.html')

@application.route('/update_data2', methods=['POST'])
def update_data2():
    data = request.get_json()

    user_id = session.get('id')
    selected_trade = data.get('selected_trade')

    # DBhandler 클래스의 인스턴스 생성
    db_handler = DBhandler()
    done_items = db_handler.get_done_items(user_id, selected_trade)

    return jsonify({'done_items': done_items})

if __name__ == "__main__":
    application.run(debug=True)