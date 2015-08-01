/**
 *@author: imeron
 *@date: 2015-07-22 
 */
//字符串模板
String.prototype.template = function(data) {
	var str = this;
	if(data && data.sort){
		for(var i=0; i<data.length; i++) {
			str = str.replace(new RegExp("{\\{"+i+"}}", "gm"), data[i]);
		}
		return str;
	}
	
	var placeholder = str.match(new RegExp("{{.+?}}", 'ig'));
	if (data && placeholder) {
		for ( var i = 0; i < placeholder.length; i++) {
			var key = placeholder[i];
			var value = proxy.call(data, key.replace(new RegExp("[{,}]", "gm"), ""));
			key = key.replace(new RegExp("\\\.", "gm"), "\\.").replace("{{","{\\{");
			if (value == null)
				value = "&nbsp;";
			str = str.replace(new RegExp(key, "gm"), value);
		}
	}
	return str;
	
	function proxy(key) {
		try {
			return eval('this.' + key);
		} catch (e) {
			return "";
		}
	}
};

function parseUrlParams(myUrl){
    var vars = [], hash;
    var hashes = window.location.href.slice(myUrl.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
      hash = hashes[i].split('=');
      vars.push(hash[0]);
      vars[hash[0]] = hash[1];
    }
    return vars;
}

//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}

//设置初始页面VIEWPORT
(function () {
    var oViewport = document.getElementById('viewport');
    var phoneWidth = parseInt(window.screen.width);
    var phoneScale = phoneWidth / 640;
    var ua = navigator.userAgent;
    if (/Android (\d+\.\d+)/.test(ua)) {
        var version = parseFloat(RegExp.$1);
        if (version > 2.3) {
            oViewport.setAttribute('content', 'width=640, minimum-scale = ' + phoneScale + ', maximum-scale = ' + phoneScale + ', target-densitydpi=device-dpi')
        } else {
            oViewport.setAttribute('content', 'width=640, target-densitydpi=device-dpi');
        }
    } else {
        oViewport.setAttribute('content', 'width=640, user-scalable=no, target-densitydpi=device-dpi');
	}
    window.onload = function () {
        document.body.addEventListener('touchstart', function () {
        });
    }
})();

//全局配置
var GLConfig = {
	baseApiUrl:'/rest/v1', //API接口调用前缀
	order_expired_in:20 * 60,//expired time
	today_suffix:'today',  //获取首页今日商品信息，URL标识
    previous_suffix:'previous', //获取首页昨日商品信息，URL标识
    get_childlist_url:'/products/childlist.json', //获取潮流童装商品列表
    get_ladylist_url:'/products/ladylist.json', //获取时尚女装商品列表
    get_modellist_url:'/products/modellist/{{model_id}}.json', //获取同款商品列表
    get_product_detail_url:'/products/{{product_id}}/details.json', //获取商品明细
    get_trade_all_url:'/trades.json', //获取用户所有订单
    get_trade_waitpay_url:'/trades/waitpay.json', //获取用户待付款订单
    get_trade_waitsend_url:'/trades/waitsend.json', //获取用户待发货订单
    get_trade_details_url:'/trades/{{trade_id}}/orders/details.json', //获取订单明细
    get_cart_url:'/carts.json', //获取购物车详细
    get_num_cart:'/carts/show_carts_num?format=json', //获取购物车数量
    get_all_address:'/address/show_address/?format=json',//获取个人用户地址列表
    delete_address:'/address/delete_address/?format=json',//删除地址
    change_default:'/address/change_default/?format=json',//更改默认地址
    province_list:'/districts/province_list/?format=json',//省份列表
    city_list:'/districts/city_list/?format=json',//城市列表
    country_list:'/districts/country_list/?format=json',//区/县列表
    create_address:'/address/create_address/?format=json',//创建新的收获地址
};

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');


/*
 * 模拟toast
 * auther:yann
 * date:2015/30/7
 */
var intervalCounter = 0;
function hideToast() {
    var alert = document.getElementById("toast");
    alert.style.opacity = 0;
    clearInterval(intervalCounter);
}
function drawToast(message) {
    var alert = document.getElementById("toast");
    if (alert == null) {
        var toastHTML = '<div id="toast">' + message + '</div>';
        document.body.insertAdjacentHTML('beforeEnd', toastHTML);
    }
    else {
        alert.style.opacity = .9;
    }
    console.log('debug toast:',alert);
    intervalCounter = setInterval("hideToast()", 1000);
}


function Set_shopcarts_num() {
    /*
    * 得到购物车数量
    * auther:yann
    * date:2015/30/7
    */
    var requestUrl = GLConfig.baseApiUrl + GLConfig.get_num_cart;
    var requestCallBack = function (res) {
        $(".total").html(res);
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: "",
        beforeSend: function () {

        },
        success: requestCallBack,
        error: function (data) {
            if (data.statusText == "FORBIDDEN") {
                $(".total").html("0");
            }
            console.info("debug error: " + data.statusText);
        }
    });
}
