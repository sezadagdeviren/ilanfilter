// #Infrastructure Begin
var iko = {};
iko.var = {};
iko.let = {};
iko.func = {};
iko.const = {};
iko.enum = {};
iko.class = {};
iko.abortControllers = {};

iko.func.showLoadingModal = function () {
    localStorage.setItem("popUpClose", false);
    $('cboxOverlay').attr('disabled', true);
    var modallo = $('<div />');
    modallo.addClass("modallo");
    $('body').append(modallo);
    var loading = $(".loading");
    loading.show();
    var top = Math.max($(window).height() / 2 - loading[0].offsetHeight / 2, 0);
    var left = Math.max($(window).width() / 2 - loading[0].offsetWidth / 2, 0);
    loading.css({ top: top, left: left });
}

// Function to hide the loading modal
iko.func.hideLoadingModal = function () {
    var loading = $('.loading');
    if (loading) {
        loading.hide();
    }
    modallo = document.querySelector('.modallo');
    if (modallo) {
        modallo.remove();
    }
    $('cboxOverlay').attr('disabled', false);
    localStorage.setItem("popUpClose", true);
}


iko.var.dataTableLanguageUrl = "/js/Turkish.json?v=" + new Date().toDateString();
iko.var.dataTableSettings = {
    dom: 'rt <"row mt-4"<"pagination-select col-md-6 d-flex align-items-center"l<"pagination-text ms-4"i>><"col-md-6 col-lg-12 d-flex justify-content-md-end jc-center-mobile justify-content-sm-center"p>>',
    //dom: `rt <"mt-4 d-flex justify-content-between"
    //        <"pagination-select d-flex align-items-center"l
    //            <"pagination-text ms-4"i>
    //        >
    //        <"d-flex justify-content-md-end jc-center-mobile justify-content-sm-center"p>
    //    >`,

    //dom: 
    //    window.innerWidth < 576 ? `rt <"row mt-4"
    //                                    <"pagination-select col-md-6 d-flex align-items-center"l
    //                                        <"pagination-text ms-4"i>
    //                                    >
    //                                    <"col-md-6 col-lg-12 d-flex justify-content-md-end jc-center-mobile justify-content-sm-center"p>
    //                                >`
    //            :
    //            `rt <"mt-4 d-flex justify-content-between"
    //                        <"pagination-select d-flex align-items-center"l
    //                            <"pagination-text ms-4"i>
    //                        >
    //                        <"d-flex justify-content-md-end jc-center-mobile justify-content-sm-center"p>
    //                    >`,
    language: {
        url: iko.var.dataTableLanguageUrl,
    },
    searching: false,
    ordering: false,
    processing: true,
    serverSide: true,
    destroy: true,
    pagingType: "simple_numbers",
    fixedHeader: {
        headerOffset: -7
    },
    error: function (xhr, error, code) {
        if (xhr.status == 511) {
            window.location = "/inside";
        }
    }
};
iko.var.dataTableSettingsOld = {
    //dom: 'rt <""<""l<""i>><""p>>',
    dom: `rt <"row mt-1"
            <"col-md-4 pad-12-08px"l>
            <"col-md-6"i>
            <"col-md-2 pad-12-08px"p>
        >`,
    language: {
        url: iko.var.dataTableLanguageUrl,
    },
    searching: false,
    ordering: false,
    processing: true,
    serverSide: true,
    destroy: true,
    pagingType: "numbers",
    fixedHeader: {
        headerOffset: -7
    },
    error: function (xhr, error, code) {
        if (xhr.status == 511) {
            window.location = "/inside";
        }
    }
};

iko.var.apiURL = 'https://api.kariyerkapisi.gov.tr/api';
iko.var.kvkkbaseurl = 'https://kariyerkapisi.gov.tr/';

if (window.location.href.includes("localhost")) {
    //iko.var.apiURL = "https://localhost:5191/api"
    iko.var.apiURL = "http://localhost:5191/api"
    //iko.var.apiURL = "https://test-kkamu-api.cbiko.gov.tr/api"
    //iko.var.apiURL = "https://api-test.kariyerkapisi.gov.tr/api"
    iko.var.kvkkbaseurl = "http://localhost:5054/"
}

