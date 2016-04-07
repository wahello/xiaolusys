$(document).ready(function() {
	//请求数据
	var requestData = function() {
		$.ajax({
			type: '',
			url: '',
			success: function() {},
			error:function() {}
		});
	};
	// requestData();
	//倒计时
	var timer = function(intDiff) {
		window.setInterval(function() {
			var day = 0,
				hour = 0,
				minute = 0,
				second = 0;

			//时间默认值		
			if (intDiff > 0) {
				day = Math.floor(intDiff / (60 * 60 * 24));
				hour = Math.floor(intDiff / (60 * 60)) - (day * 24);
				minute = Math.floor(intDiff / 60) - (day * 24 * 60) - (hour * 60);
				second = Math.floor(intDiff) - (day * 24 * 60 * 60) - (hour * 60 * 60) - (minute * 60);
			}
			if (minute <= 9) minute = '0' + minute;
			if (second <= 9) second = '0' + second;
			$('#day_show').html(day);
			$('#hour_show').html('<s id="h"></s>' + hour);
			$('#minute_show').html('<s></s>' + minute);
			$('#second_show').html('<s></s>' + second);
			intDiff--;
		}, 1000);
	};
	var requestData = function() {
		var end_time,current_time,rest_time;
		$.ajax({
				type: 'GET',
				url: 'http://192.168.1.80:8000/sale/promotion/apply/3/',
				success: function(res) {
					//set rest time of activity
					end_time = (new Date(res.end_time)).getTime();
					current_time = (new Date()).getTime();
					rest_time = parseInt((end_time - current_time)/1000);
					console.log('end_time:'+end_time);
					console.log('current_time:'+current_time);
					timer(rest_time);
				}
			});
	};
	requestData();
});