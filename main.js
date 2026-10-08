var kacinci = 0;
iko.var.ilanTypes = {
    withApplication: 1,
    announcement: 2,
};

// kurum dropdownını doldururken sadece aktif ilanı olan kurumları listelemek için kullanılıyor. Örneğin: Cumhurbaşkanlığı İnsan Kaynakları Ofisi (2 ilan)
iko.func.fillIlanCountForKurumPublicAsync = async function (result) {
    try {
        // var response = await iko.func.getAsyncFetchResult(iko.var.apiURL + '/ilan/GetIlanCountForKurumPublic', '', 'GET');
        // if (response.ok) {
        //var result = await response.json();
        $('#ddl_Kurum').empty();
        $('#ddl_Kurum').append('<option selected value="0">Kurum Seçiniz</option>');

        $.each(result, function (i, item) {
            $('#ddl_Kurum').append($('<option>', {
                text: item.adi + "(" + item.ilanCount + "İLAN)",
                value: item.krM_ID,
            }))
        })
        // } else {
        //     console.error(response.statusText)
        // }

    } catch (ex) {
        console.error(ex);
    }
}





// ilan türü dropdownını doldurur
iko.func.fillIlanTuruListAsync = async function (result) {
    try {
        // var response = await iko.func.getAsyncFetchResult(iko.var.apiURL + '/ilan/GetIlanTuruList', '', 'GET');
        // if (response.ok) {
        //var result = await response.json();
        $('#ddl_IlanTuru').empty();
        $('#ddl_IlanTuru').append('<option selected value="0"> İlan Türünü Seçiniz</option>');

        $.each(result, function (i, item) {
            $('#ddl_IlanTuru').append($('<option>', {
                text: item.ilanTuruAdi,
                value: item.ilanTuruAdi,
            }))
        })
        // } else {
        //     console.error(response.statusText)
        // }
    } catch (ex) {
        console.error(ex);
    }
}


// Şehir dropdownını doldurur
iko.func.fillSehirListAsync = async function (result) {
    try {
        // var response = await iko.func.getAsyncFetchResult(iko.var.apiURL + '/ortak/GetSehirList', '', 'GET');
        // if (response.ok) {
        //     var result = await response.json();
        $('#ddl_Il').empty();
        $('#ddl_Il').append('<option selected value="0"> İl Se&#231;iniz</option>');

        $.each(result, function (i, item) {
            $('#ddl_Il').append($('<option>', {
                text: item.il_Adi,
                value: item.id,
            }))
        })
        // } else {
        //     console.error(response.statusText)
        // }
    } catch (ex) {
        console.error(ex);
    }
}

iko.func.fillIseAlimPageAsync = async function (ilanObject) {
    try {
        var response = await iko.func.getAsyncFetchResult(iko.var.apiURL + '/ilan/GetIseAlimPage', ilanObject, 'POST');
        if (response.ok) {
            var result = await response.json();

            await iko.func.fillIlanTuruListAsync(result.ilanTuru);
            await iko.func.fillSehirListAsync(result.sehirList);
            await iko.func.fillIlanCountForKurumPublicAsync(result.ilanCountForKurum);
            await getIlanlar(result.searchIlan);

        } else {
            console.error(response.statusText);
        }
    } catch (ex) {
        console.error(ex);
    }
}

//async function getIlanlar(params) {
async function getIlanlar(allResult) {
    const pnlIlanlar = $("#pnlIlanlar");
    try {

        // const response = await fetch(apiURL, {
        //     method: 'POST',
        //     body: JSON.stringify(params),
        //     headers: {
        //         'Content-Type': 'application/json'
        //     }
        // });
        // if (response.status === 200) {
        //const allResult = await response.json();
        const now = new Date();
        const result = allResult.filter(ilan => {
            if (!ilan.bitTarih) return true;
            var bitTarih = new Date(ilan.bitTarih);
            bitTarih.setHours(23, 59, 59, 999);
            return bitTarih >= now;
        });
        const fragment = document.createDocumentFragment();

        if (result.length == 0) {
            $('#kayityok').removeClass('d-none')
        } else {
            $('#kayityok').addClass('d-none')
        }

        result.forEach(ilan => {
            var redirectUrl = (ilan.ilanTipi == iko.var.ilanTypes.withApplication ? `IlanDetay?i=${ilan.guid}` : ilan.basvuruLinki);

            const ilanHtml = `<div class="row">
                        <div class="col-md-1 col-xl-1 col-lg-1" style="padding: 0px;">
                            <img class="kurum_logolari_icin" src="/UPS/${ilan.logo_Path}" style="margin-top: 5px">
                        </div>
                        <div class="col-md-3 col-xl-3 col-lg-3">
                            <span style="color: black; font-size:14px;"><br><b>${ilan.kurumAdi}</b><br><span style="color: black; font-size:14px;">${ilan.birimAdi}</span><br><br></span>
                        </div>
                        <div class="col-md-4 col-xl-4 col-lg-4 " style=""><br><span style="color: black;font-weight:600;font-size:14px;">${ilan.ilanBaslik}</span></div>
                        <div class="col-md-2 col-xl-2 col-lg-2"><br><span style="color: black; font-size:14px;"><b>${iko.func.fDate(ilan.bitTarih, "date")}</b><br><b>${iko.func.fDate(ilan.bitTarih, "day")}</b></span></div>  
                        <div class="col-md-2 col-xl-2 col-lg-2"><br><a href="${redirectUrl}" class="btn btn-block small" style="width: 100%; background-color: #033980; color: white; border-radius: 10px/10px;">` + (ilan.ilanTipi == iko.var.ilanTypes.withApplication ? "Başvur" : "İlana Git") + `</a></div>
                    </div><hr style="background-color: #ededed !important;">`;
            $(fragment).append(ilanHtml);
        });

        pnlIlanlar.html(fragment);
        // }
    } catch (error) {
        console.error('API çağrısı sırasında bir hata oluştu:', error);
    }
}