if (window.location.href.includes("test")) {
    iko.var.apiURL = "https://api-test.kariyerkapisi.gov.tr/api"
    iko.var.kvkkbaseurl = "https://test.kariyerkapisi.gov.tr/"
    //iko.var.kvkkbaseurl = "https://test-kkamu.cbiko.gov.tr/"
}
//if (window.location.href.includes("test")) {
//    iko.var.apiURL = "https://test-kkamu-api.cbiko.gov.tr/api"
//    iko.var.kvkkbaseurl = "https://test-kkamu.cbiko.gov.tr/"
//}

$(document).ready(async function () {
    $(".select2").select2();

    if ($.fn.multiselect) {
        $.fn.multiselect.Constructor.prototype.defaults.nonSelectedText = 'Seçim yapılmadı';
        $.fn.multiselect.Constructor.prototype.defaults.allSelectedText = 'Tümü seçildi';
        $.fn.multiselect.Constructor.prototype.defaults.nSelectedText = 'Seçildi';
        $.fn.multiselect.Constructor.prototype.defaults.selectAllText = 'Tümünü Seç';
        $.fn.multiselect.Constructor.prototype.defaults.filterPlaceholder = 'Ara...';
    }
});

//$(document).keydown(function (event) {
//    if (event.keyCode == 123) {
//        return false;
//    } else if (event.ctrlKey && event.shiftKey && event.keyCode == 73) {       
//        return false;
//    }
//});

iko.func.datatableJsonParse = function (data) {

    if (data === null) {
        return null;

    }

    data = (data.split(':,')).join(':" ",');  //.replaceAll(':,', ':" ",');
    data = (data.split('\t')).join(' ');  //.replaceAll(':,', ':" ",');
    data = (data.split('\n')).join(' '); //.replaceAll("\n", "");
    data = (data.split('\r')).join(' '); //.replaceAll("\n", "");
    data = (data.split('\r\n')).join(' '); //.replaceAll("\n", "");
    data = (data.split('null')).join('"-"'); //.replaceAll("\n", "");

    return JSON.parse(data);
};

iko.func.controlInputs = function () {
    $('.input-error').removeClass('input-error');
    var count = 0;
    var isValid = true;
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    var phoneRegex = /^\(\d{3}\) \d{3} \d{2} \d{2}$/;
    $('.required').each(function () {
        var inputValue = $(this).val();
        if (inputValue.trim() === "") {
            $(this).addClass('input-error');
            count++;
        }
    });
    $('.required-file').each(function () {
        var input = $(this);
        var imgSrc = input.closest('.row').find('img.required-image').attr('src')
        var dosya = input[0].files[0];
        if (!dosya && iko.func.isNullOrEmpty(imgSrc)) {
            $(this).addClass('input-error');
            count++;
        }
    });
    $('.email').each(function () {
        var inputValue = $(this).val();
        if (!emailRegex.test(inputValue)) {
            $(this).addClass('input-error');
            count++;
        }
    })
    $('.phone').each(function () {
        var inputValue = $(this).val();
        if (!phoneRegex.test(inputValue)) {
            $(this).addClass('input-error');
            count++;
        }
    })
    if (count > 0) isValid = false;
    return isValid;
}

iko.func.getAsyncFetchResult = async function (url, paramObj, method, controller = new AbortController()) {
    var response;
    var requestVerificationToken;
    var _token = localStorage.getItem("token");
    const signal = controller.signal;
    try {
        requestVerificationToken = document.getElementsByName("__RequestVerificationToken")[0].value;
    } catch {
        requestVerificationToken = "";
    }
    var token;
    try {
        token = _token;
    } catch {
        token = "";
    }
    if (localStorage.getItem("token") === null) {
        localStorage.setItem("token", token);
    }
    if (token === undefined) {
        token = localStorage.getItem("token");
    } else {
        if (token != localStorage.getItem("token")) {
            localStorage.setItem("token", token);
        }
    }
    if (method === 'GET') {
        response = await fetch(url, {
            method: method,
            signal: signal,
            cache: "no-cache",
            referrerPolicy: "strict-origin-when-cross-origin",
            mode: "cors",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                'RequestVerificationToken': requestVerificationToken
            }
        });
    } else {
        response = await fetch(url, {
            method: method,
            signal: signal,
            cache: "no-cache",
            referrerPolicy: "strict-origin-when-cross-origin",
            mode: "cors",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                'RequestVerificationToken': requestVerificationToken
            },
            body: JSON.stringify(paramObj),
        });
    }
    if (response.status == 200) {
        //console.log("200");
    } else if (response.status == 401) {
        //console.log("401");
        window.location = "/Logout";
    } else if (response.status == 511) {
        window.location = "/inside";
    }
    return response;
}

