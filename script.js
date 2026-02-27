function startCountdown(){

let eventName = document.getElementById("eventName").value;
let date = document.getElementById("eventDate").value;
let email = document.getElementById("email").value;

let eventDate = new Date(date).getTime();

let timer = setInterval(function(){

let now = new Date().getTime();
let distance = eventDate - now;

let days = Math.floor(distance/(1000*60*60*24));
let hours = Math.floor((distance%(1000*60*60*24))/(1000*60*60));
let minutes = Math.floor((distance%(1000*60*60))/(1000*60));
let seconds = Math.floor((distance%(1000*60))/1000);

document.getElementById("countdown").innerHTML =
days+"d "+hours+"h "+minutes+"m "+seconds+"s ";

if(distance < 0){

clearInterval(timer);

document.getElementById("countdown").innerHTML="Event Started!";

sendEmail(eventName,email);

}

},1000)

}

function sendEmail(eventName,email){

let params = {
event_name:eventName,
to_email:email
}

emailjs.send("YOUR_SERVICE_ID","YOUR_TEMPLATE_ID",params)

.then(function(){
alert("Email Notification Sent!");
});

}