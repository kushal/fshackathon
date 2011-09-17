var CLIENT_ID = 'EPMLCP1Y1MS1U1F3QRQAGZQSLNSGGLD5T5K3OTZUB1CMSKEB';
if (window.location.host == 'localhost:8000') {
  CLIENT_ID = 'QADWWPJPWQEJCBQT3BZ0KHZVDZED2VDHZWI23ZW45PA00OXF';
}
var venues = ['42944', '105847', '174205', '200239', '326376', '394641', '409767', '645081', '750627', '806693', '877439', '919677', '1929512', '2209457', '2323058', '4923749', '6321969', '7130503', '17107148', '19497903', '23176411', '23824377', '23930833', '1488562, 18483013', '4b07f908f964a520c70123e3', '4b4ca0ddf964a52017b826e3', '4bcf6411462cb713759ed607', '4bf6f7be13aed13a308ceaf7', '4c8a35721eafb1f780017835', '4d22de726e8c370414900fa0', '4de0117c45dd3eae8764d6ac', '436964'];
//var venues = ['4de0117c45dd3eae8764d6ac','4c8a35721eafb1f780017835','4b4ca0ddf964a52017b826e3','750627','7130503'];

/**
 * For each venue above, build a div for who's there.
 */
function buildVenueDivs() {
  for (var i = 0; i < venues.length; i++) {
    var div = $('<div class="venuetop" style="margin-top:20px; margin-left:10px; width:300px; padding:10px;"><div id="venue-' + venues[i] + '"></div><div id="herenow-' + venues[i] + '"></div><br clear="left"></div>');
    $('#venues').append(div);
    $('#venues').append($('<br/>'));
  }
}

function fetchVenueMetadata(venueId) {
  makeRequest('venues/' + venueId, function(response) {    
    var venue = response.response.venue;
    var photo = '';
    var photoGroupIndex = 0;
    while (photo == '' && photoGroupIndex < venue.photos.groups.length) {
      var group = venue.photos.groups[photoGroupIndex];
      if (group.count > 0) {
        photo = '<img height=62 src="' + group.items[0].sizes.items[2].url + '">'; 
      }
      photoGroupIndex++;
    }
    $('#venue-' + venueId).html('<div class="venuephoto">' + photo + '</div><div class="venuename">' + venue.name + '</div><div class="count">' + venue.hereNow.count + ' people here now</div>');
  });  
}

function fetchVenueHereNow(vid) {
  makeRequest('venues/' + vid + '/herenow', function(response) {
    var herenow = response.response.hereNow.items;
    var html = [];
    for (var i = 0; i < herenow.length; i++) {
      html.push('<div class="oneperson"><img width=30 src="' +
      herenow[i]['user']['photo'] + 
      '"></div>');
    }
    html.push('<br clear="left"/>');
    //html.push('<br/><br/><br/>');
    $('#herenow-' + vid).html(html.join(''));
  });  
}

function fetchSearch() {
  $.getJSON('http://search.twitter.com/search.json?q=4sqhackathon&result_type=recent&count=5&callback=?&rpp=6&page=1', {}, function(result) {
    var results = result.results;
    var html = [];
    for (var i = 0; i < results.length; i++) {
      html.push('<div class="tweet"><div class="text">', results[i].text, '</div><div class="author">@', results[i].from_user, '</div></div>')   
    }
    $('#tweets').html(html.join(''));
  })
}

function rotateVenueDivs() {
  var children = $('#venues').children();
  
  var lastDiv = children[children.length - 2];
  var lastDivBr = children[children.length - 1];
  $(lastDivBr).insertBefore(children[1]);
  $(lastDiv).insertBefore(lastDivBr);
}

function update() {
  for (var i = 0; i < venues.length; i++) {
    fetchVenueMetadata(venues[i]);
    fetchVenueHereNow(venues[i]);
  }
  fetchSearch();
}

function init() {
  buildVenueDivs();
  update();
  setInterval(update, 60000)
  setInterval(rotateVenueDivs, 10000)
}

var token = null;

function doAuthRedirect() {
  var redirect = window.location.href.replace(window.location.hash, '');
  var url = 'https://foursquare.com/oauth2/authenticate?response_type=token&client_id=' + CLIENT_ID +
      '&redirect_uri=' + encodeURIComponent(redirect);
  window.location.href = url;
}

function zeroPad(num) {
    if (num < 10) {
      return '0' + num;
    } else {
      return num;
    }
}

function makeRequest(query, callback) {
  var tokenParam = ((query.indexOf('?') > -1) ? '&' : '?') + 'oauth_token=' + token;
  var date = new Date();
  var versionParam = '&v=' + (date.getYear() + 1900) + zeroPad(date.getMonth() + 1) + zeroPad(date.getDate());
  var url = 'https://api.foursquare.com/v2/' + query + tokenParam + versionParam;
  $.getJSON(url + '&callback=?', {}, callback);
}

$(function() {
  if ($.bbq.getState('access_token')) {
    // If there is a token in the state, consume it
    token = $.bbq.getState('access_token');
    $.bbq.pushState({}, 2)
    init();
  } else if ($.bbq.getState('error')) {
    // TODO: Handle error
  } else {
    doAuthRedirect();
  }
});