$(document).ready(function () {
    try {
        $.fn.dataTable.ext.errMode = function (settings, helpPage, message) {
            console.error("settings : " + settings);
            console.error("helpPage : " + helpPage);
            console.error("message : " + message);
            /*if()*/
        };
    } catch (err) {

    }
});

iko.func.getAsyncFormDataFetchResult = async function (url, paramObj, controller = new AbortController()) {
    var response;
    var requestVerificationToken;
    var _token = localStorage.getItem("token");
    const signal = controller.signal;
    try {
        requestVerificationToken = document.getElementsByName("__RequestVerificationToken")[0].value;
    } catch {
        requestVerificationToken = "";
    }
    var token;
    try {
        token = _token;
    } catch {
        token = "";
    }
    if (localStorage.getItem("token") === null) {
        localStorage.setItem("token", token);
    }
    if (token === undefined) {
        token = localStorage.getItem("token");
    } else {
        if (token != localStorage.getItem("token")) {
            localStorage.setItem("token", token);
        }
    }

    response = await fetch(url, {
        method: 'POST',
        signal: signal,
        cache: "no-cache",
        referrerPolicy: "no-referrer",
        headers: {
            //"Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            'RequestVerificationToken': requestVerificationToken
        },
        body: paramObj,
    });
    if (response.status == 200) {
        //console.log("200");
    } else if (response.status == 401) {
        //console.log("401");
        window.location = "/Logout";
    } else if (response.status == 511) {
        window.location = "/inside";
    }
    return response;
}

iko.func.createAjaxRequest = function (data, callback, settings, url, dataCreator, requestController) {
    // data,callback,settings -> these values default from datatables ajax
    // url : string -> request url after /api Ex: /basvuru/
    // dataCreator : function -> function for apicall data creation
    // requestContorller : jqXHR? -> previous request if available

    const token = localStorage.getItem("token");
    if (settings.jqXHR) {
        settings.jqXHR.abort();
    }
    if (requestController) {
        requestController.abort();
    }
    const request = $.ajax({
        url: iko.var.apiURL + url,
        type: "POST",
        contentType: "application/json; charset=utf-8",
        beforeSend: function (xhr) {
            xhr.setRequestHeader("Authorization", "Bearer " + token);
        },
        crossDomain: true,
        data: dataCreator(data),
        success: function (json) {
            callback(json);
        },
        error: function (xhr, status, error) {
            if (xhr.status == 511) {
                window.location = "/inside";
            }
            if (xhr.status == 401) {
                window.location = "/Logout";
            }
            if (status !== 'abort') {
                console.error('DataTables AJAX error:', error);
            }
        }
    });
    // Start a new Ajax call and store the handle
    settings.jqXHR = request;
    return request;
}