iko.func.searchIlan = async function (ilanObject) {
    try {
        var response = await iko.func.getAsyncFetchResult(iko.var.apiURL + '/ilan/SearchIlanPublic', ilanObject, 'POST');
        if (response.ok) {
            var result = await response.json();
            await getIlanlar(result);

        } else {
            console.error(response.statusText);
        }
    } catch (ex) {
        console.error(ex);
    }
}

// Seçili optionlara göre aktifteki ilanları listeler. Her option değiştirildiğinde çalışır.
$(document).ready(async function () {
    const ilanObject = {
        krM_ID: 0,
        searchText: '',
        il: "0",
        ilanTuru: "0",
    };

    //await getIlanlar(ilanObject);
    await iko.func.fillIseAlimPageAsync(ilanObject);

    $("#btn_Search").on("click", async function () {
        ilanObject.krM_ID = parseInt($('#ddl_Kurum').val());
        ilanObject.searchText = $("#txt_SearchMetin").val();
        ilanObject.il = $('#ddl_Il option:selected').text();
        ilanObject.ilanTuru = $('#ddl_IlanTuru option:selected').text();

        if (ilanObject.il == " İl Seçiniz") {
            ilanObject.il = "0";
        }

        if (ilanObject.ilanTuru == " İlan Türünü Seçiniz") {
            ilanObject.ilanTuru = "0";
        }

        //await getIlanlar(ilanObject);
        await iko.func.searchIlan(ilanObject);
    });


    $("#ddl_Kurum").on("change", async function () {
        //await iko.func.fillIlanTuruListAsync()
        //await iko.func.fillSehirListAsync()
        ilanObject.krM_ID = parseInt($('#ddl_Kurum').val());
        ilanObject.searchText = $("#txt_SearchMetin").val();
        ilanObject.il = $('#ddl_Il option:selected').text();
        ilanObject.ilanTuru = $('#ddl_IlanTuru option:selected').text();

        if (ilanObject.il == " İl Seçiniz") {
            ilanObject.il = "0";
        }

        if (ilanObject.ilanTuru == " İlan Türünü Seçiniz") {
            ilanObject.ilanTuru = "0";
        }

        //await getIlanlar(ilanObject);
        await iko.func.searchIlan(ilanObject);
    });
    $("#txt_SearchMetin").on("change", async function () {
        ilanObject.krM_ID = parseInt($('#ddl_Kurum').val());
        ilanObject.searchText = $("#txt_SearchMetin").val();
        ilanObject.il = $('#ddl_Il option:selected').text();
        ilanObject.ilanTuru = $('#ddl_IlanTuru option:selected').text();

        if (ilanObject.il == " İl Seçiniz") {
            ilanObject.il = "0";
        }

        if (ilanObject.ilanTuru == " İlan Türünü Seçiniz") {
            ilanObject.ilanTuru = "0";
        }

        //await getIlanlar(ilanObject);
        await iko.func.searchIlan(ilanObject);
    });
    $("#ddl_Il").on("change", async function () {
        var kacinci = 2;

        ilanObject.krM_ID = parseInt($('#ddl_Kurum').val());
        ilanObject.searchText = $("#txt_SearchMetin").val();
        ilanObject.il = $('#ddl_Il option:selected').text();
        ilanObject.ilanTuru = $('#ddl_IlanTuru option:selected').text();

        if (ilanObject.il == " İl Seçiniz") {
            ilanObject.il = "0";
        }

        if (ilanObject.ilanTuru == " İlan Türünü Seçiniz") {
            ilanObject.ilanTuru = "0";
        }

        //await getIlanlar(ilanObject);
        await iko.func.searchIlan(ilanObject);
    });
    $("#ddl_IlanTuru").on("change", async function () {
        var kacinci = 1;
        //await iko.func.fillSehirListAsync()

        ilanObject.krM_ID = parseInt($('#ddl_Kurum').val());
        ilanObject.searchText = $("#txt_SearchMetin").val();
        ilanObject.il = $('#ddl_Il option:selected').text();
        ilanObject.ilanTuru = $('#ddl_IlanTuru option:selected').text();

        if (ilanObject.il == " İl Seçiniz") {
            ilanObject.il = "0";
        }

        if (ilanObject.ilanTuru == " İlan Türünü Seçiniz") {
            ilanObject.ilanTuru = "0";
        }

        //await getIlanlar(ilanObject);
        await iko.func.searchIlan(ilanObject);
    });
});

// popup
///POPUP Closed 27.07.2026
/*
const popupOverlay = document.getElementById('popupOverlay');
const popup = document.querySelector('.popup');
const closePopupButton = document.getElementById('closePopup');

function showPopup() {
    popupOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hidePopup() {
    popupOverlay.classList.remove('active');
    document.body.style.overflow = 'auto';
}

window.addEventListener('DOMContentLoaded', function () {
    showPopup();
});

closePopupButton.addEventListener('click', hidePopup);

popupOverlay.addEventListener('click', function (event) {
    // Check if the click was on the overlay itself, not on the popup
    if (event.target === popupOverlay) {
        hidePopup();
    }
});
*/