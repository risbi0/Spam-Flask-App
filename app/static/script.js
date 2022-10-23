let csrftoken = $('meta[name=csrf-token]').attr('content')
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
});

$(document).ready(function() {
    $('#form').on('submit', function(e) {
        $.ajax({
            type: 'POST',
            url: '/',
            data: {
                yt_id: $('#yt_id').val()
            }
        })
        .done(function(data) {
            if (data.output !== null) {
                $('#thumbnail').attr('src', data.output[0]);
                $('#title').text(data.output[1]).show();
                $('#channel').text(data.output[2]).show();
                $('#comment-count').text(`${data.output[3]} comments`).show();
                $('#error-container').addClass('opacity-0');
                $('#error').text(null).show();
            } else {
                $('#thumbnail').attr('src', null);
                $('#title').text(null).show();
                $('#channel').text(null).show();
                $('#comment-count').text(null).show();
                $('#error-container').removeClass('opacity-0');
                $('#error').text(data.error).show();
            }
        });
        e.preventDefault();
    });
});