function BindTable(jsondata, tableid, isExist) {/*Function used to convert the JSON array to Html Table*/
    var columns = BindTableHeader(jsondata, tableid, isExist); /*Gets all the column headings of Excel*/
    for (var i = 0; i < jsondata.length; i++) {
        var row$ = $('<tr/>');
        for (var colIndex = 0; colIndex < columns.length; colIndex++) {
            var cellValue = jsondata[i][columns[colIndex]];
            if (cellValue == null)
                cellValue = "";
            row$.append($('<td/>').html(cellValue));
        }
        $(tableid).append(row$);
    }
}
function BindTableHeader(jsondata, tableid, isExist) {/*Function used to get all column names from JSON and bind the html table header*/
    var columnSet = [];
    var headerTr$ = $('<tr/>');
    for (var i = 0; i < jsondata.length; i++) {
        var rowHash = jsondata[i];
        for (var key in rowHash) {
            if (rowHash.hasOwnProperty(key)) {
                if ($.inArray(key, columnSet) == -1) {/*Adding each unique column names to a variable array*/
                    columnSet.push(key);
                    headerTr$.append($('<th/>').html(key));
                }
            }
        }
    }
    if (!isExist)
        $(tableid).append(headerTr$);
    return columnSet;
}
iko.func.isNullOrEmpty = function (string) {
    if (string === null)
        return true;
    if (string === undefined)
        return true;
    string = String(string);
    if (string.trim() === "")
        return true;
    else
        return false;
}
iko.func.isSelectedAny = function (string) {
    debugger;
    if (string === null)
        return true;
    if (string === undefined)
        return true;
    string = String(string);
    if (string.trim() === "0")
        return true;
    else
        return false;
}
iko.func.returnIsNullOrEmptyString = function (string) {
    if (string === null)
        return '';
    if (string === undefined)
        return '';
    string = String(string);
    if (string.trim() === "")
        return '';
    else
        return string;
}
iko.func.formatDate = function (dateStart, dateFinish) {
    let dateNow = new Date();
    let formattedStartDate = new Date(dateStart);
    let formattedFinishDate = new Date(dateFinish);
    if (formattedStartDate.getFullYear() - dateNow.getFullYear() >= 5) {
        return 'Tarihler kurum tarafından daha sonra belirlenecektir.'
    } else {
        return iko.func.controlDate(formattedStartDate) + '-' + iko.func.controlDate(formattedFinishDate);
    }
}
iko.func.controlDate = function (date) {
    let day = date.getDate();

    let month = (date.getMonth() + 1);

    let year = date.getFullYear();

    if (day < 10) {
        day = '0' + day;
    }

    if (month < 10) {
        month = `0${month}`;
    }

    return `${day}.${month}.${year}`;
}
iko.func.controlDateTime = function (date) {
    let day = date.getDate();
    let month = (date.getMonth() + 1);
    let year = date.getFullYear();
    let hours = date.getHours();
    let minutes = date.getMinutes();

    if (day < 10) day = '0' + day;
    if (month < 10) month = '0' + month;
    if (hours < 10) hours = '0' + hours;
    if (minutes < 10) minutes = '0' + minutes;

    return `${day}.${month}.${year} ${hours}:${minutes}`;
}
iko.func.formatDatePicker = function (date) {
    var splittedDate = date.split(".");
    var formattedDate = splittedDate[2] + "-" + splittedDate[1] + "-" + splittedDate[0] + "T00:00";
    return formattedDate;
}
iko.func.formatDateForDatePicker = function (date) {
    if (date.includes("T")) {
        var splittedDate = date.split("T");
        splittedDate = splittedDate[0].split("-");
        var formattedDate = splittedDate[2] + "." + splittedDate[1] + "." + splittedDate[0];
        return formattedDate;
    }
    else {
        var splittedDate = date.split("-");
        var formattedDate = splittedDate[2] + "." + splittedDate[1] + "." + splittedDate[0];
        return formattedDate;
    }
}

iko.func.queryUrlParam = function (query) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(query);
}

iko.func.formatJsDate = function (date) {
    date = moment(date, 'DD.MM.YYYY').locale("en").format("YYYY-MM-DD");
    return date;
}

/*
iko.func.queryUrlParamPop = function (href, query) {
    console.log(href)
    const urlParams = new URLSearchParams(href);
    return urlParams.get(query);
}*/


