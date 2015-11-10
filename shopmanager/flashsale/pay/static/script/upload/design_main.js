/*global Qiniu */
/*global plupload */
/*global FileProgress */
/*global hljs */

var TOUTU_TYPE = "1";
var CONTENT_TYPE = "2";
var SHANGPIN_TYPE = "3";
$(function () {


    var zhutuuploader = Qiniu.uploader({
        runtimes: 'html5,flash,html4',
        browse_button: 'head_img',
        container: 'zhutu',
        drop_element: 'zhutu',
        max_file_size: '100mb',
        flash_swf_url: 'js/plupload/Moxie.swf',
        dragdrop: true,
        chunk_size: '4mb',
        uptoken_url: $('#uptoken_url').val(),
        domain: $('#domain').val(),
        auto_start: true,
        init: {
            'FilesAdded': function (up, files) {

            },
            'BeforeUpload': function (up, file) {

            },
            'UploadProgress': function (up, file) {

            },
            'UploadComplete': function () {
                //$('#success').show();
            },
            'FileUploaded': function (up, file, info) {
                var domain = up.getOption('domain');
                var res = jQuery.parseJSON(info);
                var sourceLink = domain + res.key; //获取上传成功后的文件的Url
                $("#head_img").attr("src", sourceLink);
            },
            'Error': function (up, err, errTip) {

            }
            ,
            'Key': function (up, file) {
                var timestamp = new Date().getTime();
                var key = "MG-" + timestamp + "-" + file.name;
                return key
            }
        }
    });
    var all_tou = $(".toutu");
    $.each(all_tou, function (index, obj) {
        var product_id = all_tou.eq(index).attr("data-product");
        var temp_contain = "toutu_" + product_id;
        var browse = "chuan_" + product_id;
        var toutuuploader = Qiniu.uploader({
            runtimes: 'html5,flash,html4',
            browse_button: browse,
            container: temp_contain,
            drop_element: temp_contain,
            max_file_size: '100mb',
            flash_swf_url: 'js/plupload/Moxie.swf',
            dragdrop: true,
            chunk_size: '4mb',
            uptoken_url: $('#uptoken_url').val(),
            domain: $('#domain').val(),
            auto_start: true,
            init: {
                'FilesAdded': function (up, files) {

                },
                'BeforeUpload': function (up, file) {

                },
                'UploadProgress': function (up, file) {

                },
                'UploadComplete': function () {
                    //$('#success').show();
                },
                'FileUploaded': function (up, file, info) {
                    var domain = up.getOption('domain');
                    var res = jQuery.parseJSON(info);
                    var sourceLink = domain + res.key; //获取上传成功后的文件的Url
                    $("#"+browse).attr("src", sourceLink);
                    ajaxImage(SHANGPIN_TYPE, product_id, sourceLink)
                },
                'Error': function (up, err, errTip) {

                }
                ,
                'Key': function (up, file) {
                    var timestamp = new Date().getTime();
                    var key = "MG-" + timestamp + "-" + file.name;
                    // do something with key
                    return key
                }
            }
        });

    });

    zhutuuploader.bind('FileUploaded', function (up, file, info) {
        var domain = up.getOption('domain');
        var res = jQuery.parseJSON(info.response);
        var sourceLink = domain + res.key;

        ajaxImage(TOUTU_TYPE, $("#model_id").html(), sourceLink)
    });

    function ajaxImage(type, pro_id, pic_link) {
        var requestUrl = "/mm/chuantu/";
        var requestCallBack = function (data) {
            console.log(data)
        };
        $.ajax({
            type: 'post',
            url: requestUrl,
            data: {'type': type, "pro_id": pro_id, "pic_link": pic_link},
            dataType: 'json',
            success: requestCallBack
        });
    }
});
