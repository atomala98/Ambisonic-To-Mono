var serverAdress = "http://127.0.0.1:8000/";
var filename = "";
var output_filenames = [];

async function handleFiles(event) {
    let data = new FormData();
    var file = event.target.files[0];
    filename = file.name;
    data.append('file', file);
    const options = {
        method: 'POST',
        body: data,
    };
    
    console.log(document.getElementById("message").innerHTML);

    await fetch(serverAdress + "savefile", options)
        .then(response => response.json())
        .then(response => document.getElementById("message").innerHTML = response.message);
    
    
}

function channels(event) {
    let isMono = document.getElementById("mono").checked;
    if (!isMono) {
        document.getElementById("mono-div").setAttribute('style', 'display: none');
        document.getElementById("stereo-div").setAttribute('style', 'display: block');
        document.getElementById("mono-div-2").setAttribute('style', 'display: none');
        document.getElementById("stereo-div-2").setAttribute('style', 'display: block');
    }
    else {
        document.getElementById("mono-div").setAttribute('style', 'display: block');
        document.getElementById("stereo-div").setAttribute('style', 'display: none');
        document.getElementById("mono-div-2").setAttribute('style', 'display: block');
        document.getElementById("stereo-div-2").setAttribute('style', 'display: none');
    }
}

async function convertMono(event) {
    if (filename === "") {
        document.getElementById("message").innerHTML = "Upload file!";
        return;
    }

    document.getElementById("message").innerHTML = "Converting...";

    var elems = document.getElementsByName("bformat");
    var format = "";
    elems.forEach(x => {
        if (x.checked) format = x.value;
    });

    var theta = document.getElementById("theta").value;
    var polarity = document.getElementById("polarity").value

    const options = {
        headers: {
            "Content-Type": "application/json; charset=utf-8"
        },
        method: 'POST',
        body: JSON.stringify({
            "filename": filename,
            "theta": theta,
            "p": polarity,
            "format": format
        })
    };

    await fetch(serverAdress + "convertmono", options)
        .then(response => response.json())
        .then(response => {
            console.log(response);
            output_filenames = response.filenames;
            document.getElementById("message").innerHTML = response.message;
        });

}

async function convertStereo(event) {
    if (filename === "") {
        document.getElementById("message").innerHTML = "Upload file!";
        return;
    }

    document.getElementById("message").innerHTML = "Converting...";

    var elems = document.getElementsByName("bformat");
    var format = "";
    elems.forEach(x => {
        if (x.checked) format = x.value;
    });

    var elems = document.getElementsByName("method");
    var method = "";
    elems.forEach(x => {
        if (x.checked) method = x.value;
    });
    const options = {
        headers: {
            "Content-Type": "application/json; charset=utf-8"
        },
        method: 'POST',
        body: JSON.stringify({
            "filename": filename,
            "method": method,
            "format": format
        })
    };

    await fetch(serverAdress + "convertstereo", options)
        .then(response => response.json())
        .then(response => {
            console.log(response);
            output_filenames = response.filenames;
            document.getElementById("message").innerHTML = response.message;
        });
}

document.getElementById("upload").addEventListener("change", handleFiles, false);
document.getElementById("mono").addEventListener("change", channels, false);
document.getElementById("stereo").addEventListener("change", channels, false);
document.getElementById("convert-mono").addEventListener("click", convertMono, false);
document.getElementById("convert-stereo").addEventListener("click", convertStereo, false);

document.getElementById("theta").addEventListener("change", function() {
    var theta = document.getElementById("theta").value;
    document.getElementById("theta-label").innerHTML = "Theta: " + theta + " degrees";
}, false);

document.getElementById("polarity").addEventListener("change", function() {
    var p = document.getElementById("polarity").value;
    document.getElementById("polarity-label").innerHTML = "Polarity: " + (parseInt (p) / 100).toFixed(2);
}, false);

document.getElementById("download-mono").addEventListener("click", function() {
    if (output_filenames[0] == undefined) return;

    var element = document.getElementById("download-link");
    var link = "outputfiles/" + output_filenames[0];
    console.log(link)
    element.setAttribute('href', link);
    element.click();
}, false);

document.getElementById("download-stereo").addEventListener("click", function() {
    if (output_filenames[0] == undefined) return;

    var element = document.getElementById("download-link");
    var link = "outputfiles/" + output_filenames[0];
    element.setAttribute('href', link);
    element.click();
    link = "outputfiles/" + output_filenames[1];
    element.setAttribute('href', link);
    element.click();
}, false);    