// Bu fonksiyon, belirtilen bir parametrenin değerini bir URL'den çıkarmak için kullanılır
iko.func.queryUrlParamPop = function (url, name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(url);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

iko.func.lowercaseFirstTwoChars = function (string) {
    return string.charAt(0).toLowerCase() + string.charAt(1).toLowerCase() + string.slice(2);
}

iko.func.fDate = function (tarih, type) {
    const haftaninGunleri = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];
    const aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];

    const parts = tarih.split("-");
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // JS ayları 0'dan başlatır
    const day = parseInt(parts[2], 10);

    // UTC'de bir Date nesnesi oluştur
    const date = new Date(Date.UTC(year, month, day));

    let gunIndex = date.getUTCDay();

    //gunIndex = (gunIndex === 0) ? 6 : gunIndex - 1; // Pazar 0'dır, bu yüzden 6 olarak ayarlıyoruz, diğer günler 1 eksiltilir
    //gunIndex = (gunIndex === 0) ? 6 : gunIndex; // Pazar 0'dır, bu yüzden 6 olarak ayarlıyoruz, diğer günler 1 eksiltilir

    const gun = date.getDate().toString().padStart(2, '0');
    const ayIndex = date.getMonth();
    const yil = date.getFullYear();

    const gunAdi = haftaninGunleri[gunIndex];
    const ay = aylar[ayIndex];

    if (type === "full")
        return `${gun} ${ay} ${yil} ${gunAdi}`;
    else if (type === "date")
        return `${gun} ${ay} ${yil}`;
    else if (type === "day")
        return `${gunAdi}`;
    else if (type === "sdate")
        return `${gun}.${ayIndex + 1}.${yil}`; // Ay indexi 0'dan başladığı için 1 ekliyoruz
}


iko.func.removeLastCommas = function (text) {
    return text.replace(/,(?=[^,]*$)/, '');
}

