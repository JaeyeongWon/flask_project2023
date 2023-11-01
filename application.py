from flask import Flask, render_template, request

application = Flask(__name__)

@application.route("/", methods=['GET', 'POST'])
def hello():
    return render_template("home.html")

@application.route("/productList")
def productList():
    return render_template("productList.html")

@application.route("/productRegister")
def productRegister():
    return render_template("productRegister.html")

@application.route("/submit", methods=['POST'])
def submitProduct():
    if request.method == "POST":
        product_title = request.form.get("product-title")
        price_method = request.form.get("price-method")
        product_description = request.form.get("product-description")
        user_id = request.form.get("user-id")
        post_date = request.form.get("post-date")

        if price_method == "일반거래":
            normal_price = request.form.get("normal-price")
        elif price_method == "경매":
            auction_end_time = request.form.get("auction-end-time")
            auction_min_bid = request.form.get("auction-min-bid")
            auction_max_bid = request.form.get("auction-max-bid")

        #터미널에 데이터값 출력
        print("상품명(글제목):", product_title)
        print("가격방식:", price_method)

        if price_method == "일반거래":
            print("판매가:", normal_price)
        elif price_method == "경매":
            print("경매마감일:", auction_end_time)
            print("최저낙찰가:", auction_min_bid)
            print("최고낙찰가:", auction_max_bid)
        
        print("상세설명:", product_description)
        print("글작성날짜:", post_date)

    return "상품이 성공적으로 등록되었습니다."



@application.route("/reviewRegister")
def reviewRegister():
    return render_template("reviewRegister.html")

@application.route("/myReview")
def myReview():
    return render_template("myReview.html")

@application.route("/productSubmitResult", methods=['POST'])
def productSubmitResult():
    data = request.form
    return render_template("productSubmitResult.html", data=data)

if __name__ == "__main__":
    application.run(host='0.0.0.0')
