let currentNewsIndex = 0;
let currentCategory = '';
let currentAudio = null;

window.onload = function() {        
    navigator.geolocation.getCurrentPosition(function(position) {
        getWeather(position.coords.latitude, position.coords.longitude, function() {
            if (userLoggedIn && userCategory) {
                currentCategory = userCategory;
            } else {
                currentCategory = 'NATION';  // ログインしていない場合のデフォルトカテゴリ
            }
            fetchNewsItem(currentCategory, 0);
        });
    }, function(error) {
        console.warn('位置情報の取得エラー: ' + error.message);
        // 位置情報が取得できなかった場合のデフォルトの処理
        currentCategory = 'NATION';
        fetchNewsItem(currentCategory, 0);
    });

    //ボタンやリンク以外の場所をクリックした時のイベントリスナー
    document.addEventListener('click', function(event) {
        if(event.target.tagName != 'BUTTON' && event.target.tagName !== 'A' && event.target.tagName !== 'SELECT' && currentNewsIndex != null) {
            console.log('ボタンやリンク以外の場所がクリックされました')
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/mark_latest_news_as_clicked", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                if (xhr.status == 200) {
                    var response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        // 成功音を再生
                        var audio = new Audio('static/audio/success.mp3');
                        audio.play();
                    }
                }
            };
            xhr.send();
        }
    });
};
        
document.addEventListener('DOMContentLoaded', function() {
    var getWeatherButton = document.getElementById('get-weather');
    if (getWeatherButton) {
        getWeatherButton.addEventListener('click', function() {
            stopCurrentAudio();
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    fetchWeather(position.coords.latitude, position.coords.longitude);
                }, function(error) {
                    console.error('Error Code = ' + error.code + ' - ' + error.message);
                });
            } else {
                console.log('Geolocation is not supported by this browser.');
            }
        });
    } else {
        console.log('The element with id "get-weather" does not exist.');
    }
});


function getWeather(lat, lon, callback) {
    // 天気情報の取得中メッセージを表示
    document.getElementById('weather-container').innerHTML = '天気情報を取得中...';

    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_weather?lat=" + lat + "&lon=" + lon, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                var response = JSON.parse(xhr.responseText);
                console.log(response); // 応答データの構造を確認
                
                // 天気と気温の情報を表示
                var weatherDescription = response.weather_description || "情報なし";
                var temperature = response.temperature ? `${response.temperature}度` : "情報なし";
                document.getElementById('weather-container').innerHTML = `天気: ${weatherDescription}, 気温: ${temperature}`;

                // 音声ファイルがあれば再生
                var audioFile = response.audio_file;
                if (audioFile) {
                    currentAudio = new Audio("/audio/" + audioFile);
                    currentAudio.play();
                    currentAudio.onended = function() {
                        if (callback && typeof callback === "function") {
                            callback();
                        }
                    };
                } else {
                    if (callback && typeof callback === "function") {
                        callback();
                    }
                }
            } else {
                // 天気情報の取得に失敗した場合のメッセージを表示
                document.getElementById('weather-container').innerHTML = '天気情報の取得に失敗しました。';
            }
        }
    };
    xhr.send();
}


function getNews() {
    fetchNewsItem('NATION', 0);  // デフォルトカテゴリを設定
}
        
document.getElementById('category-select').addEventListener('change', function() {
    stopCurrentAudio();
    currentCategory = this.value;
    currentNewsIndex = 0;
    fetchNewsItem(currentCategory, currentNewsIndex);
    updateLastSelectedCategory(currentCategory);  //データベースを更新
});
    
function fetchNewsItem(category, index) {
    fetch('/get_news', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({category: category, index: index})
    })
    .then(response => response.json())
    .then(data => {
        if (data.audio_file) {
            const newsContainer = document.getElementById('news-container');
            const oldTitle = newsContainer.firstChild;

            // 既存のタイトルがある場合、フェードアウト
            if (oldTitle && oldTitle.classList) {
                oldTitle.classList.add('fade-out');
            }

            setTimeout(() => {
                // 新しいニュースのタイトルをセット
                newsContainer.innerHTML = `<h3>${data.title}</h3><a href="${data.link}" target="_blank">リンク</a>`;

                // 新しいタイトルにフェードインクラスを追加
                const newTitle = newsContainer.firstChild;
                newTitle.classList.add('fade-in');

                // 音声再生
                currentAudio = new Audio(`/audio/${data.audio_file}`);
                currentAudio.play();
                currentAudio.onended = function() {
                    currentNewsIndex++;
                    fetchNewsItem(category, currentNewsIndex);
                };
            }, 1000); // アニメーションの持続時間に合わせて適切なタイムアウトを設定
        } else {
            console.log('ニュース項目がありません');
        }
    })
    .catch(error => console.error('Error:', error));
}



document.getElementById('get-weather').addEventListener('click', function() {
    stopCurrentAudio();
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            fetchWeather(position.coords.latitude, position.coords.longitude);
        }, function(error) {
            console.error('Error Code = ' + error.code + ' - ' + error.message);
        });
    } else {
        console.log('Geolocation is not supported by this browser.');
    }
});

function fetchWeather(latitude, longitude) {
    fetch(`/get_weather?lat=${latitude}&lon=${longitude}`)
    .then(response => response.json())
    .then(data => {
        // 天気情報を表示
        document.getElementById('weather-container').innerHTML = data.weather_text;
        if (data.audio_file) {
            const audio = new Audio(`/audio/${data.audio_file}`);
            audio.play();
        }        
    })
    .catch(error => console.error('Error:', error));
}

const userGreeting = document.getElementById('user-greeting');

//ログインしている場合，ユーザー名を表示
fetch('/get_user_info')
    .then(response => response.json())
    .then(data => {
        if (data.username) {
            userGreeting.innerHTML = `こんにちは、${data.username}さん`;
        }
    })
    .catch(error => console.error('Error:', error));

//再生中の音声を停止する関数
function stopCurrentAudio() {
    if (currentAudio && !currentAudio.paused) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }
}

function updateLastSelectedCategory(category) {
    fetch('/update_category', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({category: category})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('カテゴリ更新成功');
        } else {
            console.error('カテゴリ更新失敗');
        }
    })
    .catch(error => console.error('Error:', error));
}