// BBCode → HTML converter. Mirrors server-side KKWeb.Helper.BBCodeHelper.Convert
// so that PDF/modal (server) ve ilan-detay (client) renderları birebir aynı HTML üretir.
iko.func.convertBBCodeAndFormatToHTML = (function () {
    var SAFE_COLOR = /^(#[0-9a-fA-F]{3,8}|[a-zA-Z]+)$/;
    var SAFE_SIZE = /^\d+%?$/;
    var SAFE_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

    function htmlEncode(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function htmlDecode(s) {
        return String(s)
            .replace(/&#39;/g, "'")
            .replace(/&quot;/g, '"')
            .replace(/&gt;/g, '>')
            .replace(/&lt;/g, '<')
            .replace(/&amp;/g, '&');
    }

    function isSafeUrl(url) {
        try {
            var u = new URL(url);
            return u.protocol === 'http:' || u.protocol === 'https:' || u.protocol === 'mailto:';
        } catch (e) {
            return false;
        }
    }

    return function (text) {
        if (text == null) return '';
        var s = String(text);
        if (!s.trim()) return '';

        // 1) Encode raw input
        s = htmlEncode(s);

        // 2) Lists (before newline replacement)
        s = s.replace(/\[list=1\]([\s\S]*?)\[\/list\]/gi, '<ol>$1</ol>');
        s = s.replace(/\[list=a\]([\s\S]*?)\[\/list\]/g, '<ol style="list-style-type:lower-alpha;">$1</ol>');
        s = s.replace(/\[list=A\]([\s\S]*?)\[\/list\]/g, '<ol style="list-style-type:upper-alpha;">$1</ol>');
        s = s.replace(/\[list\]([\s\S]*?)\[\/list\]/gi, '<ul>$1</ul>');
        s = s.replace(/[\r\n]*\[\*\]([^\r\n]*)[\r\n]*/gi, '<li>$1</li>');

        // 3) Newlines and tabs
        s = s.replace(/\r\n/g, '\n').replace(/\n/g, '<br/>');
        s = s.replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');

        // 4) Inline formatting
        s = s.replace(/\[b\]([\s\S]*?)\[\/b\]/gi, '<strong>$1</strong>');
        s = s.replace(/\[i\]([\s\S]*?)\[\/i\]/gi, '<em>$1</em>');
        s = s.replace(/\[u\]([\s\S]*?)\[\/u\]/gi, '<u>$1</u>');
        s = s.replace(/\[s\]([\s\S]*?)\[\/s\]/gi, '<s>$1</s>');

        // 5) Alignment
        s = s.replace(/\[left\]([\s\S]*?)\[\/left\]/gi, '<div style="text-align:left;">$1</div>');
        s = s.replace(/\[right\]([\s\S]*?)\[\/right\]/gi, '<div style="text-align:right;">$1</div>');
        s = s.replace(/\[center\]([\s\S]*?)\[\/center\]/gi, '<div style="text-align:center;">$1</div>');
        s = s.replace(/\[justify\]([\s\S]*?)\[\/justify\]/gi, '<p style="text-align:justify;">$1</p>');

        // 6) Styled spans — sanitize option; on invalid value keep inner text
        s = s.replace(/\[color=([^\]]+)\]([\s\S]*?)\[\/color\]/gi, function (_m, v, t) {
            var val = htmlDecode(v).trim();
            if (!SAFE_COLOR.test(val)) return t;
            return '<span style="color:' + val + ';">' + t + '</span>';
        });

        s = s.replace(/\[size=([^\]]+)\]([\s\S]*?)\[\/size\]/gi, function (_m, v, t) {
            var val = htmlDecode(v).trim();
            if (!SAFE_SIZE.test(val)) return t;
            if (val.charAt(val.length - 1) !== '%') val += '%';
            return '<span style="font-size:' + val + ';">' + t + '</span>';
        });

        // 7) Quote + code
        s = s.replace(/\[quote(?:=&quot;([\s\S]*?)&quot;)?\]([\s\S]*?)\[\/quote\]/gi, function (_m, cite, body) {
            if (!cite) return '<blockquote>' + body + '</blockquote>';
            return '<blockquote><cite>' + cite + '</cite>' + body + '</blockquote>';
        });
        s = s.replace(/\[code\]([\s\S]*?)\[\/code\]/gi, '<code>$1</code>');

        // 8) Links
        s = s.replace(/\[url=([^\]]+)\]([\s\S]*?)\[\/url\]/gi, function (_m, href, inner) {
            var h = htmlDecode(href).trim();
            if (!isSafeUrl(h)) return inner;
            return '<a href="' + htmlEncode(h) + '" rel="nofollow noopener noreferrer" target="_blank">' + inner + '</a>';
        });

        s = s.replace(/\[url\]([\s\S]*?)\[\/url\]/gi, function (_m, inner) {
            var h = htmlDecode(inner);
            if (!isSafeUrl(h)) return inner;
            var safe = htmlEncode(h);
            return '<a href="' + safe + '" rel="nofollow noopener noreferrer" target="_blank">' + safe + '</a>';
        });

        s = s.replace(/\[email\]([\s\S]*?)\[\/email\]/gi, function (_m, inner) {
            var addr = htmlDecode(inner).trim();
            if (!SAFE_EMAIL.test(addr)) return inner;
            var safe = htmlEncode(addr);
            return '<a href="mailto:' + safe + '">' + safe + '</a>';
        });

        // 9) Images
        s = s.replace(/\[img\]([\s\S]*?)\[\/img\]/gi, function (_m, inner) {
            var src = htmlDecode(inner);
            if (!isSafeUrl(src)) return '';
            return '<img src="' + htmlEncode(src) + '" alt="" loading="lazy" />';
        });

        debugger;

        //const out = s.replace(/&amp;#(\d+);/g, (_, code) => String.fromCodePoint(code));
        s = s.replace(/&amp;#(\d+);/g, (_, code) => `&#` + code + `;`);

        return s;
    };
})();

iko.func.farkiBul = function (tarihParametresi) {
    const simdikiTarih = new Date();
    const simdikiTarihUtc = Date.UTC(simdikiTarih.getUTCFullYear(), simdikiTarih.getUTCMonth(), simdikiTarih.getUTCDate(), simdikiTarih.getUTCHours(), simdikiTarih.getUTCMinutes(), simdikiTarih.getUTCSeconds());

    const verilenTarih = new Date(tarihParametresi);
    const verilenTarihUtc = Date.UTC(verilenTarih.getUTCFullYear(), verilenTarih.getUTCMonth(), verilenTarih.getUTCDate(), verilenTarih.getUTCHours(), verilenTarih.getUTCMinutes(), verilenTarih.getUTCSeconds());

    let farkSaniye = Math.floor((verilenTarihUtc - simdikiTarihUtc) / 1000);

    const yil = 31536000;
    const ay = 2592000;
    const hafta = 604800;
    const gun = 86400;
    const saat = 3600;
    const dakika = 60;

    var farkText = '';
    //while (farkSaniye >= 60) {
    for (i = 0; i < 2; i++) {
        if (farkSaniye >= yil) {
            farkText = farkText + Math.floor(farkSaniye / yil) + ' Yıl';
            farkSaniye = farkSaniye - (Math.floor(farkSaniye / yil) * yil);
        }
        else if (farkSaniye >= ay) {
            farkText = farkText + Math.floor(farkSaniye / ay) + ' Ay';
            farkSaniye = farkSaniye - (Math.floor(farkSaniye / ay) * ay);
        }
        else if (farkSaniye >= hafta) {
            farkText = farkText + Math.floor(farkSaniye / hafta) + ' Hafta';
            farkSaniye = farkSaniye - (Math.floor(farkSaniye / hafta) * hafta);
        }
        else if (farkSaniye >= gun) {
            farkText = farkText + Math.floor(farkSaniye / gun) + ' Gün';
            farkSaniye = farkSaniye - (Math.floor(farkSaniye / gun) * gun);
        }
        else if (farkSaniye >= saat) {
            farkText = farkText + Math.floor(farkSaniye / saat) + ' Saat';
            farkSaniye = farkSaniye - (Math.floor(farkSaniye / saat) * saat);
        }
        else if (farkSaniye >= dakika) {
            farkText = farkText + Math.floor(farkSaniye / dakika) + ' Dakika';
            farkSaniye = farkSaniye - (Math.floor(farkSaniye / dakika) * dakika);
        }
        else {
            farkSaniye = -1;
        }
        farkText = farkText + ' ';
    }
    if (farkText == '') {
        farkText = 'Şuan';
    }

    return farkText;

    //if (farkSaniye >= yil) {
    //    return Math.floor(farkSaniye / yil) + ' Yıl';
    //}
    //if (farkSaniye >= ay) {
    //    return Math.floor(farkSaniye / ay) + ' Ay';
    //}
    //if (farkSaniye >= hafta) {
    //    return Math.floor(farkSaniye / hafta) + ' Hafta';
    //}
    //if (farkSaniye >= gun) {
    //    return Math.floor(farkSaniye / gun) + ' Gün';
    //}
    //if (farkSaniye >= saat) {
    //    return Math.floor(farkSaniye / saat) + ' Saat';
    //}
    //if (farkSaniye >= dakika) {
    //    return Math.floor(farkSaniye / dakika) + ' Dakika';
    //}
    //if (farkSaniye < 60) {
    //    return 'Şuan';
    //}
}

iko.func.farkiBulDays = function (tarih1, tarih2) {
    // İki tarihi çıkartma
    var farkMillisaniye = tarih2 - tarih1;
    // Farkı kullanarak yeni bir tarih nesnesi oluşturma
    var sonucTarih = new Date(farkMillisaniye);

    var today = new Date();
    var timeDiff = tarih2 - today.getTime();
    var remainingDays = Math.ceil(timeDiff / (1000 * 3600 * 24)); // Milisaniyeden güne çevirme
    var remainingYears = Math.floor(remainingDays / 365);
    var remainingMonths = Math.floor((remainingDays % 365) / 30); // Ortalama ay süresi 30 gün olarak kabul edilmiştir.
    var remainingDays = remainingDays % 30;

    if (remainingYears > 0)
        return remainingYears + " yıl " + remainingMonths + " ay " + remainingDays + " gün kaldı";

    else if (remainingMonths > 0)
        return remainingMonths + " ay " + remainingDays + " gün kaldı";
    else {
        return remainingDays + " gün kaldı";
    }

    return "";
}

const delayForToastr = ms => new Promise(res => setTimeout(res, ms));
if (typeof toastr !== "undefined") {
    toastr.options = {
        "closeButton": true,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }
}
function readFileAsync(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = function (e) {
            resolve(e.target.result);
        };

        reader.onerror = function (err) {
            reject(err);
        };

        reader.readAsDataURL(file);
    });
}

// Checkboxın xheckli olup olmadığını kontrol eden helper fonksiyon
iko.func.formatCheckbox = function (checkbox) {
    if ($(checkbox).is(":checked")) { return 1; }
    else { return 0; }
}

iko.func.downloadFileResponse = function (blob, filename) {
    const blobUrl = URL.createObjectURL(blob);

    // Anchor click is the most compatible approach
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = filename;
    a.rel = "noopener"; // good hygiene
    document.body.appendChild(a);
    a.click();
    a.remove();

    // Cleanup to avoid memory leaks
    URL.revokeObjectURL(blobUrl);
}