const video=document.getElementById("video");
const canvas=document.getElementById("canvas");
const start=document.getElementById("start-camera");
const capture=document.getElementById("capture");
const cameraImage=document.getElementById("camera-image");
const preview=document.getElementById("preview");
const upload=document.getElementById("image");
let stream=null;
function showPreview(src){preview.innerHTML="";const img=document.createElement("img");img.src=src;preview.appendChild(img);}
start?.addEventListener("click",async()=>{
 try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"},audio:false});video.srcObject=stream;video.style.display="block";document.getElementById("camera-placeholder").style.display="none";capture.disabled=false;start.textContent="Camera started";}
 catch(e){alert("Camera unavailable. Check browser permission or use Upload image.");}
});
capture?.addEventListener("click",()=>{
 if(!video.videoWidth){alert("Wait for the camera preview to load.");return;}
 canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext("2d").drawImage(video,0,0);
 const data=canvas.toDataURL("image/jpeg",.88);cameraImage.value=data;upload.value="";showPreview(data);
});
upload?.addEventListener("change",()=>{
 cameraImage.value="";
 if(upload.files&&upload.files[0])showPreview(URL.createObjectURL(upload.files[0]));
});
document.getElementById("clear-image")?.addEventListener("click",()=>{upload.value="";cameraImage.value="";preview.innerHTML="🌾<span>Image preview</span>";});
document.getElementById("inspection-form")?.addEventListener("submit",()=>{
 if(stream)stream.getTracks().forEach(t=>t.stop());
});
