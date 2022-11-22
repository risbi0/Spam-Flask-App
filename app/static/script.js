const csrftoken = $('meta[name=csrf-token]').attr('content');
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

const errorContainer = '#error-container';
const error = '#error';
const result = '#result';
const loading1 = '#loading-1';
const details = '#details';
const title = '#title';
const channel = '#channel';
const commentCount = '#comment-count';
const thumbnail = '#thumbnail';
const progressContainer = '#progress-container';
const tableContainer = '#table-container';
$('form').on('submit', e => {
    $(details).hide();
    $(thumbnail).attr('src', null);
    $(`${error}, ${result}`).text(null);
    $(`${errorContainer}, ${progressContainer}`).addClass('opacity-0');
    $(loading1).addClass('load-anim');
    $(tableContainer).empty();
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
                $(loading1).removeClass('load-anim');
                $(thumbnail).attr('src', data.output[0]);
                $(title).text(data.output[1]);
                $(channel).text(data.output[2]);
                $(commentCount).text(`${data.output[3]} comments`);
                $(details).show();
            });
        } else {
            $(loading1).removeClass('load-anim');
            $(`${title}, ${channel}, ${commentCount}`).text(null);
            $(errorContainer).removeClass('opacity-0');
            $(error).text(data.error);
        }
    });
    e.preventDefault();
});

const loading2 = '#loading-2';
const progress = '#progress';
const totalNum = '#total-num';
const desc = '#desc';
let output;
$('#process').on('click', e => {
    $(progressContainer).removeClass('opacity-0');
    $(loading2).addClass('load-anim');
    $(progress).text('0');
    $(totalNum).text($(commentCount).text().replace(/[^0-9]/g, ''));
    $(tableContainer).empty();
    (function loop() {
        const source = new EventSource('/process');
        source.onmessage = (e) => {
            const parsed_data = JSON.parse(e.data.replace(/'/g,'"'));
            $(progress).text(parsed_data['progress']);
            $(desc).text(parsed_data['desc']);
            if (parsed_data['repeat'] == 'True') {
                console.log('Request is taking over 20 seconds to execute. Restarting request...');
                source.close();
                loop();
            } else if (parsed_data['done'] == 'True') {
                $(loading2).removeClass('load-anim');
                if (Object.keys(parsed_data['output']['comment']).length != 0) {
                    $(progressContainer).addClass('opacity-0');
                    createTable(parsed_data['output']);
                } else {
                    $(desc).text('No spam detected.');
                }
                console.log('Done.');
                source.close();
            } else if (parsed_data['display_total_num'] == '') {
                $(totalNum).text(parsed_data['total_num']);
            }
        }
    }());
    e.preventDefault();
});

const tableHeaders = ['ID', 'Comment', 'Score'];
const createTable = (output) => {
    const table = document.createElement('table');
    const tableHead = table.createTHead();
    const tableHeadRow = tableHead.insertRow();
    for (let i = 0; i < 3; i++) {
        const tableHeader = document.createElement('th');
        tableHeader.textContent = tableHeaders[i];
        tableHeadRow.appendChild(tableHeader);
    }
    tableHead.appendChild(tableHeadRow);
    const tableBody = table.createTBody();
    for (let i = 0; i < Object.keys(output['id']).length; i++) {
        const tableBodyRow = tableBody.insertRow();
        for (let j = 0; j < 3; j++) {
            const tableBodyCell = tableBodyRow.insertCell();
            tableBodyCell.textContent = Object.values(output)[j][i];
        }
        tableBody.appendChild(tableBodyRow);
    }
    table.appendChild(tableHead);
    table.appendChild(tableBody);
    $(tableContainer).append(table);
}