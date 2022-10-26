let csrftoken = $('meta[name=csrf-token]').attr('content');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

const waitForImageToLoad = src => {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.addEventListener('load', resolve);
        image.addEventListener('error', reject);
        image.src = src;
    });
}

$('form').on('submit', e => {
    $('#details').hide();
    $('#thumbnail').attr('src', null);
    $('#error, #result').text(null);
    $('#error-container, #progress').addClass('opacity-0');
    $('#loading-1').addClass('load-anim');
    $.ajax({
        type: 'POST',
        url: '/',
        data: {
            yt_id: $('#yt_id').val()
        }
    })
    .done(data => {
        if (data.output && typeof data.output !== 'undefined') {
            waitForImageToLoad(data.output[0]).then(() => {
                $('#loading-1').removeClass('load-anim');
                $('#thumbnail').attr('src', data.output[0]);
                $('#title').text(data.output[1]);
                $('#channel').text(data.output[2]);
                $('#comment-count').text(`${data.output[3]} comments`);
                $('#details').show();
            });
        } else {
            $('#loading').removeClass('load-anim');
            $('#title, #channel, #comment-count').text(null);
            $('#error-container').removeClass('opacity-0');
            $('#error').text(data.error);
        }
    });
    e.preventDefault();
});

$('#process').on('click', e => {
    $('#progress').removeClass('opacity-0');
    $('#loading-2').addClass('load-anim');
    $('#result').text('0');
    $('#comment-count-2').text($('#comment-count').text().replace(/[^0-9]/g, ''));
    var source = new EventSource('/process');
    source.onmessage = (e) => {
        var parsed_data = JSON.parse(e.data.replace(/'/g,'"'));
        $('#result').text(parsed_data['progress']);
        if (parsed_data['done'] == 'true') {
            console.log('done');
            source.close();
            $('#loading-2').removeClass('load-anim');
        }
    }
    e.preventDefault();
});