function readRoadInput() {


    var startRoad = document.getElementById('startInput').value;
    var endRoad   = document.getElementById('endInput').value;
    var dangerLevel = document.getElementById('range').value;

    console.log(dangerLevel);
    console.log(endRoad);
    
    var request = 'http://127.0.0.1:5000/route?start='+startRoad+'&end='+endRoad +'&dangerLevel='+ dangerLevel;
    console.log(request);

    location.href = request;

    return false;
  }