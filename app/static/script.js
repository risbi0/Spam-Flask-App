let csrftoken = $('meta[name=csrf-token]').attr('content');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$('form').on('submit', e => {
    $('#details').hide();
    $.ajax({
        type: 'POST',
        url: '/',
        data: {
            yt_id: $('#yt_id').val()
        }
    })
    .done(data => {
        if (data.output !== null) {
            $('#details').show();
            $('#thumbnail').attr('src', data.output[0]);
            $('#title').text(data.output[1]);
            $('#channel').text(data.output[2]);
            $('#comment-count').text(`${data.output[3]} comments`);
            $('#error-container').addClass('opacity-0');
            $('#error').text(null);
        } else {
            $('#thumbnail').attr('src', null);
            $('#title').text(null);
            $('#channel').text(null);
            $('#comment-count').text(null);
            $('#error-container').removeClass('opacity-0');
            $('#error').text(data.error);
        }
    });
    e.preventDefault();
});