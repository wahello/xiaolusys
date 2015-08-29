/**
 * Created by jishu_linjie on 8/17/15.
 */

function get_Coupon_On_Buy() {
    var url = GLConfig.baseApiUrl + GLConfig.user_own_coupon;
    console.log('debug:', url);
    $.get(url, function (res) {
        if (res.length > 0) {
            var nums = 0;
            $.each(res, function (i, val) {
                nums = nums + 1;//有效可用的优惠券数量
            });
            Coupon_Nums_Show(nums);//显示优惠券数量
        }
        else if (res.length == 0) {
            Coupon_Nums_Show(0);//显示优惠券数量
        }
    });
}

function Coupon_Nums_Show(nums) {
    console.log('nums nums ', nums);
    $("#coupon_nums").text("可用优惠券（" + nums + "）");
    if (nums > 0) {
        $("#coupon_nums").click(function () {
            var total_money = ($("#total_money").html().split(">")[2]);
            location.href = "./choose-coupon.html?price=" + total_money;
        });
    }
}

function get_Coupon_On_Choose() {
    var url = GLConfig.baseApiUrl + GLConfig.user_own_coupon;
    $.get(url, function (res) {
        if (res.length > 0) {
            var nums = 0;
            $.each(res, function (i, val) {
                if (val.coupon_status == 0) {
                    nums = nums + 1;//有效可用的优惠券数量
                    var id = val.id;
                    var coupon_status = val.coupon_status;
                    var coupon_type = val.coupon_type;
                    var coupon_value = val.coupon_value;
                    var deadline = val.deadline.split(' ')[0];
                    var created = val.created;
                    var yhq_obj = {
                        "id": id,
                        "created": created,
                        "deadline": deadline,
                        "coupon_value": coupon_value
                    };

                    if (coupon_value == 30 && coupon_status == 0 && coupon_type == 4) {
                        //满30返30　　代理审核生成的优惠券
                        var yhq_tree3 = Create_xlmm_coupon_dom(yhq_obj);
                        $('.coupons').append(yhq_tree3);
                    }
                    if (coupon_value == 30 && coupon_status == 1 && coupon_type == 4) {
                        //满30返30　　代理审核生成的优惠券
                        var yhq_tree4 = Create_coupon_used_xlmm_dom(yhq_obj);
                        $('.coupons').append(yhq_tree4);
                    }

                    if (nums == 0) {
                        pop_info();
                    }
                }
            });
        }
        else {
            // 显示提示信息　没有优惠券
            pop_info();
        }
    });
}

function Create_xlmm_coupon_dom(obj) {
    var html = $("#coupon_template_xlmm").html();
    return hereDoc(html).template(obj)
}
function Create_coupon_used_xlmm_dom(obj){
    var html = $("#coupon_template_xlmm_used").html();
    return hereDoc(html).template(obj)
}

function choose_Coupon(coupon_id) {
    var price = parseFloat(getUrlParam('price'));
    if (price >= 30) {

        swal({
                title: "",
                text: '确定选择这张优惠券吗？',
                type: "",
                showCancelButton: true,
                imageUrl: "http://image.xiaolu.so/logo.png",
                confirmButtonColor: '#DD6B55',
                confirmButtonText: "确定",
                cancelButtonText: "取消"
            },
            function () {//确定　则跳转
                console.log(document.referrer);
                var buy_nuw_url = document.referrer.split("&")[0] + "&" + document.referrer.split("&")[1];
                var include_coupon = buy_nuw_url + "&coupon_id=" + coupon_id;
                location.href = include_coupon;
            });
    }
    else {
        drawToast("商品价格不足优惠券使用金额哦~");
    }
}



function getUrlParam(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
    var r = window.location.search.substr(1).match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return null; //返回参数值
}

function pop_info() {
    // 显示提示信息　没有优惠券
    swal({
            title: "",
            text: '您暂时还没有优惠券哦~',
            type: "",
            showCancelButton: false,
            imageUrl: "http://image.xiaolu.so/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: "返回",
            cancelButtonText: "取消"
        },
        function () {//确定　则跳转
            location.href = document.referrer;
        });
}